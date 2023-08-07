import aiosqlite
import discord
from discord.ext import commands
import re
import timeywimey


class Counter(commands.Cog):
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event: discord.RawReactionActionEvent):
        member = await self.bot.fetch_user(event.user_id)
        if member.bot:
            return

        # Use 0 for DMs
        # This breaks if there exists a real Discord guild with ID 0
        guild_id = event.guild_id if event.guild_id is not None else 0
        emoji = event.emoji
        async with await self.db.cursor() as cur:
            if event.emoji.is_custom_emoji():
                await cur.execute(
                    """
                    INSERT INTO emojis_custom (GuildID, EmojiID, Name, URL, Uses)
                    VALUES (?, ?, ?, ?, 1)
                    ON CONFLICT(GuildID, EmojiID) DO
                    UPDATE SET Uses = Uses + 1;
                    """,
                    [guild_id, emoji.id, emoji.name, str(emoji.url)],
                )
            else:
                await cur.execute(
                    """
                    INSERT INTO emojis_default (GuildID, Name, Uses)
                    VALUES (?, ?, 1)
                    ON CONFLICT(GuildID, Name) DO
                    UPDATE SET Uses = Uses + 1;
                    """,
                    [guild_id, emoji.name],
                )
        await self.db.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, event: discord.RawReactionActionEvent):
        member = await self.bot.fetch_user(event.user_id)
        if member.bot:
            return

        # Use 0 for DMs
        # This breaks if there exists a real Discord guild with ID 0
        guild_id = event.guild_id if event.guild_id is not None else 0
        emoji = event.emoji
        async with await self.db.cursor() as cur:
            if event.emoji.is_custom_emoji():
                await cur.execute(
                    """
                    UPDATE emojis_custom
                    SET Uses = Uses - 1
                    WHERE GuildID = (?)
                    AND EmojiID = (?);
                    """,
                    [guild_id, emoji.id],
                )
            else:
                await cur.execute(
                    """
                    UPDATE emojis_default
                    SET Uses = Uses - 1
                    WHERE GuildID = (?)
                    AND Name = (?);
                    """,
                    [guild_id, emoji.name],
                )
        await self.db.commit()
