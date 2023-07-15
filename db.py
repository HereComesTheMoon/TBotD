import asyncio
import aiosqlite
import discord
from discord.ext import tasks, commands
import timeywimey
import datetime
import botlog as bl

from tabulate import tabulate
import config as pm
from config import on_tbd


class Database(commands.Cog):
    def __init__(self, bot: commands.Bot, db: aiosqlite.Connection):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, roles=False, replied_user=False
        )
        self.db = db

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction_event: discord.RawReactionActionEvent):
        if (
            reaction_event.guild_id is None
            or reaction_event.member.bot
            or reaction_event.guild_id != pm.SERVER_ID
        ):
            return 0
        if reaction_event.emoji.is_custom_emoji():
            await self.custom_emoji_reacted(reaction_event.emoji)
        else:
            await self.emoji_reacted(reaction_event.emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self, reaction_event: discord.RawReactionActionEvent
    ):
        member = await self.bot.fetch_user(reaction_event.user_id)
        if (
            reaction_event.guild_id is None
            or member.bot
            or reaction_event.guild_id != pm.SERVER_ID
        ):
            return 0
        if reaction_event.emoji.is_custom_emoji():
            await self.custom_emoji_react_removed(reaction_event.emoji)
        else:
            await self.emoji_react_removed(reaction_event.emoji)

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

    async def emoji_reacted(self, emoji: discord.PartialEmoji):
        # TABLE emojis_default (name TEXT, uses INT)
        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT * 
            FROM emojis_default 
            WHERE name = (?)
            """,
            [emoji.name],
        )
        rows = list(await cur.fetchall())
        if not rows:
            await cur.execute(
                """
                INSERT INTO emojis_default 
                VALUES (?,?)
                """,
                [emoji.name, 1],
            )
        else:
            await cur.execute(
                """
                UPDATE emojis_default 
                SET uses = uses + 1 
                WHERE name = (?)
                """,
                [emoji.name],
            )
        await self.db.commit()

    async def emoji_react_removed(self, emoji: discord.PartialEmoji):
        # TABLE emojis_default (name TEXT, uses INT)
        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT * 
            FROM emojis_default 
            WHERE name = (?)
            """,
            [emoji.name],
        )
        rows = list(await cur.fetchall())
        if not rows:
            pass
        else:
            await cur.execute(
                """
                UPDATE emojis_default 
                SET uses = uses - 1 
                WHERE name = (?)
                """,
                [emoji.name],
            )
        await self.db.commit()

    async def custom_emoji_reacted(self, emoji: discord.PartialEmoji):
        # TABLE emojis_reacts (emoji_id INTEGER, name TEXT, url TEXT, uses INT)
        cur = await self.db.cursor()
        emoji_id = emoji.id
        await cur.execute(
            """
            SELECT * 
            FROM emojis_custom 
            WHERE emoji_id = (?)
            """,
            [emoji_id],
        )
        rows = list(await cur.fetchall())
        if not rows:
            await cur.execute(
                """
                INSERT INTO emojis_custom 
                VALUES (?,?,?,?)
                """,
                [emoji_id, emoji.name, str(emoji.url), 1],
            )
        else:
            await cur.execute(
                """
                UPDATE emojis_custom 
                SET uses = uses + 1 
                WHERE emoji_id = (?)
                """,
                [emoji_id],
            )
        await self.db.commit()

    async def custom_emoji_react_removed(self, emoji: discord.PartialEmoji):
        # TABLE emojis_reacts (emoji_id INTEGER, name TEXT, url TEXT, uses INT)
        cur = await self.db.cursor()
        emoji_id = emoji.id
        await cur.execute(
            """
            SELECT * 
            FROM emojis_custom 
            WHERE emoji_id = (?)
            """,
            [emoji_id],
        )
        rows = list(await cur.fetchall())
        if not rows:
            pass
        else:
            await cur.execute(
                """
                UPDATE emojis_custom 
                SET uses = uses - 1 
                WHERE emoji_id = (?)
                """,
                [emoji_id],
            )
        await self.db.commit()
