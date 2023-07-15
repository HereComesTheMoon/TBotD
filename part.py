import discord
from discord.ext import tasks, commands
import asyncio
import aiosqlite
import botlog as bl
import timeywimey

from config import IDGI


class Part(commands.Cog, name="Part"):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.db = db
        self.loop.start()

    @commands.command(aliases=["snooze"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def part(self, ctx: commands.Context, *, post: str = ""):
        """!part 2 hours/days/etc. Leaves channel for specified time."""
        bl.log(self.part, ctx)
        member = ctx.author
        _, due, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

        userID = member.id
        guildID = ctx.guild.id
        channelID = ctx.channel.id

        await ctx.channel.set_permissions(member, read_messages=False)

        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO part
            VALUES (?, ?, ?, ?, ?);
            """,
            (userID, guildID, channelID, due, "Future"),
        )
        await self.db.commit()
        await self.queue_unparts()

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def rejoin(self, ctx: commands.Context, *, post: str = ""):
        """Rejoins all !part-ed channels."""
        bl.log(self.rejoin, ctx)
        guild: discord.Guild = ctx.guild
        member: discord.Member = guild.get_member(ctx.author.id)

        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT channelID FROM part
            WHERE userID = (?)
            AND guildID = (?)
            AND status in ('Present', 'Future');
            """,
            (ctx.author.id, guild.id),
        )
        channels = await cur.fetchall()
        for row in channels:
            channel: discord.Channel = guild.get_channel(row["channelID"])
            await channel.set_permissions(member, overwrite=None)

        cur = await self.db.cursor()
        await cur.execute(
            """
            UPDATE part
            SET status = 'Past'
            WHERE userID = (?)
            AND guildID = (?);
            """,
            (ctx.author.id, guild.id),
        )
        await self.db.commit()

    async def unpart(self, row: aiosqlite.Row):
        guild: discord.Guild = self.bot.get_guild(row["guildID"])
        channel: discord.Channel = guild.get_channel(row["channelID"])
        member: discord.Member = guild.get_member(row["userID"])
        delay = row["due"] - timeywimey.right_now()
        cur = await self.db.cursor()
        await cur.execute(
            """
            UPDATE part
            SET status = 'Present'
            WHERE oid = (?)
            """,
            [row["rowid"]],
        )
        await self.db.commit()

        await asyncio.sleep(max(delay, 1))

        cur = await self.db.cursor()
        try:
            await channel.set_permissions(member, overwrite=None)
        except discord.HTTPException:
            bl.error_log.exception("Bot unparting permission change error!")
            await cur.execute(
                """
                UPDATE part
                SET status = 'Error'
                WHERE oid = (?)
                """,
                [row["rowid"]],
            )
            await self.db.commit()
            return

        await cur.execute(
            """
            UPDATE part
            SET status = 'Past'
            WHERE oid = (?)
            """,
            [row["rowid"]],
        )
        await self.db.commit()

    @tasks.loop(minutes=5)
    async def loop(self):
        await self.queue_unparts()

    @loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
        part = await self.get_rejoins()
        task_stack = [asyncio.create_task(self.unpart(x)) for x in part]
        if task_stack:
            await asyncio.wait(task_stack)

    async def queue_unparts(self):
        part = await self.get_rejoins()
        task_stack = [asyncio.create_task(self.unpart(x)) for x in part]
        if task_stack:
            await asyncio.wait(task_stack)

    async def get_rejoins(self):
        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT oid, *
            FROM part
            WHERE due <= (?)
            AND status LIKE 'Future'
            """,
            [timeywimey.right_now() + 360 + 1],
        )
        return await cur.fetchall()
