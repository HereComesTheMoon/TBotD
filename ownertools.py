import discord
from discord.ext import commands
import botlog as bl
from aiosqlite import Connection

from tabulate import tabulate

from config import CATSCREAM, IDGI, BOT_JOINED_AT


class OwnerTools(commands.Cog, name="Tools"):
    def __init__(
        self, bot: commands.Bot, db: Connection, tbd: discord.Guild, went_online_at: int
    ):
        self.bot = bot

        self.db = db

        self.tbd = tbd

        self.went_online_at = went_online_at

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

    @commands.command(hidden=True)
    @commands.is_owner()
    async def poast(self, ctx: commands.Context, *, arg: str):
        """There is no help for you."""
        bl.log(self.poast, ctx)
        if "," in arg:  # Format argument, split desired channel from post to be poasted
            iid, what = arg.split(sep=",", maxsplit=1)
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
    @commands.is_owner()
    async def kill(self, ctx: commands.Context):
        bl.log(self.kill, ctx)
        print("Shutdown command received.")
        await ctx.message.add_reaction(CATSCREAM)
        await self.db.close()
        await self.bot.close()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        bl.joinleave_log.warning(
            f"User {member} joined {member.guild} ({member.guild.id})."
        )
        await self.bot.get_user(self.bot.owner_id).send(
            content=f"User {member} joined {member.guild} ({member.guild.id}). {member.display_avatar.url}"
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        bl.joinleave_log.warning(
            f"User {member} left {member.guild} ({member.guild.id}). Joined at {member.joined_at}."
        )
        await self.bot.get_user(self.bot.owner_id).send(
            content=f"User {member} left {member.guild} ({member.guild.id}). Joined at {member.joined_at}. {member.display_avatar.url}"
        )

    @commands.command()
    async def stats(self, ctx: commands.Context):
        """Display statistics of the server!"""
        bl.log(self.stats, ctx)
        data = []

        data.append(
            f"I joined the server <t:{int(BOT_JOINED_AT)}:R>, and the last time I was restarted was <t:{self.went_online_at}:R>."
        )

        cur = await self.db.cursor()
        await cur.execute("""SELECT COUNT(*) AS count FROM suggestions""")
        # Fetches the first (and in this case only row), and accesses its key.
        # RowFactory setting allows this.
        result = await cur.fetchone()
        assert result is not None
        result = result["count"]
        data.append(f"I have counted {result} server-name suggestions!")

        cur = await self.db.cursor()
        await cur.execute("""SELECT COUNT(*) AS count FROM used_titles""")
        result = await cur.fetchone()
        assert result is not None
        result = result["count"]
        data.append(f"I have counted {result} different server names!")

        cur = await self.db.cursor()
        await cur.execute(
            '''SELECT COUNT(*) AS count FROM memories WHERE status != "Past"'''
        )
        result = await cur.fetchone()
        assert result is not None
        result = result["count"]
        data.append(f"There are {result} reminders waiting to be triggered!")

        cur = await self.db.cursor()
        await cur.execute("""SELECT SUM(uses) AS count FROM emojis_default""")
        result = await cur.fetchone()
        assert result is not None
        result = result["count"]
        data.append(
            f"I have counted a total of {result} reactions with default emojis!"
        )

        cur = await self.db.cursor()
        await cur.execute("""SELECT SUM(uses) AS count FROM emojis_custom""")
        result = await cur.fetchone()
        assert result is not None
        result = result["count"]
        data.append(f"I have counted a total of {result} reactions with custom emojis!")

        cur = await self.db.cursor()
        emojis = tuple([emoji.id for emoji in self.tbd.emojis])
        await cur.execute(
            f"""SELECT * FROM emojis_custom 
                              WHERE emoji_id IN({','.join(['?'] * len(emojis))})
                              ORDER BY RANDOM() 
                              LIMIT 3""",
            emojis,
        )
        result = await cur.fetchall()
        for row in result:
            data.append(
                f"<:{row['name']}:{row['emoji_id']}> has been used {row['uses']} times!"
            )

        poast = "Loading statistics... \n" + "\n".join(data)
        await ctx.reply(content=poast)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def least_used_emojis(self, ctx: commands.Context, *, post: str = ""):
        emojis = tuple([emoji.id for emoji in self.tbd.emojis])
        cur = await self.db.cursor()
        await cur.execute(
            f"""SELECT name, emoji_id, uses FROM emojis_custom
                              WHERE emoji_id IN({','.join(['?'] * len(emojis))})
                              ORDER BY uses ASC""",
            emojis,
        )
        answer = "Here's a table of least-used emojis:"

        result = [
            (name, emoji_id, uses) for name, emoji_id, uses in await cur.fetchall()
        ]
        used_check = {x[1] for x in result}
        not_used = [
            (emoji.name, emoji.id, 0)
            for emoji in self.tbd.emojis
            if emoji.id not in used_check
        ]

        least_used = [
            (uses, f"<:{name}:{emoji_id}>")
            for name, emoji_id, uses in not_used + result
        ]
        last = least_used[0][0] - 1
        for uses, name in least_used:
            if (
                len(answer) + len(name) < 1900
            ):  # Ensure the message fits into the discord messaging field
                if last != uses:
                    answer += f"\n{uses} : {name}"
                    last = uses
                else:
                    answer += f", {name}"
            else:
                break
        await ctx.reply(answer)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def printdbs(self, ctx: commands.Context):
        bl.log(self.printdbs, ctx)
        cur = await self.db.cursor()
        await cur.execute("""SELECT * from sqlite_master""")
        tabs = tabulate([tuple(x) for x in await cur.fetchall()])
        await ctx.reply(content="```" + tabs + "```")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def printdb(self, ctx: commands.Context, *, post: str = ""):
        # TODO: This is horrible, and prone to wrecking your stuff if you accidentally SQL inject yourself. Change!
        bl.log(self.printdb, ctx)
        cur = await self.db.cursor()
        await cur.execute(
            """SELECT name FROM sqlite_master
                             WHERE type ='table'
                             AND name NOT LIKE 'sqlite_%';"""
        )
        table_names = [tuple(x)[0] for x in await cur.fetchall()]
        if post not in table_names:
            await ctx.message.add_reaction(IDGI)
            return
        try:
            await cur.execute("""SELECT * FROM """ + post + """ """ + """LIMIT 5""")
            tabs = tabulate([tuple(x) for x in await cur.fetchall()])
        except:
            bl.error_log.exception(
                "Oh god oh no this can't be happening sql injection or worse."
            )
            await ctx.reply(
                content="I warned you about SQL injection. Why didn't you listen?"
            )
            return
        await ctx.reply(content=post + "\n```" + tabs + "```")
