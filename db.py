import asyncio
import discord
from discord.ext import tasks, commands
import timeywimey
import datetime
import botlog as bl

from tabulate import tabulate
import config as pm


# Database and aiosqlite notes:
# Opening a database connection is expensive.
# Context manager automatically commits or rolls back at the end
# Context manager does not close connections automatically.
# Edit: This is fine, keep a single connection open all the time, store as global bot variable. This works great.
# aiosqlite is an async version of sqlite3

class Database(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ping_priv = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)
        # CURRENTLY DISABLED
        # self.loop_send_title_suggestions.start()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction_event: discord.RawReactionActionEvent):
        if reaction_event.guild_id is None or reaction_event.member.bot or reaction_event.guild_id != pm.SERVER_ID:
            return 0
        if reaction_event.emoji.is_custom_emoji():
            await self.custom_emoji_reacted(reaction_event.emoji)
        else:
            await self.emoji_reacted(reaction_event.emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, reaction_event: discord.RawReactionActionEvent):
        member = await self.bot.fetch_user(reaction_event.user_id)
        if reaction_event.guild_id is None or member.bot or reaction_event.guild_id != pm.SERVER_ID:
            return 0
        if reaction_event.emoji.is_custom_emoji():
            await self.custom_emoji_react_removed(reaction_event.emoji)
        else:
            await self.emoji_react_removed(reaction_event.emoji)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        # TODO: Also strip all symbols when checking whether a word fits the TBD scheme
        if msg.author.bot or not pm.on_tbd(msg):
            return 0
        words = msg.content.split()
        if len(words) >= 3:
            to, be, determined = words[0], words[1], words[2]
            if to[0].lower() == 't' and be[0].lower() == 'b' and determined[0].lower() == 'd':
                now = timeywimey.right_now()
                await self.add_tbd_suggestion(
                    now,
                    msg.author.id,
                    msg.id,
                    to,
                    be,
                    determined
                )

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.name != after.name:
            words = after.name.split()
            if len(words) >= 3:
                to, be, determined = words[0], words[1], words[2]
                if to[0].lower() == 't' and be[0].lower() == 'b' and determined[0].lower() == 'd':
                    await self.add_tbd_used_title(timeywimey.right_now(), to, be, determined)

    # CURRENTLY DISABLED
    # If reenable, make sure to remember to install Pytz or to rewrite
    # @tasks.loop(hours=1)
    # async def loop_send_title_suggestions(self):
        # now = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin'))
        # brit = datetime.datetime(now.year, now.month, now.day, 6, 0, tzinfo=pytz.timezone('Europe/London'))
        # delta = brit - now
        # seconds = delta.total_seconds()
        # if 0 <= seconds <= 3600:
            # await asyncio.sleep(max(seconds, 1))
            # cur = await self.bot.db.cursor()
            # await cur.execute('''SELECT * 
                    # FROM suggestions s
                    # LEFT JOIN used_titles u
                    # ON s.t LIKE u.t
                        # AND s.b LIKE u.b
                        # AND s.d LIKE u.d
                    # WHERE u.t is NULL
                        # OR u.b is NULL
                        # OR u.d is NULL
                    # ORDER BY s.rowid DESC
                    # LIMIT 10''')
            # output = "Guten Morgen, [ADMIN NAME PENDING]. I hope that you're having a pleasant day. " \
                     # "Here is a list of server name suggestions:\n" + \
                     # "\n".join([" ".join(tuple(row)[3:6]) for row in await cur.fetchall()])
            # user = self.bot.get_user(pm.OWNER_ID)
            # await user.send(content=output)

    # @loop_send_title_suggestions.before_loop
    # async def before_loop(self):
        # await self.bot.wait_until_ready()

    @commands.command(hidden=True)
    @pm.is_owner()
    async def least_used_emojis(self, ctx: commands.Context, *, post: str = ""):
        emojis = tuple([emoji.id for emoji in self.bot.get_guild(pm.SERVER_ID).emojis])
        cur = await self.bot.db.cursor()
        await cur.execute(f'''SELECT name, emoji_id, uses FROM emojis_custom
                              WHERE emoji_id IN({','.join(['?'] * len(emojis))})
                              ORDER BY uses ASC''', emojis)
        answer = "Here's a table of least-used emojis:"

        result = [(name, emoji_id, uses) for name, emoji_id, uses in await cur.fetchall()]
        used_check = {x[1] for x in result}
        not_used = [(emoji.name, emoji.id, 0) for emoji in self.bot.get_guild(pm.SERVER_ID).emojis if
                    emoji.id not in used_check]

        least_used = [(uses, f"<:{name}:{emoji_id}>") for name, emoji_id, uses in not_used + result]
        last = least_used[0][0] - 1
        for uses, name in least_used:
            if len(answer) + len(name) < 1900:
                if last != uses:
                    answer += f"\n{uses} : {name}"
                    last = uses
                else:
                    answer += f", {name}"
            else:
                break
        await ctx.reply(answer)

    @commands.command(hidden=True)
    @pm.is_owner()
    async def printdbs(self, ctx: commands.Context):
        bl.log(self.printdbs, ctx)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT * from sqlite_master''')
        tabs = tabulate([tuple(x) for x in await cur.fetchall()])
        await ctx.reply(content="```" + tabs + "```")

    @commands.command(hidden=True)
    @pm.is_owner()
    async def printdb(self, ctx: commands.Context, *, post: str = ""):
        # TODO: This is horrible, and prone to wrecking your stuff if you accidentally SQL inject yourself. Change!
        bl.log(self.printdb, ctx)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT name FROM sqlite_master
                             WHERE type ='table'
                             AND name NOT LIKE 'sqlite_%';''')
        table_names = [tuple(x)[0] for x in await cur.fetchall()]
        if post not in table_names:
            await ctx.message.add_reaction(pm.IDGI)
            return
        try:
            await cur.execute('''SELECT * FROM ''' + post + ''' ''' + '''LIMIT 5''')
            tabs = tabulate([tuple(x) for x in await cur.fetchall()])
        except:
            bl.error_log.exception("Oh god oh no this can't be happening sql injection or worse.")
            await ctx.reply(content="I warned you about SQL injection. Why didn't you listen?")
            return
        await ctx.reply(content=post + "\n```" + tabs + "```")

    @commands.command()
    async def stats(self, ctx: commands.Context):
        """Display statistics of the server!"""
        bl.log(self.stats, ctx)
        data = []

        data.append(f"I joined the server <t:{int(pm.BOT_JOINED_AT)}:R>, and the last time I was restarted was <t:{self.bot.went_online_at}:R>.")

        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT COUNT(*) AS count FROM suggestions''')
        # Fetches the first (and in this case only row), and accesses its key.
        # RowFactory setting allows this.
        result = (await cur.fetchone())['count']
        data.append(f"I have counted {result} server-name suggestions!")

        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT COUNT(*) AS count FROM used_titles''')
        result = (await cur.fetchone())['count']
        data.append(f"I have counted {result} different server names!")

        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT COUNT(*) AS count FROM memories
                             WHERE status != "Past"''')
        result = (await cur.fetchone())['count']
        data.append(f"There are {result} reminders waiting to be triggered!")

        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT SUM(uses) AS count FROM emojis_default''')
        result = (await cur.fetchone())['count']
        data.append(f"I have counted a total of {result} reactions with default emojis!")

        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT SUM(uses) AS count FROM emojis_custom''')
        result = (await cur.fetchone())['count']
        data.append(f"I have counted a total of {result} reactions with custom emojis!")

        cur = await self.bot.db.cursor()
        emojis = tuple([emoji.id for emoji in self.bot.get_guild(pm.SERVER_ID).emojis])
        await cur.execute(f'''SELECT * FROM emojis_custom 
                              WHERE emoji_id IN({','.join(['?'] * len(emojis))})
                              ORDER BY RANDOM() 
                              LIMIT 3''', emojis)
        result = await cur.fetchall()
        for row in result:
            data.append(f"<:{row['name']}:{row['emoji_id']}> has been used {row['uses']} times!")

        poast = "Loading statistics... \n" + "\n".join(data)
        await ctx.reply(content=poast)

    async def add_tbd_suggestion(self, date: int, user_id: int, post_id: int, to: str, be: str, determined: str):
        # TABLE suggestions (date INT, userID INT, postID INT, t TEXT, b TEXT, d TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''INSERT INTO suggestions 
                             VALUES (?,?,?,?,?,?)''',
                          [date, user_id, post_id, to, be, determined])
        await self.bot.db.commit()

    async def add_tbd_used_title(self, date: int, to: str, be: str, determined: str):
        # TABLE used_title (date INT, t TEXT, b TEXT, d TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''INSERT INTO used_titles 
                             VALUES (?,?,?,?)''',
                          [date, to, be, determined])
        await self.bot.db.commit()

    async def emoji_reacted(self, emoji: discord.PartialEmoji):
        # TABLE emojis_default (name TEXT, uses INT)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT * 
                             FROM emojis_default 
                             WHERE name = (?)''',
                          [emoji.name])
        rows = list(await cur.fetchall())
        if not rows:
            await cur.execute('''INSERT INTO emojis_default 
                                 VALUES (?,?)''',
                              [emoji.name, 1])
        else:
            await cur.execute('''UPDATE emojis_default 
                                 SET uses = uses + 1 
                                 WHERE name = (?)''',
                              [emoji.name])
        await self.bot.db.commit()

    async def emoji_react_removed(self, emoji: discord.PartialEmoji):
        # TABLE emojis_default (name TEXT, uses INT)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT * 
                             FROM emojis_default 
                             WHERE name = (?)''',
                          [emoji.name])
        rows = list(await cur.fetchall())
        if not rows:
            pass
        else:
            await cur.execute('''UPDATE emojis_default 
                                 SET uses = uses - 1 
                                 WHERE name = (?)''',
                              [emoji.name])
        await self.bot.db.commit()

    async def custom_emoji_reacted(self, emoji: discord.PartialEmoji):
        # TABLE emojis_reacts (emoji_id INTEGER, name TEXT, url TEXT, uses INT)
        cur = await self.bot.db.cursor()
        emoji_id = emoji.id
        await cur.execute('''SELECT * 
                             FROM emojis_custom 
                             WHERE emoji_id = (?)''',
                          [emoji_id])
        rows = list(await cur.fetchall())
        if not rows:
            await cur.execute('''INSERT INTO emojis_custom 
                                 VALUES (?,?,?,?)''',
                              [emoji_id, emoji.name, str(emoji.url), 1])
        else:
            await cur.execute('''UPDATE emojis_custom 
                                 SET uses = uses + 1 
                                 WHERE emoji_id = (?)''',
                              [emoji_id])
        await self.bot.db.commit()

    async def custom_emoji_react_removed(self, emoji: discord.PartialEmoji):
        # TABLE emojis_reacts (emoji_id INTEGER, name TEXT, url TEXT, uses INT)
        cur = await self.bot.db.cursor()
        emoji_id = emoji.id
        await cur.execute('''SELECT * 
                             FROM emojis_custom 
                             WHERE emoji_id = (?)''',
                          [emoji_id])
        rows = list(await cur.fetchall())
        if not rows:
            pass
        else:
            await cur.execute('''UPDATE emojis_custom 
                                 SET uses = uses - 1 
                                 WHERE emoji_id = (?)''',
                              [emoji_id])
        await self.bot.db.commit()
