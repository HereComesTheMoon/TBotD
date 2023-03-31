import discord
from discord.ext import commands, tasks
from io import BytesIO
import botlog as bl
from PIL import Image
import datetime as dt
from zoneinfo import ZoneInfo
from config import is_owner, in_dms, in_bot_channel, CATPOUT
import random
import asyncio
import aiosqlite
from collections import defaultdict

"""
  Each time you yud in an inappropriate channel, a yudminder gets queued up.
If you have more than three, you can't yud in a public channel anymore.  
"""

class Yud(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
        self.yud_loop.start()
        self.yud = Image.open('./yud.jpeg')
        self.yudminders: dict[int, list[int]] = defaultdict(set)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        rng = random.randint(1, 24_000)
        if 40 < rng:
            return

        today = dt.datetime.now().astimezone(ZoneInfo('EST')).date()
        if 'yud' in msg.content.lower() or (today.month == 4 and today.day == 1) or rng == 1:
            yud = self.get_yud()
            await msg.channel.send(file=yud)


    @commands.command(hidden=True)
    @is_owner()
    async def yud(self, ctx: commands.Context, *, post: str = ""):
        """yud"""
        bl.log(self.yud, ctx)
        if in_dms(ctx) or in_bot_channel(ctx):
            yud = self.get_yud()
            await ctx.reply(allowed_mentions=self.ping_priv, file=yud)
        if self.yudminders[ctx.author.id]:
            await self.queue_yudminder(ctx.author.id)
            ctx.message.add_reaction(CATPOUT)
            return

        await self.queue_yudminder(ctx.author.id)
        yud = self.get_yud()
        await ctx.reply(allowed_mentions=self.ping_priv, file=yud)


    async def get_yud(self, x: float=5, y: float=1.5) -> discord.File:
        yud = self.yud.resize((round(self.yud.size[0] * random.uniform(0.001, x)),
        round(self.yud.size[1] * random.uniform(0.001, y))))
        temp = BytesIO()
        yud.save(temp, format='jpeg')
        temp.seek(0)
        return discord.File(temp, filename='yud.jpeg')

    async def queue_yudminder(self, userID:int):
        d = dt.timedelta(days=7)
        scale = random.lognormvariate(0, 1.5)
        d *= scale
        due = dt.datetime.now() + d
        due = int(due.timestamp())
        self.yudminders[userID].add(due)


    @tasks.loop(hours=1)
    async def yud_loop(self):
        await self.queue_yuds()

    @yud_loop.before_loop
    async def before_yud_loop(self):
        await self.bot.wait_until_ready()
        yudminders = []
        now = int(dt.datetime.now().timestamp())
        for userID, yuds_due in self.yudminders.items():
            for due in yuds_due:
                if due <= now + 3600 + 60:
                    yudminders.append((userID, due))
        task_stack = [asyncio.create_task(self.yudify(userID, due)) for userID, due in yudminders]
        if task_stack:
            await asyncio.wait(task_stack)

    async def yudify(self, userID: int, due: int):
        user = self.bot.get_user(userID)
        delay = due - int(dt.datetime.now().timestamp())
        await asyncio.sleep(max(delay, 1))
        try:
            yud = self.get_yud()
            await user.send(file=yud)
            self.yudminders[userID].discard(due)
        except discord.HHTTPException:
            bl.error_log.exception(f"Dropped a Yud for {user}, irrelevant.")
