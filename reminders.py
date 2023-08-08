import discord
from tabulate import tabulate
from discord.ext import tasks, commands
import asyncio
import aiosqlite
import botlog as bl
import timeywimey
from timeywimey import epoch2iso

from config import IDGI


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.reminder_loop.start()
        self.ping_priv = discord.AllowedMentions(
            everyone=False, roles=False, replied_user=False
        )
        self.db = db

    @tasks.loop(seconds=1)
    async def reminder_loop(self):
        await self.queue_reminders()

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    async def cog_unload(self):
        self.reminder_loop.stop()

    async def queue_reminders(self):
        p = await self.read_data(
            """
            WHERE queryDue <= (?) 
            AND status LIKE 'Future'
            """,
            [timeywimey.right_now() + 1],
        )
        task_stack = [asyncio.create_task(self.notify(x)) for x in p]
        if task_stack:
            await asyncio.wait(task_stack)

    async def notify(self, p: aiosqlite.Row):
        user = self.bot.get_user(p["userID"])
        try:
            await user.send(
                content=f"{p['reminder']}.\n\nYou set a reminder on the <t:{p['queryMade']}>. "
                f"Link to original query: {p['postUrl']}",
                allowed_mentions=self.ping_priv,
            )
            bl.notification_triggered(tuple(p))
        except discord.DiscordException as e:
            bl.error_log.exception(e)
            await self.db.execute(
                """
                UPDATE memories 
                SET status = 'Error' 
                WHERE oid = (?)
                """,
                [p["rowid"]],
            )
        else:
            await self.db.execute(
                """
                UPDATE memories 
                SET status = 'Past' 
                WHERE oid = (?)
                """,
                [p["rowid"]],
            )
        await self.db.commit()

    @commands.command()
    async def remindme(self, ctx: commands.Context, *, arg: str = ""):
        """eg. !remindme 5 hours, take out the trash"""
        bl.log(self.remindme, ctx)
        if "," in arg:
            when, what = arg.split(sep=",", maxsplit=1)
            when, what = when.strip(), what.strip()
        else:
            when = arg.strip()
            what = when
        now, then, parse_status = timeywimey.parse_time(when)
        if not parse_status:
            await ctx.message.add_reaction(IDGI)
            return
        p = {
            "userID": ctx.author.id,
            "postID": ctx.message.id,
            "postUrl": ctx.message.jump_url,
            "reminder": what,
            "queryMade": now,
            "queryDue": then,
            "status": "Future",
        }
        content = f"You'll be reminded on the <t:{p['queryDue']}> of {p['reminder']}. Use ``!reminders`` to check your reminders."
        if 30 < len(arg) and "," not in arg:
            content += " Please remember to use a `,` to separate *what* you want to be reminded from *when* you want to be reminded of it. Good: `!remindme 3 days, mom's birthday 2 days`. Bad: `!remindme 3 days mom's birthday 2 days`."
        await ctx.message.reply(content, allowed_mentions=self.ping_priv)
        p["oid"] = await self.add_data(p)
        await self.queue_reminders()

    @commands.command()
    async def reminders(self, ctx):
        """Show your active reminders."""
        bl.log(self.reminders, ctx)
        userID = ctx.author.id
        tab = await self.read_data(
            """
            WHERE userID LIKE (?) 
            AND status NOT LIKE 'Past' 
            ORDER BY queryDue ASC 
            LIMIT 10
            """,
            [userID],
        )
        results = [
            (
                k + 1,
                epoch2iso(p["queryDue"]),
                p["status"],
                p["reminder"].replace("\n", " ")[:85],
            )  # [:85] Trim reminder text if too long.
            for (k, p) in enumerate(tab)
        ]
        content = tabulate(results, headers=["No.", "Due", "Status", "Reminder"])
        if not results:
            await ctx.message.reply(content="You currently have no active reminders.")
        else:
            await ctx.message.reply(
                content=f"'Due' is given in timezone of the bot. "
                f"When it's midnight for the bot then it's <t:1642028420:t> for you. "
                f"Right now it's <t:{timeywimey.right_now()}> in your time zone, "
                f"and {timeywimey.epoch2iso(timeywimey.right_now())} "
                f"in bot time.\n```" + content + "```",
                allowed_mentions=self.ping_priv,
            )

    async def read_data(self, query: str, params: list):
        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT oid, * 
            FROM memories """
            + query,
            params,
        )
        return await cur.fetchall()

    async def add_data(self, p: dict):
        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO memories 
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            [
                p["userID"],
                p["postID"],
                p["postUrl"],
                p["reminder"],
                p["queryMade"],
                p["queryDue"],
                p["status"],
            ],
        )
        await self.db.commit()
        return cur.lastrowid
