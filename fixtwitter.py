import discord
from discord.ext import commands
import asyncio

TWITTER_PREFIX = "https://twitter.com/"
FIXTWITTER_PREFIX = "https://vxtwitter.com/"


class FixTwitter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, users=False, roles=False, replied_user=False
        )
        self.stored_posts: dict[
            int, discord.Message
        ] = (
            {}
        )  # (id of original message, bot response message), use to delete bot response if original is deleted

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if "twitter.com/" not in msg.clean_content:
            return

        stuff = msg.clean_content.split("/twitter.com/")
        content = "/vxtwitter.com/".join(stuff)

        if content == "":
            return

        try:
            new_post = await msg.reply(content, mention_author=False)
            self.stored_posts[msg.id] = new_post
        except discord.HTTPException:
            return  # If we cannot post a fixed link, return, since we do not want to suppress embeds on the post

        try:
            await msg.edit(suppress=True)
        except discord.errors.Forbidden:
            pass  # For example, forbidden from removing embeds in a post that happened in DMs

        await asyncio.sleep(
            7200
        )  # Two hours time during which deletion of msg results in deletion of response
        self.stored_posts.pop(msg.id, None)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.id in self.stored_posts:
            bot_response = self.stored_posts[msg.id]
            await bot_response.delete()
            self.stored_posts.pop(msg.id, None)
