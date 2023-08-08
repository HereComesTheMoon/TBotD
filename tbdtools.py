import aiosqlite
import discord
from discord.ext import commands
import timeywimey
import botlog as bl

from config import IDGI, TBD_GUILD, CW_CHANNEL


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
        for channel in guild.channels:
            try:
                await channel.set_permissions(member, read_messages=False)
                cur = await self.db.cursor()
                await cur.execute(
                    """
                    INSERT INTO part(UserID, GuildID, ChannelID, Due, Error)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (ctx.author.id, guild.id, channel.id, due, None),
                )
                await cur.close()
            except discord.Forbidden:
                pass
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
