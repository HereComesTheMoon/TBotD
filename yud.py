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
from collections import defaultdict


class Yud(commands.Cog):
    def __init__(self, bot: commands.Bot, db):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
        self.yud_loop.start()
        self.yudim = Image.open('./yud.jpeg')
        self.yudminders: dict[int, list[int]] = defaultdict(set)
        self.db = db

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        rng = random.randint(1, 24_000)
        if 40 < rng:
            return

        today = dt.datetime.now().astimezone(ZoneInfo('EST')).date()
        if 'yud' in msg.content.lower() or (today.month == 4 and today.day == 1) or rng == 1:
            yud = self.yudim.resize((round(self.yudim.size[0] * random.uniform(0.001, 5)),
            round(self.yudim.size[1] * random.uniform(0.001, 1.5))))
            temp = BytesIO()
            yud.save(temp, format='jpeg')
            temp.seek(0)
            file = discord.File(temp, filename='yud.jpeg')
            await msg.reply(allowed_mentions=self.ping_priv, file=file)
            cur = await self.db.cursor()
# yuds (date INT, userID INT, postID INT, height INT, width INT)
            await cur.execute('''INSERT INTO yuds 
                                 VALUES (?, ?, ?, ?, ?);''',
                              [
                    int(dt.datetime.now().timestamp()),
                    msg.author.id,
                    msg.id,
                    yud.size[0],
                    yud.size[1]
            ])
            await self.db.commit()


    @commands.command(hidden=True)
    @is_owner()
    async def show_yudminders(self, ctx: commands.Context, *, post:str = ""):
        s = []
        for user, yudminders in self.yudminders.items():
            if not yudminders:
                continue
            user = self.bot.get_user(user)
            nxt = sorted(yudminders).pop(0)
            s.append(f"{user} : {len(yudminders)=} : <t:{nxt}:R>")
        await ctx.reply("\n".join(s))
            
    
    @commands.command()
    async def yud(self, ctx: commands.Context, *, post: str = ""):
        """yud"""
        bl.log(self.yud, ctx)
        if in_dms(ctx):
            yud = await self.get_yud()
            await ctx.reply(allowed_mentions=self.ping_priv, file=yud)
            return
        if self.yudminders[ctx.author.id]:
            await ctx.message.add_reaction(CATPOUT)
            await self.queue_yudminder(ctx.author.id)
            return

        yud = await self.get_yud()
        await ctx.reply(allowed_mentions=self.ping_priv, file=yud)
        await self.queue_yudminder(ctx.author.id)


    async def get_yud(self, x: float=5, y: float=1.5) -> discord.File:
        yud = self.yudim.resize((round(self.yudim.size[0] * random.uniform(0.001, x)),
        round(self.yudim.size[1] * random.uniform(0.001, y))))
        temp = BytesIO()
        yud.save(temp, format='jpeg')
        temp.seek(0)
        return discord.File(temp, filename='yud.jpeg')

    async def queue_yudminder(self, userID:int):
        d = dt.timedelta(days=7)
        today = dt.datetime.now().astimezone(ZoneInfo('EST')).date()
        if today.month == 4 and today.day == 1:
            d = dt.timedelta(minutes=7)
        scale = random.lognormvariate(0, 1.5)
        d *= scale
        due = dt.datetime.now() + d
        due = int(due.timestamp())
        self.yudminders[userID].add(due)
        await self.queue_yuds()


    @tasks.loop(hours=1)
    async def yud_loop(self):
        await self.queue_yuds()

    @yud_loop.before_loop
    async def before_yud_loop(self):
        await self.bot.wait_until_ready()
        yudminders = []
        now = int(dt.datetime.now().timestamp())
        for userID, yuds_due in self.yudminders.items():
            delet = set()
            for due in yuds_due:
                if due <= now + 3600 + 60:
                    yudminders.append((userID, due))
                    delet.add(due)
            for due in delet:
                yuds_due.discard(due)
        task_stack = [asyncio.create_task(self.yudify(userID, due)) for userID, due in yudminders]
        if task_stack:
            await asyncio.wait(task_stack)

    async def queue_yuds(self):
        yudminders = []
        now = int(dt.datetime.now().timestamp())
        for userID, yuds_due in self.yudminders.items():
            delet = set()
            for due in yuds_due:
                if due <= now + 3600 + 60:
                    yudminders.append((userID, due))
            for due in delet:
                yuds_due.discard(due)
        task_stack = [asyncio.create_task(self.yudify(userID, due)) for userID, due in yudminders]
        if task_stack:
            await asyncio.wait(task_stack)

    async def yudify(self, userID: int, due: int):
        user = self.bot.get_user(userID)
        delay = due - int(dt.datetime.now().timestamp())
        await asyncio.sleep(max(delay, 1))
        try:
            yud = await self.get_yud()
            await user.send(file=yud)
            self.yudminders[userID].discard(due)
        except discord.HHTTPException:
            bl.error_log.exception(f"Dropped a Yud for {user}, irrelevant.")
