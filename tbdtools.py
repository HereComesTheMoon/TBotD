import aiosqlite
import asyncio
import discord
from discord.ext import commands
import timeywimey
import botlog as bl
from config import IDGI, TBD_GUILD, CW_CHANNEL, THREAD_WATCH_CHANNEL


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

    @commands.command()
    async def blindme(self, ctx: commands.Context, *, post: str = ""):
        """Blind yourself from a server for a set amount of time. eg. !blindme 2 hours"""
        bl.log(self.blindme, ctx)
        if ctx.guild is None:
            guild = self.bot.get_guild(TBD_GUILD)
            if guild.get_member(ctx.author.id) is None:
                await ctx.message.add_reaction(IDGI)
                return
        else:
            guild = ctx.guild

        _, due, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

        cog = self.bot.get_cog("Part")
        if cog is None:
            bl.error_log("The !part cog is not loaded, but the TBDTools cog is.")
            await ctx.reply("Error: The !part cog is not loaded.")
            return

        member = ctx.author

        async def task(channel: discord.TextChannel):
            try:
                await channel.set_permissions(member, read_messages=False)
            except discord.Forbidden:
                return
            except discord.HTTPException as e:
                bl.error_log.error(repr(e))
                return

            cur = await self.db.cursor()
            await cur.execute(
                """
                INSERT INTO part(UserID, GuildID, ChannelID, Due, Error)
                VALUES (?, ?, ?, ?, ?);
                """,
                (ctx.author.id, guild.id, channel.id, due, None),
            )
            await cur.close()

        async with asyncio.TaskGroup() as tg:
            for channel in guild.text_channels:
                if "bot" in channel.name:
                    continue
                tg.create_task(task(channel))

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

            content = f"New thread: {thread.mention} (#{thread.name})"
            if thread.owner:
                content += f" created by {thread.owner.mention} ({thread.owner})"
            if thread.parent:
                content += f" in <#{thread.parent_id}> (#{thread.parent.name})"

            content += f". Link: {thread.jump_url}"

            try:
                await tw_channel.send(content=content, allowed_mentions=self.ping_priv)
            except discord.HTTPException:
                bl.error_log.exception("Can't post in thread-watch channel.")
