import aiosqlite
import discord
from discord.ext import commands
import timeywimey
import re
import botlog as bl

from config import IDGI


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
    @commands.guild_only()
    async def blindme(self, ctx: commands.Context, *, post: str = ""):
        """Blind yourself for a set amount of time. eg. !blindme 2 hours"""
        bl.log(self.blindme, ctx)
        member = ctx.author
        _, due, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

    @commands.command()
    async def cwbanme(self, ctx: commands.Context, *, post: str = ""):
        """CW-Ban yourself for a set amount of time. eg. !cwbanme 2 hours"""
        _, due, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

        cog = self.bot.get_cog("Part")
        if cog is None:
            bl.error_log("The !part cog is not loaded, but the TBDTools is.")
            await ctx.reply("Error: The !part cog is not loaded.")
            return

        # This is a special case for a specific server. It's a bit brittle
        # It avoids having to hardcode the channel ID into the config file
        channel = discord.utils.get(
            self.bot.get_all_channels(), name="culture-war", category__name="TOP TEXT"
        )

        if channel is None:
            bl.error_log(
                "Can't find the culture-war channel! Was it or its category renamed recently?"
            )

        guild = channel.guild
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
    async def on_message(self, msg: discord.Message):
        # TODO: Also accept suggestions such as 'to-be$determined'
        if msg.author.bot:
            return
        pattern = r"\b[tT]\w*\s+[bB]\w*\s+[dD]\w*\b"

        cur = await self.db.cursor()
        await cur.executemany(
            """
            INSERT INTO suggestions(Suggestion)
            VALUES (?);
            """,
            ((match,) for match in re.findall(pattern, msg.content)),
        )
        await cur.close()
        await self.db.commit()

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.name == after.name:
            return
        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO used_titles(GuildID, Date, Title)
            VALUES (?,?,?);
            """,
            [after.id, timeywimey.right_now(), after.name],
        )
        await cur.close()
        await self.db.commit()
