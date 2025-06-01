import aiosqlite
import asyncio
import discord
from discord.ext import commands, tasks
import timeywimey
import botlog as bl
from config import IDGI, TBD_GUILD, CW_CHANNEL, THREAD_WATCH_CHANNEL, BLINDED_ROLE


def is_tbd_member():
    async def predicate(ctx: commands.Context):
        tbd = ctx.bot.get_guild(TBD_GUILD)
        return tbd.get_member(ctx.author.id) is not None

    return commands.check(predicate)


class TBDTools(commands.Cog):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, roles=False, replied_user=False
        )
        self.db = db
        assert self.bot.get_guild(TBD_GUILD) is not None
        if self.bot.get_cog("Part") is None:
            raise "Part is not loaded. !cwbanme won't work"
        self.roles_loop.start()

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        # Ensures the bot auto-joins every new thread.
        try:
            await thread.fetch_member(self.bot.user.id)
        except discord.NotFound:
            await thread.join()
            if thread.guild.id != TBD_GUILD:
                return

            tw_channel: discord.TextChannel = await self.bot.fetch_channel(
                THREAD_WATCH_CHANNEL
            )
            if tw_channel is None:
                bl.error_log.exception("Can't find thread-watch channel.")
                return

            content = f"{thread.mention} (#{thread.name})"
            if thread.owner:
                content += f" created by {thread.owner.mention}"
            if thread.parent:
                content += f" in <#{thread.parent_id}>."

            try:
                await tw_channel.send(content=content, allowed_mentions=self.ping_priv)
            except discord.HTTPException:
                bl.error_log.exception("Can't post in thread-watch channel.")

    @commands.command()
    @is_tbd_member()
    async def blindme(self, ctx: commands.Context, *, post: str = ""):
        """Blind yourself from a server for a set amount of time. eg. !blindme 2 hours"""
        bl.log(self.blindme, ctx)
        guild = self.bot.get_guild(TBD_GUILD)
        blinded_role = guild.get_role(BLINDED_ROLE)
        member = guild.get_member(ctx.author.id)

        _, due, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

        await member.add_roles(blinded_role, reason="!blindme command.")
        await self.db.execute(
            """
            INSERT INTO remove_role(UserID, GuildID, RoleID, Due, Error)
            VALUES (?, ?, ?, ?, ?);
            """,
            (ctx.author.id, guild.id, blinded_role.id, due, None),
        )
        await self.db.commit()

    @commands.command()
    @is_tbd_member()
    async def cwbanme(self, ctx: commands.Context, *, post: str = ""):
        """CW-Ban yourself for a set amount of time. eg. !cwbanme 2 hours"""
        _, due, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

        cog = self.bot.get_cog("Part")
        if cog is None:
            bl.error_log("The !part cog is not loaded, but the TBDTools cog is.")
            await ctx.reply("Error: The !part cog is not loaded.")
            return

        guild = self.bot.get_guild(TBD_GUILD)
        channel = guild.get_channel(CW_CHANNEL)

        member = guild.get_member(ctx.author.id)

        await channel.set_permissions(member, read_messages=False)

        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO part(UserID, GuildID, ChannelID, Due, Error)
            VALUES (?, ?, ?, ?, ?);
            """,
            (ctx.author.id, guild.id, channel.id, due, None),
        )
        await self.db.commit()

    @tasks.loop(seconds=1)
    async def roles_loop(self):
        now = timeywimey.right_now() + 1
        tasks = await self.db.execute(
            """
            SELECT rowid, UserID, GuildID, RoleID
            FROM remove_role
            WHERE Due <= (?)
            AND Error IS NULL;
            """,
            [now],
        )

        for row in await tasks.fetchall():
            try:
                guild: discord.Guild = self.bot.get_guild(row["GuildID"])
                role: discord.Role = guild.get_role(row["RoleID"])
                member: discord.Member = guild.get_member(row["UserID"])

                await member.remove_roles(role, reason="Bot removed.")
            except (AttributeError, discord.DiscordException) as e:
                bl.error_log.exception(e)
                await self.db.execute(
                    """
                    UPDATE remove_role
                    SET Error = (?)
                    WHERE rowid = (?);
                    """,
                    [repr(e), row["rowid"]],
                )
            else:
                await self.db.execute(
                    """
                    DELETE FROM remove_role
                    WHERE rowid = (?);
                    """,
                    [row["rowid"]],
                )
        await self.db.commit()

    @roles_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    async def cog_unload(self):
        self.roles_loop.stop()
