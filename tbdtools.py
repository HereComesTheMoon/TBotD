import aiosqlite
import discord
from discord.ext import commands
import timeywimey

from config import on_tbd


class TBDTools(commands.Cog):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, roles=False, replied_user=False
        )
        self.db = db

    @commands.Cog.listener()
    @on_tbd()
    async def on_message(self, msg: discord.Message):
        # TODO: Also strip all symbols when checking whether a word fits the TBD scheme
        if msg.author.bot:
            return 0
        words = msg.content.split()
        if len(words) >= 3:
            to, be, determined = words[0], words[1], words[2]
            if (
                to[0].lower() == "t"
                and be[0].lower() == "b"
                and determined[0].lower() == "d"
            ):
                now = timeywimey.right_now()
                await self.add_tbd_suggestion(
                    now, msg.author.id, msg.id, to, be, determined
                )

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.name != after.name:
            words = after.name.split()
            if len(words) >= 3:
                to, be, determined = words[0], words[1], words[2]
                if (
                    to[0].lower() == "t"
                    and be[0].lower() == "b"
                    and determined[0].lower() == "d"
                ):
                    await self.add_tbd_used_title(
                        timeywimey.right_now(), to, be, determined
                    )

    async def add_tbd_suggestion(
        self, date: int, user_id: int, post_id: int, to: str, be: str, determined: str
    ):
        # TABLE suggestions (date INT, userID INT, postID INT, t TEXT, b TEXT, d TEXT)
        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO suggestions 
            VALUES (?,?,?,?,?,?)
            """,
            [date, user_id, post_id, to, be, determined],
        )
        await self.db.commit()

    async def add_tbd_used_title(self, date: int, to: str, be: str, determined: str):
        # TABLE used_title (date INT, t TEXT, b TEXT, d TEXT)
        cur = await self.db.cursor()
        await cur.execute(
            """
            INSERT INTO used_titles 
            VALUES (?,?,?,?)
            """,
            [date, to, be, determined],
        )
        await self.db.commit()
