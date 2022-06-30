import discord
from tabulate import tabulate
from discord.ext import tasks, commands
import asyncio
import aiosqlite
from parsedatetime import Calendar
import datetime
import botlog as bl
import timeywimey
from timeywimey import epoch2iso

from config import IDGI, OWNER_ID

"""
What needs to be stored in the reminders database?
int: running number, aka "reminder number X" 
int: postID
int: ID of person who made the request
TEXT: status, Was the reminder executed? Is it in active memory? 
TEXT: What they want to be reminded of
TEXT: When they made the request
TEXT: When it is due

??? STATUS for tasks:
Waiting ~ At some point far in the future
Active/Threaded ~ Has an async sleep task associated to it, and fires soon (eg less than an hour) 
Done ~ Completed. Someone was successfully reminded.
Error ~ Something went wrong, eg. it was not possible to remind them.


???
-STORE DATES IN EPOCH TIME: aka seconds after '1970-01-01T00:00:00'. Allows treating as ints, and ordering in sql

Additional feature ideas:
If the bot is restarted, ensure it doesn't drop any active reminder tasks. (EDIT: Probably done.)
"""


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_loop.start()
        self.ping_priv = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)

    @tasks.loop(hours=1)
    async def reminder_loop(self):
        await self.queue_reminders()

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()
        p = await self.read_data('''WHERE queryDue <= (?) 
                                    AND status IN ("Present", "Future")''',
                                 [int(datetime.datetime.now().timestamp()) + 3600 + 60])
        task_stack = [asyncio.create_task(self.notify(x)) for x in p]
        if task_stack:
            await asyncio.wait(task_stack)

    async def queue_reminders(self):
        p = await self.read_data('''WHERE queryDue <= (?) 
                                    AND status LIKE "Future"''',
                                 [int(datetime.datetime.now().timestamp()) + 3600 + 60])
        task_stack = [asyncio.create_task(self.notify(x)) for x in p]
        if task_stack:
            await asyncio.wait(task_stack)

    async def notify(self, p: aiosqlite.Row):
        cur = await self.bot.db.cursor()
        user = self.bot.get_user(p['userID'])
        delay = p['queryDue'] - int(datetime.datetime.now().timestamp())
        await cur.execute('''UPDATE memories 
                             SET status = "Present" 
                             WHERE oid = (?)''',
                          [p['rowid']])
        await self.bot.db.commit()

        await asyncio.sleep(max(delay, 1))

        try:
            await user.send(content=f"{p['reminder']}.\n\nYou set a reminder on the <t:{p['queryMade']}>. "
                                    f"Link to original query: {p['postUrl']}",
                            allowed_mentions=self.ping_priv)
            cur = await self.bot.db.cursor()
            await cur.execute('''UPDATE memories 
                                 SET status = "Past" 
                                 WHERE oid = (?)''',
                              [p['rowid']])
            await self.bot.db.commit()
            bl.notification_triggered(tuple(p))
        except discord.HTTPException:
            bl.error_log.exception("Reminder notification error! Not good!")
            owner = self.bot.get_user(OWNER_ID)
            await owner.send(content="Reminder notification error! Not good!")
            await owner.send(content=f"{p['reminder']}.\n\nYou set a reminder on the <t:{p['queryMade']}>."
                                     f"Link to original query: {p['postUrl']}",
                             allowed_mentions=self.ping_priv)
            cur = await self.bot.db.cursor()
            await cur.execute('''UPDATE memories 
                                 SET status = "Error" 
                                 WHERE oid = (?)''',
                              [p['rowid']])
            await self.bot.db.commit()

    @commands.command()
    async def remindme(self, ctx, *, arg: str = ""):
        """eg. !remindme 5 hours, take out the trash"""
        bl.log(self.remindme, ctx)
        if ',' in arg:  # Format argument, decide if 'what to be reminded of' was given.
            when, what = arg.split(sep=',', maxsplit=1)
            when, what = when.strip(), what.strip()  # _, reminder
        else:
            when = arg.strip()
            what = when
        cal = Calendar()
        time_struct, parse_status = cal.parse(when)
        t = datetime.datetime(*time_struct[:6])
        now = int(datetime.datetime.now().timestamp())  # queryMade
        try:
            then = int(t.timestamp())  # queryThen
        except OSError:
            then = now
        p = {
            # 0 ~ 'oid': INTEGER, primary key, increments automatically
            'userID': ctx.author.id,
            'postID': ctx.message.id,
            'postUrl': ctx.message.jump_url,
            'reminder': what,
            'queryMade': now,
            'queryDue': then,
            'status': "Future"
        }
        if p['queryDue'] <= p['queryMade'] + 5 or not parse_status:
            await ctx.message.add_reaction(IDGI)
            return
        await ctx.message.reply(content=f"You'll be reminded on the <t:{p['queryDue']}> of {p['reminder']}. "
                                        f"Use ``!reminders`` to check your reminders.",
                                allowed_mentions=self.ping_priv)
        p['oid'] = await self.add_data(p)  # Store new reminder in database, return primary key row_id
        await self.queue_reminders()

    @commands.command()
    async def reminders(self, ctx):
        """Show your active reminders."""
        bl.log(self.reminders, ctx)
        userID = ctx.author.id
        tab = await self.read_data('''WHERE userID LIKE (?) 
                                      AND status NOT LIKE "Past" 
                                      ORDER BY queryDue ASC 
                                      LIMIT 10''',
                                   [userID])
        results = [
                    (k + 1,
                    epoch2iso(p['queryDue']),
                    p['status'],
                    p['reminder'].replace("\n", " ")[:85]) # [:85] Trim reminder text if too long.
                    for (k, p) in enumerate(tab)
                  ]
        content = tabulate(results, headers=["No.", "Due", "Status", "Reminder"])
        if not results:
            await ctx.message.reply(content="You currently have no active reminders.")
        else:
            await ctx.message.reply(content=f"'Due' is given in timezone of the bot. "
                                            f"When it's midnight for the bot then it's <t:1642028420:t> for you. "
                                            f"Right now it's <t:{timeywimey.right_now()}> in your time zone, "
                                            f"and {timeywimey.epoch2iso(timeywimey.right_now())} "
                                            f"in bot time.\n```" + content + '```',
                                    allowed_mentions=self.ping_priv)

    async def read_data(self, query: str, params: iter):
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT oid, * 
                             FROM memories ''' + query, params)
        return await cur.fetchall()

    async def add_data(self, p: dict):
        cur = await self.bot.db.cursor()
        await cur.execute('''INSERT INTO memories 
                             VALUES (?, ?, ?, ?, ?, ?, ?);''',
                          [p['userID'], p['postID'], p['postUrl'], p['reminder'], p['queryMade'], p['queryDue'],
                           p['status']])
        await self.bot.db.commit()
        return cur.lastrowid
