import discord
from discord.ext import commands
import asyncio
import botlog as bl
from config import THREAD_WATCH_CHANNEL_ID, SERVER_ID
TWITTER_PREFIX = "https://twitter.com/"
FIXTWITTER_PREFIX = "https://vxtwitter.com/"


class FixTwitter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
        self.stored_posts: dict[int, discord.Message] = {} # (id of original message, bot response message), use to delete bot response if original is deleted

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        await asyncio.sleep(2) # To prevent the race-condition where Discord didn't load the embed yet
        if any(embed.url.startswith(TWITTER_PREFIX) and embed.video.url is not None for embed in msg.embeds):
            # This is a set to cull duplicates, otherwise the bot will post the link several times. Discord embeds are funny.
            new_content = " ".join({fix_twitter_url(embed.url) for embed in msg.embeds})
            new_post = await msg.reply(content=new_content, mention_author=False)
            self.stored_posts[msg.id] = new_post
            await msg.edit(suppress=True)
            await asyncio.sleep(7200) # Two hours time during which deletion of msg results in deletion of response
            self.stored_posts.pop(msg.id, None)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.id in self.stored_posts:
            bot_response = self.stored_posts[msg.id]
            await bot_response.delete()
            self.stored_posts.pop(msg.id, None)


def fix_twitter_url(embed_url: str) -> str:
    if embed_url.startswith(TWITTER_PREFIX):
        return FIXTWITTER_PREFIX + embed_url[len(TWITTER_PREFIX):]
    return embed_url
