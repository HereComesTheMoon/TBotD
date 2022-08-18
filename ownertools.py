import discord
from discord.ext import commands
import botlog as bl
from aiosqlite import Connection

from config import is_owner, OWNER_ID, CATSCREAM, IDGI


class OwnerTools(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Connection):
        self.bot = bot

        self.db = db

        _owner = bot.get_user(OWNER_ID)
        assert _owner is not None
        self.owner: discord.User = _owner

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

    @commands.command(hidden=True)
    @is_owner()
    async def poast(self, ctx: commands.Context, *, arg: str):
        """There is no help for you."""
        bl.log(self.poast, ctx)
        if ',' in arg:  # Format argument, split desired channel from post to be poasted
            iid, what = arg.split(sep=',', maxsplit=1)
            iid, what = int(iid.strip()), what.strip()

            try:
                channel = await self.bot.fetch_channel(iid)
                if isinstance(channel, discord.TextChannel):
                    await channel.send(what)
                else:
                    await ctx.reply("Unable to poast. This is not a text channel.")
                    await ctx.message.add_reaction(IDGI)
            except discord.NotFound:
                user = await self.bot.fetch_user(iid)
                await user.send(what)
            except discord.HTTPException:
                bl.error_log.exception("Unable to poast.")
                await ctx.reply("Unable to poast!")
                await ctx.message.add_reaction(IDGI)


    @commands.command(hidden=True)
    @is_owner()
    async def kill(self, ctx: commands.Context):
        bl.log(self.kill, ctx)
        print("Shutdown command received.")
        await ctx.message.add_reaction(CATSCREAM)
        await self.db.close()
        await self.bot.close()


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        bl.joinleave_log.warning(f"User {member} joined {member.guild} ({member.guild.id}).")
        await self.owner.send(content=f"User {member} joined {member.guild} ({member.guild.id}). {member.display_avatar.url}")


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        bl.joinleave_log.warning(f"User {member} left {member.guild} ({member.guild.id}). Joined at {member.joined_at}.")
        await self.owner.send(content=f"User {member} left {member.guild} ({member.guild.id}). Joined at {member.joined_at}. {member.display_avatar.url}")

