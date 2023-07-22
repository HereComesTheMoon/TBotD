import aiosqlite
import discord
from discord.ext import commands
import timeywimey
import re


class TBDTools(commands.Cog):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, roles=False, replied_user=False
        )
        self.db = db

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
