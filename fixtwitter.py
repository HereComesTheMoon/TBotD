import discord
from discord.ext import commands
import asyncio
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

        if not msg.embeds: # Just in case
            await asyncio.sleep(2)

        content = ""
        for embed in msg.embeds:
            if embed.url is None or embed.video.url is None:
                continue
            if not embed.url.startswith(TWITTER_PREFIX):
                continue

            content += FIXTWITTER_PREFIX + embed.url[len(TWITTER_PREFIX):] + " "

        if content:
            new_post = await msg.reply(content, mention_author=False)
            self.stored_posts[msg.id] = new_post
            try:
                await msg.edit(suppress=True)
            except discord.errors.Forbidden:
                pass

            await asyncio.sleep(7200) # Two hours time during which deletion of msg results in deletion of response
            self.stored_posts.pop(msg.id, None)



    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.id in self.stored_posts:
            bot_response = self.stored_posts[msg.id]
            await bot_response.delete()
            self.stored_posts.pop(msg.id, None)

