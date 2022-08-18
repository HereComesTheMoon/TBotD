import discord
from discord.ext import commands
import botlog as bl
from config import THREAD_WATCH_CHANNEL, SERVER_ID


class ThreadWatch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        # Ensures the bot auto-joins every new thread.
        try:
            await thread.fetch_member(self.bot.user.id)
        except discord.NotFound:
            await thread.join()
            if thread.guild.id != SERVER_ID:
                return

            tw_channel = await self.bot.fetch_channel(THREAD_WATCH_CHANNEL)
            if tw_channel is None:
                bl.error_log.exception("Can't find thread-watch channel.")
                return

            content = f"New thread: {thread.mention} (#{thread.name})"
            if thread.owner:
                content += f" created by {thread.owner.mention} ({thread.owner})"
            if thread.parent:
                content += f" in <#{thread.parent_id}> (#{thread.parent.name})"

            content += f". Link: {thread.jump_url}"

            try:
                await tw_channel.send(content=content, allowed_mentions=self.ping_priv)
            except discord.HTTPException:
                bl.error_log.exception("Can't post in thread-watch channel.")
