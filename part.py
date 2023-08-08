import discord
from discord.ext import tasks, commands
import aiosqlite
import botlog as bl
import timeywimey

from config import IDGI


class Part(commands.Cog, name="Part"):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.db = db
        self.part_loop.start()

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

        try:
            await ctx.channel.set_permissions(member, read_messages=False)
        except AttributeError:
            await ctx.reply(
                "You are probably trying to use this command in a thread. Threads inherit their permissions from their parent channel, so this doesn't work. You can try leaving the thread instead."
            )
            return

        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO part
            VALUES (?, ?, ?, ?, ?);
            """,
            (userID, guildID, channelID, due, None),
        )
        await self.db.commit()

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def rejoin(self, ctx: commands.Context, *, post: str = ""):
        """Rejoins all !part-ed channels."""
        bl.log(self.rejoin, ctx)

        tasks = await self.db.execute(
            """
            SELECT UserID, GuildID, ChannelID FROM part
            WHERE UserID = (?)
            AND GuildID = (?)
            AND Error IS NOT NULL;
            """,
            (ctx.author.id, ctx.guild.id),
        )
        for row in await tasks.fetchall():
            await self.unpart(row)

    async def unpart(self, row: aiosqlite.Row):
        try:
            guild: discord.Guild = self.bot.get_guild(row["GuildID"])
            channel: discord.Channel = guild.get_channel(row["ChannelID"])
            member: discord.Member = guild.get_member(row["UserID"])

            await channel.set_permissions(member, overwrite=None)
        except discord.DiscordException as e:
            bl.error_log.exception(e)
            await self.db.execute(
                """
                UPDATE part
                SET Error = (?)
                WHERE rowid = (?);
                """,
                [repr(e), row["rowid"]],
            )
        else:
            await self.db.execute(
                """
                DELETE FROM part
                WHERE rowid = (?);
                """,
                [row["rowid"]],
            )
        await self.db.commit()

    @tasks.loop(seconds=1)
    async def part_loop(self):
        now = timeywimey.right_now() + 1
        tasks = await self.db.execute(
            """
            SELECT rowid, *
            FROM part
            WHERE Due <= (?)
            AND Error IS NULL;
            """,
            [now],
        )

        for row in await tasks.fetchall():
            await self.unpart(row)

    @part_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    async def cog_unload(self):
        self.part_loop.stop()
