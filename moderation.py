import discord
from discord.ext import commands
from config import MOD_ROLE, SERVER_ID, LOUDSPEAKER


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot, logger_channel: discord.TextChannel):
        self.bot = bot
        self.logger_channel = logger_channel

    @commands.Cog.listener()
    async def on_reaction_add(self, react: discord.Reaction, user: discord.User):
        if str(react.emoji) != LOUDSPEAKER:
            return

        channel = react.message.channel
        if isinstance(channel, discord.DMChannel):
            content = f"<@&{MOD_ROLE}> : The mods were called with the {LOUDSPEAKER} emoji in private correspondence with the bot. Post:\n\n{react.message.content}"
        else:
            # If not in DMs, then only accept if it was a TextChannel on TBD
            guild = react.message.channel.guild
            if guild is None or guild.id != SERVER_ID or not isinstance(channel, discord.TextChannel):
                return

            try: 
                await react.remove(user)
            except discord.HTTPException:
                pass

            content = f"<@&{MOD_ROLE}> : The mods were called with the {LOUDSPEAKER} emoji by {user.mention} in {channel.mention}.\nLINK : <{react.message.jump_url}>\n. Post by {react.message.author.mention}: \n\n{react.message.content}"

        await self.logger_channel.send(content[:1990])
