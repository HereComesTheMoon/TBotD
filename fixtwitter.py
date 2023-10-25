import discord
from discord.ext import commands
import asyncio

from config import DELETE


class FixTwitter(commands.Cog):
    replace: list[tuple[str, str]] = [
        ("https://twitter.com/", "https://vxtwitter.com/"),
        ("https://x.com/", "https://vxtwitter.com/"),
        ("https://bsky.app/", "https://psky.app/"),
    ]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, users=False, roles=False, replied_user=False
        )
        self.user_post_to_fixed: dict[
            int, discord.Message
        ] = (
            {}
        )  # (id of original message, bot response message), use to delete bot response if original is deleted
        self.fixed_to_user_post: dict[
            int, discord.Message
        ] = {}  # delete bot response if 'X' react happens

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        content = msg.clean_content

        for match, substitute in self.replace:
            content = content.replace(match, substitute)

        if content == msg.clean_content:
            return

        try:
            fixed = await msg.reply(content, mention_author=False)
            self.user_post_to_fixed[msg.id] = fixed
            self.fixed_to_user_post[fixed.id] = msg
            await fixed.add_reaction(DELETE)
        except discord.HTTPException:
            return  # If we cannot post a fixed link, return, since we do not want to suppress embeds on the post

        try:
            await msg.edit(suppress=True)
        except discord.errors.Forbidden:
            pass  # For example, forbidden from removing embeds in a post that happened in DMs

        await asyncio.sleep(
            300
        )  # Two hours time during which deletion of msg results in deletion of response
        self.user_post_to_fixed.pop(msg.id, None)
        await fixed.remove_reaction(DELETE, self.bot)
        self.fixed_to_user_post.pop(fixed.id, None)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        if msg.id in self.user_post_to_fixed:
            bot_response = self.user_post_to_fixed[msg.id]
            await bot_response.delete()
            self.user_post_to_fixed.pop(msg.id, None)

    @commands.Cog.listener()
    async def on_reaction_add(self, react: discord.Reaction, user: discord.User):
        if user.bot:
            return
        if react.emoji != DELETE:
            return
        if react.message.id not in self.fixed_to_user_post:
            return

        user_post = self.fixed_to_user_post[react.message.id]

        if user_post.author != user:
            return

        try:
            await user_post.edit(suppress=False)
        except discord.errors.Forbidden:
            pass  # eg. in DMs
        finally:
            self.fixed_to_user_post.pop(react.message.id, None)
            await react.message.delete()
