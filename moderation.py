import discord
from discord.ext import commands
from config import MOD_ROLE, LOGGER_CHANNEL, SERVER_ID, LOUDSPEAKER


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, react: discord.Reaction, user: discord.User):
        guild = react.message.channel.guild
        if guild is None or guild.id != SERVER_ID:
            return
        if str(react.emoji) == LOUDSPEAKER:
            channel = await self.bot.fetch_channel(LOGGER_CHANNEL)
            await react.remove(user)
            content = f"<@&{MOD_ROLE}> : The mods were called with the {LOUDSPEAKER} emoji by {user.mention} in {react.message.channel.mention}.\nLINK : <{react.message.jump_url}>\n"
            try:
                await channel.send(content=content+f"Post by {react.message.author.mention} : \n{react.message.content}")
            except discord.HTTPException:
                await channel.send(content=content)
