import discord
from discord.ext import commands


class Poll(commands.Cog):
    def __init__(self, bot, db_connection):
        self.bot = bot
        self.db = db_connection

    @commands.command()
    async def poll(self, ctx, question: str, *options: str):
        if len(options) < 2:
            return await ctx.send("A poll must have at least two options.")
        if len(options) > 10:
            return await ctx.send("A poll cannot have more than 10 options.")

        description = []
        for idx, option in enumerate(options, start=1):
            description.append(f"{idx}. {option}")
        embed = discord.Embed(
            title=question, description="\n".join(description), color=0x00FF00
        )
        poll_message = await ctx.send(embed=embed)

        for idx in range(len(options)):
            await poll_message.add_reaction(chr(0x1F1E6 + idx))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return
        print(f"Received {reaction.emoji} from {user} for poll.")
