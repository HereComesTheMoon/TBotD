import discord
from discord.ext import tasks, commands
import asyncio
import aiosqlite
import datetime
import botlog as bl
import timeywimey

from config import CW_BAN_ROLE, BLINDED_ROLE, MUTED_ROLE, IDGI

# add_at / remove_at implement functions which add or remove a role at a given date.
# Only remove_at is used at the current time



class RoleManagement(commands.Cog):
    def __init__(self, bot: commands.Bot, tbd: discord.Guild):
        self.bot = bot
        self.loop.start()
        self.ping_priv = discord.AllowedMentions(everyone=False, roles=False, replied_user=False)
        self.TBD = tbd

        # self.TBD: discord.Guild = self.bot.get_guild(SERVER_ID) # Afaik this just didn't work? Check again

    # region commands
    @commands.command()
    async def cwbanme(self, ctx: commands.Context, *, post: str = ""):
        """CW-Ban yourself for a set amount of time. eg. !cwbanme 2 hours"""
        bl.log(self.cwbanme, ctx)
        await self.time_out(ctx, CW_BAN_ROLE, post)

    @commands.command()
    async def muteme(self, ctx: commands.Context, *, post: str = ""):
        """Mute yourself for a set amount of time. eg. !muteme 2 hours"""
        bl.log(self.muteme, ctx)
        await self.time_out(ctx, MUTED_ROLE, post)

    @commands.command()
    async def blindme(self, ctx: commands.Context, *, post: str = ""):
        """Blind yourself for a set amount of time. eg. !blindme 2 hours"""
        bl.log(self.blindme, ctx)
        await self.time_out(ctx, BLINDED_ROLE, post)

    @commands.command()
    async def cwbanmeat(self, ctx: commands.Context, *, post: str = ""):
        """CW-Ban yourself at a given time, for a set amount of time. eg. !cwbanmeat 5 min, 2 hours"""
        bl.log(self.cwbanmeat, ctx)
        await self.time_out_at(ctx, CW_BAN_ROLE, post)

    @commands.command()
    async def mutemeat(self, ctx: commands.Context, *, post: str = ""):
        """Mute yourself at a given time, for a set amount of time. eg. !mutemeat 10 hours, 2 hours"""
        bl.log(self.mutemeat, ctx)
        await self.time_out_at(ctx, MUTED_ROLE, post)

    @commands.command()
    async def blindmeat(self, ctx: commands.Context, *, post: str = ""):
        """Blind yourself at a given time, for a set amount of time. eg. !blindmeat 7 hours, 2 hours"""
        bl.log(self.blindmeat, ctx)
        await self.time_out_at(ctx, BLINDED_ROLE, post)


    @commands.command()
    async def when(self, ctx: commands.Context, *, post: str = ""):
        """Parse a time!"""
        bl.log(self.when, ctx)
        now, then, parse_status = timeywimey.parse_time(post)
        if not parse_status:
            await ctx.reply("Sorry, I was unable to parse this message.")
            return
        content = f"I parse this as <t:{then}:F>, ie. <t:{then}:R>. This is ``{then}`` in Unix time. Relative timestamps: \n"
        formats = [':t', ':T', ':d', ':D', '', ':F', ':R']
        content += "".join([f"Type ``<t:{then}{flag}>`` to write <t:{then}{flag}>.\n" for flag in formats])
        await ctx.reply(content=content)

    # @config.is_owner()
    # async def unban(self, ctx: commands.Context, *, user_id: str):
        # """Remove bot-applied roles from a user via a bot command. Can only be called by Mond. This is now unnecessary."""
        # bl.log(self.unban, ctx)
        # try:
            # member: discord.Member = self.TBD.get_member(int(user_id))
            # roles = [self.TBD.get_role(x) for x in [MUTED_ROLE, CW_BAN_ROLE, BLINDED_ROLE]]
            # for role in roles:
                # await member.remove_roles(role, reason="!unban command was called. Can only be called by Mond.")
            # await ctx.message.add_reaction(CATHEARTS)
        # except discord.HTTPException:
            # await ctx.message.add_reaction(IDGI)

    # endregion

    # region loops
    @tasks.loop(hours=1)
    async def loop(self):
        await self.queue_role_changes()

    @loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
        add_at = await self.read_add_at()
        remove_at = await self.read_remove_at()
        task_stack = [asyncio.create_task(self.add_role(x)) for x in add_at] \
                     + [asyncio.create_task(self.remove_role(x)) for x in remove_at]
        if task_stack:
            await asyncio.wait(task_stack)

    async def queue_role_changes(self):
        add_at = await self.read_add_at()
        remove_at = await self.read_remove_at()
        task_stack = [asyncio.create_task(self.add_role(x)) for x in add_at] \
                     + [asyncio.create_task(self.remove_role(x)) for x in remove_at]
        if task_stack:
            await asyncio.wait(task_stack)
    # endregion

    # region functions
    async def remove_role(self, row: aiosqlite.Row):
        """Removes a role based on some stored database query."""
        # TABLE remove_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        member: discord.Member = self.TBD.get_member(row['user_id'])
        role = self.TBD.get_role(row['role_id'])
        delay = row['due'] - timeywimey.right_now()
        await cur.execute('''UPDATE remove_at
                             SET status = "Present"
                             WHERE oid = (?)''',
                          [row['rowid']])
        await self.bot.db.commit()

        await asyncio.sleep(max(delay, 1))

        cur = await self.bot.db.cursor()
        try:
            await member.remove_roles(role, reason="Bot removed.")
        except discord.HTTPException:
            bl.error_log.exception("Bot role removal error!")
            await cur.execute('''UPDATE remove_at
                                 SET status = "Error"
                                 WHERE oid = (?)''',
                              [row['rowid']])
            await self.bot.db.commit()
            return
        await cur.execute('''UPDATE remove_at
                             SET status = "Past"
                             WHERE oid = (?)''',
                          [row['rowid']])
        await self.bot.db.commit()

    async def add_role(self, row: aiosqlite.Row):
        """Adds a role based on some stored database query."""
        # TABLE add_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        member: discord.Member = self.TBD.get_member(row['user_id'])
        role = self.TBD.get_role(row['role_id'])
        delay = row['due'] - timeywimey.right_now()

        await cur.execute('''UPDATE add_at
                             SET status = "Present"
                             WHERE oid = (?)''',
                          [row['rowid']])
        await self.bot.db.commit()

        await asyncio.sleep(max(delay, 1))

        cur = await self.bot.db.cursor()
        try:
            await member.add_roles(role, reason="Bot added.")
        except discord.HTTPException:
            bl.error_log.exception("Bot role addition error!")
            await cur.execute('''UPDATE add_at
                                 SET status = "Error"
                                 WHERE oid = (?)''',
                              [row['rowid']])
            await self.bot.db.commit()
            return 0  # Missing permissions

        await cur.execute('''UPDATE add_at
                             SET status = "Past"
                             WHERE oid = (?)''',
                          [row['rowid']])
        await self.bot.db.commit()

    async def time_out(self, ctx: commands.Context, role_id: int, post: str = ""):
        """Times a user out by parsing command, or (if already timed out) tells them how long the time-out is going
        to last. """
        author = self.TBD.get_member(ctx.author.id)
        if author is None:
            bl.error_log.exception("Tried to fetch a member which does not exist.")
            await ctx.message.add_reaction(IDGI)
            return

        role: discord.Role = self.TBD.get_role(role_id)
        if role is None:
            bl.error_log.exception("Tried to fetch a role which does not exist.")
            await ctx.message.add_reaction(IDGI)
            return

        if role in author.roles:
            due = await self.check_ban_length(author.id, role_id)
            if due:
                until = timeywimey.right_now() + due
                await ctx.reply(f"You're already timed out. You can go back to posting <t:{until}:R>, ie. <t:{until}>.")
            else:
                await ctx.reply(f"Sorry, I don't know anything about this. Something might've gone wrong. :cry:")
            return

        if post == "":
            await ctx.reply("You're not currently timed out.")
            return

        _, then, parse_status = timeywimey.parse_time(post)
        if parse_status == 0:
            await ctx.message.add_reaction(IDGI)
            return

        # Happy path etc.
        try:
            await author.add_roles(role, reason="Self-applied via bot command.")
        except discord.HTTPException:
            bl.error_log.exception("Time out error! Unable to add role to user, most likely.")
            await ctx.message.add_reaction(IDGI)
            return

        msg = f"You're timed out until <t:{then}>."
        await ctx.reply(msg, mention_author = False)
        try:
            await author.send(msg)
        except discord.HTTPException:
            bl.error_log.exception("Unable to send timeout message in DMs. No big deal tbh.")

        await self.store_remove_at(author.id, role.id, then)
        await self.queue_role_changes()

    async def time_out_at(self, ctx: commands.Context, role_id: int, post: str = ""):
        """Times a user out by parsing command, or (if already timed out) tells them how long the time-out is going
        to last. """
        author = self.TBD.get_member(ctx.author.id)
        if author is None:
            await ctx.message.add_reaction(IDGI)
            return
        if ',' not in post:
            await ctx.reply("Sorry, I can't parse that. Remember to use a ``,`` in your command. Examples which I "
                            "should be able to parse: ``!cwbanmeat X hours, Y hours``, ``!blindmeat tomorrow, "
                            "10 hours``, ``!mutemeat 04.12.22 11:15, 2 days``. Don't use a date for the second command.")
            return

        role = self.TBD.get_role(role_id)
        when, until_when = post.split(sep=',', maxsplit=1)
        when, until_when = when.strip(), until_when.strip()  # _, reminder
        now, then, parse_status = timeywimey.parse_time(when)
        _, until_then, parse_status2 = timeywimey.parse_time(until_when)
        if parse_status == 0 or parse_status2 == 0:
            await ctx.message.add_reaction(IDGI)
            await ctx.reply("Sorry, I can't parse that. Examples which I should be able to parse: ``!cwbanmeat X "
                            "hours, Y hours``, ``!blindmeat tomorrow, 10 hours``, ``!mutemeat 04.12.22 11:15, "
                            "2 days``. Don't use a date for the second command.")
            return

        try:
            await self.store_add_at(author.id, role.id, then)
            await self.store_remove_at(author.id, role.id, until_then + then - now)
            await ctx.reply(f"You'll be timed out from the <t:{then}> until <t:{until_then + then - now}>.")
        except discord.HTTPException:
            bl.error_log.exception("Time out error! Unable to add role to user, most likely.")
            await ctx.message.add_reaction(IDGI)
        await self.queue_role_changes()

    # endregion

    # region HelperFunctions
    async def check_ban_length(self, user_id: int, role_id) -> int:
        # TABLE remove_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT oid, * FROM remove_at
                             WHERE user_id = (?)
                             AND role_id = (?)
                             AND status IN ("Present", "Future")
                             ORDER BY due ASC''',
                          [user_id, role_id])
        row = await cur.fetchone()
        if not row:  # Ban won't be removed automatically
            bl.error_log.error("Permanent ban detected!")
            return 0
        else:
            due = row['due']
            now = timeywimey.right_now()
            if due < now:
                bl.error_log.error("Ban length negative!")
                return 1
            return due - now

    async def store_add_at(self, user_id: int, role_id: int, due: int):
        """Adds a row to table which represents a 'ADD ROLE(role_id) TO USER(user_id) AT due EVENT."""
        # TABLE add_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''INSERT INTO add_at
                             VALUES (?, ?, ?, ?);''',
                          (user_id, role_id, due, 'Future'))
        await self.bot.db.commit()
        return cur.lastrowid

    async def store_remove_at(self, user_id: int, role_id: int, due: int):
        """Adds a row to table which represents a 'REMOVE ROLE(role_id) TO USER(user_id) AT due EVENT."""
        # TABLE remove_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''INSERT INTO remove_at
                             VALUES (?, ?, ?, ?);''',
                          (user_id, role_id, due, 'Future'))
        await self.bot.db.commit()
        return cur.lastrowid

    async def read_add_at(self):
        # TABLE add_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT oid, *
                             FROM add_at WHERE due <= (?)
                             AND status LIKE "Future"''',
                          [int(datetime.datetime.now().timestamp()) + 3600 + 60])
        return await cur.fetchall()

    async def read_remove_at(self):
        # TABLE remove_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)
        cur = await self.bot.db.cursor()
        await cur.execute('''SELECT oid, *
                             FROM remove_at
                             WHERE due <= (?)
                             AND status LIKE "Future"''',
                          [int(datetime.datetime.now().timestamp()) + 3600 + 60])
        return await cur.fetchall()
    # endregion
