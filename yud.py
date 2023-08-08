from typing import Optional, Tuple
import discord
from timeywimey import right_now, epoch2iso
from discord.ext import commands, tasks
from io import BytesIO
import botlog as bl
from PIL import Image
import datetime as dt
from zoneinfo import ZoneInfo
from config import CATPOUT, CATSCREAM, LOAD_YUD
from tabulate import tabulate
import random
import asyncio


class Yud(commands.Cog):
    def __init__(self, bot: commands.Bot, db):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(
            everyone=False, users=False, roles=False, replied_user=False
        )
        self.yud_loop.start()
        self.db = db

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        rng = random.randint(1, 24_000)
        if 40 < rng:
            return

        today = dt.datetime.now().astimezone(ZoneInfo("EST")).date()
        if (
            "yud" in msg.content.lower()
            or (today.month == 4 and today.day == 1)
            or rng == 1
        ):
            yud = YudImage()
            await msg.reply(
                allowed_mentions=self.ping_priv, file=await yud.get_discord_file()
            )
            cur = await self.db.cursor()
            # yuds (date INT, userID INT, postID INT, width INT, height INT, quality INT)
            await cur.execute(
                """
                INSERT INTO yuds 
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                [
                    int(dt.datetime.now().timestamp()),
                    msg.author.id,
                    msg.id,
                    yud.width,
                    yud.height,
                    yud.quality,
                ],
            )
            await self.db.commit()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def yudboard(self, ctx: commands.Context):
        cur = await self.db.cursor()
        await cur.execute("""SELECT date, userID, postID, height, width FROM yuds""")
        table_data = list(
            (date, userID, postID, height, width, height * width)
            for date, userID, postID, height, width in await cur.fetchall()
        )
        table_data.sort(key=lambda row: row[-1], reverse=True)
        s = [
            f"Board of rare Yuds. Thus far discovered: {len(table_data)}. Ordered by total magnitude:"
        ]
        for k, (date, userID, _, height, width, size) in enumerate(table_data[:5], 1):
            date = f"<t:{date}:D>"
            user = self.bot.get_user(userID).name
            s.append(
                f"{k} :: Discovered by {user} on {date}. Height: {height}. Girth: {width}. Total magnitude: {size}"
            )
        res = "\n\n".join(s)
        await ctx.reply(res)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_yudminders(self, ctx: commands.Context, *, post: str = ""):
        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT
            userID,
            MIN(due) AS next_yud,
            MAX(due) AS last_yud,
            COUNT(due) AS num_yuds
            FROM yudminders
            GROUP BY userID;"""
        )

        res = [
            (
                self.bot.get_user(p["userID"]).name,
                p["num_yuds"],
                epoch2iso(p["next_yud"]),
                epoch2iso(p["last_yud"]),
            )
            for p in await cur.fetchall()
        ]
        content = (
            "```"
            + tabulate(res, headers=["User", "#Yuds pending", "Next Yud", "Cooldown"])
            + "```"
        )

        await ctx.reply(content=content)

    @tasks.loop(minutes=5)
    async def yud_loop(self):
        await self.queue_yudminders()

    async def cog_unload(self):
        self.yud_loop.stop()

    async def queue_yudminders(self):
        now = right_now()
        cur = await self.db.cursor()
        await cur.execute(
            """
            SELECT oid, * 
            FROM yudminders 
            WHERE (?) <= due
            AND due <= (?)
            ORDER BY due ASC
            """,
            [now, now + 300],
        )
        yudminders = await cur.fetchall()

        await cur.execute(
            """
            DELETE
            FROM yudminders
            WHERE (?) <= due
            AND due <= (?);
            """,
            [now, now + 300],
        )
        await self.db.commit()

        task_stack = [
            asyncio.create_task(self.send_yudminder(row["userID"], row["due"]))
            for row in yudminders
        ]
        if task_stack:
            await asyncio.wait(task_stack)

    async def send_yudminder(self, userID: int, due: int):
        user = self.bot.get_user(userID)
        if user is None:
            bl.error_log.exception(
                f"Yudminders could not find user with id {userID}, weird!"
            )
            return
        delay = due - right_now()
        await asyncio.sleep(max(delay, 1))
        try:
            yud = await YudImage().get_discord_file()
            await user.send(file=yud)
        except discord.errors.Forbidden:
            bl.error_log.error(f"{user} probably has the bot blocked. Sad!")
        except discord.HHTTPException:
            bl.error_log.error(f"Dropped a Yud for {user}, irrelevant.")

    @commands.command()
    async def yud(self, ctx: commands.Context, *, post: str = ""):
        """yud"""
        bl.log(self.yud, ctx)
        if isinstance(ctx.channel, discord.channel.DMChannel):
            yud = await YudImage().get_discord_file()
            await ctx.reply(allowed_mentions=self.ping_priv, file=yud)
            return

        yudminders = await self.get_yudminders_for(ctx.author.id)

        if 5 <= len(yudminders):
            await ctx.message.add_reaction(CATSCREAM)
        elif yudminders:
            await ctx.message.add_reaction(CATPOUT)
            await self.queue_yudminder(ctx.author.id)
        else:
            yud = await YudImage().get_discord_file()
            await ctx.reply(allowed_mentions=self.ping_priv, file=yud)
            await self.queue_yudminder(ctx.author.id)

    async def queue_yudminder(self, userID: int):
        d = dt.timedelta(days=7 / 3)
        today = dt.datetime.now().astimezone(ZoneInfo("EST")).date()
        if today.month == 4 and today.day == 1:
            d = dt.timedelta(minutes=7)
        # Mean lognorm(mu, sigma) = exp(mu + (sigma**2)/2)
        # mu = 0, sigma = 1.5 => Mean ~= 3
        # timedelta of 7/3 days => approximately one week until yud refresh
        scale = random.lognormvariate(0, 1.5)
        d *= scale
        due = dt.datetime.now() + d
        due = int(due.timestamp())

        cur = await self.db.cursor()
        await cur.execute(
            """
                INSERT INTO yudminders
                VALUES (?, ?);
            """,
            [userID, due],
        )
        await self.db.commit()

        await self.queue_yudminders()

    async def get_yudminders_for(self, userID: int) -> list:
        cur = await self.db.cursor()
        now = right_now()
        await cur.execute(
            """
            SELECT oid, * 
            FROM yudminders 
            WHERE userID LIKE (?)
            AND (?) <= due
            ORDER BY due ASC
            LIMIT 10
            """,
            [userID, now],
        )
        return await cur.fetchall()


class YudImage:
    im = Image.new("RGB", (200, 200))
    try:
        im = Image.open("./yud.jpeg")
    except FileNotFoundError as e:
        if LOAD_YUD:
            print(f"No Yud found error: {e}")
            bl.error_log.exception(f"No Yud found error: {e}")
            raise e

    def __init__(
        self, size: Optional[Tuple[int, int]] = None, quality: Optional[int] = None
    ):
        if size is None:
            self.width = round(YudImage.im.size[0] * random.uniform(0.001, 5))
            self.height = round(YudImage.im.size[1] * random.uniform(0.001, 1.5))
        else:
            self.width = size[0]
            self.height = size[0]

        if quality is not None and 1 <= quality <= 100:
            self.quality = int(quality)
        else:
            self.quality = int(random.uniform(1, 75))

    async def get_discord_file(self):
        yud = await self.get_image_file()
        temp = BytesIO()
        yud.save(temp, format="jpeg", quality=self.quality)
        temp.seek(0)
        return discord.File(temp, filename="yud.jpeg")

    async def get_image_file(self):
        return YudImage.im.resize((self.width, self.height))
