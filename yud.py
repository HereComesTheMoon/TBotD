import discord
from discord.ext import commands
from io import BytesIO
import botlog as bl
from PIL import Image
import datetime as dt
from zoneinfo import ZoneInfo
from config import is_owner
import random


class Yud(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
        self.stored_posts: dict[int, discord.Message] = {} # (id of original message, bot response message), use to delete bot response if original is deleted

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        today = dt.datetime.now().astimezone(ZoneInfo('EST')).date()
        if today.month != 4 and today.day != 1:
            return

        yud = Image.open('./yud.jpeg')
        yud = yud.resize((round(yud.size[0] * random.uniform(0.001,0.5)),
        round(yud.size[1] * random.uniform(0.001,0.05))))
        temp = BytesIO()
        yud.save(temp, format='jpeg')
        temp.seek(0)
        await msg.channel.send(file=discord.File(temp,filename='yud.jpeg'))


    @commands.command(hidden=True)
    @is_owner()
    async def yud(self, ctx: commands.Context, *, post: str = ""):
        """yud"""
        bl.log(self.yud, ctx)
        yud = Image.open('./yud.jpeg')
        yud = yud.resize((round(yud.size[0] * random.uniform(0.001,5)),
        round(yud.size[1] * random.uniform(0.001,1.5))))
        temp = BytesIO()
        yud.save(temp, format='jpeg')
        temp.seek(0)
        await ctx.channel.send(file=discord.File(temp,filename='yud.jpeg'))
