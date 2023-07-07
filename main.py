import discord
from discord.ext import commands

import fixtwitter
import moderation
import threadwatch
import ownertools
import yud
import part
from config import SERVER_ID, LOGGER_CHANNEL, IDGI, ORANGE_PORTAL, BLUE_PORTAL, DENIED, KEY
from config import FLUSHED, WAVE, CONFOUNDED, WOOZY, CATHEARTS, CATPOUT, RAT, PLEADING
import random
import re
import time
import aiosqlite

import db
import temproles
import timeywimey
import reminders
import botlog as bl

# Intents
intents = discord.Intents.all()
# Status
activity = discord.Activity(type=discord.ActivityType.listening, name="Poasting! Type '!help' for commands.")
TBotD = commands.Bot(command_prefix='!',
                     activity=activity,
                     intents=intents,
                     status=discord.Status.online)

# General issues with the code:
# The way config.ini imports are handled is inconsistent

@TBotD.event
async def on_ready():
    print("Ready!")
    print(time.strftime("%b %d %Y %H:%M:%S", time.localtime()))
    # Global bot variables. Careful, might overwrite stuff, can be used everywhere.
    connection: aiosqlite.Connection = await aiosqlite.connect("db.db")

    connection.row_factory = aiosqlite.Row

    tbd = TBotD.get_guild(SERVER_ID)
    assert tbd is not None

    # Cogs:
    # !remindme
    await TBotD.add_cog(reminders.Reminders(TBotD, connection))
    # Store "TBD" title suggestions, and used emoji status (for no real reason)
    await TBotD.add_cog(db.Database(TBotD, connection))
    # !cwbanme and related commands
    await TBotD.add_cog(temproles.RoleManagement(TBotD, tbd, connection))
    # Post a comment when a new thread is created. TODO: Should be reworked at some point.
    await TBotD.add_cog(threadwatch.ThreadWatch(TBotD))
    # "Fixes" Twitter links. Relies on vxtwitter.
    await TBotD.add_cog(fixtwitter.FixTwitter(TBotD))
    # Posts Yud
    await TBotD.add_cog(yud.Yud(TBotD, connection))
    # !part command
    await TBotD.add_cog(part.Part(TBotD, tbd, connection))
    # Calls the mods when a :loudspeaker: react is added
    logger_channel = await TBotD.fetch_channel(LOGGER_CHANNEL)
    if isinstance(logger_channel, discord.TextChannel):
        await TBotD.add_cog(moderation.Moderation(TBotD, logger_channel))
    else:
        bl.error_log.error("logger_channel is not a TextChannel. Unable to load Cog.")
    # Owner tools, to kill the bot and to puppet it
    await TBotD.add_cog(ownertools.OwnerTools(TBotD, connection, tbd, timeywimey.right_now()))



@TBotD.command()
async def roll(ctx, *, dice: str = '1d2'):
    """Example: !roll 2d6"""
    bl.log(roll, ctx)
    p = re.compile(r'\dd\d{1,7}', re.IGNORECASE)
    temp = p.match(dice)
    if temp is None:
        await ctx.message.add_reaction(IDGI)
        return
    dice = temp.group()
    k, n = map(int, dice.split('d'))
    rolls = [random.randint(1, n) for i in range(k)]
    output = f"{ctx.author.name} rolls {k}d{n}: " + ", ".join(map(str, rolls))
    if k > 1:
        output += f" for a total of {sum(rolls)}."
    await ctx.channel.send(output)


@TBotD.command()
async def choose(ctx, *, post: str = ""):
    """Example: !choose Big Yud, small yud, wide yud"""
    bl.log(choose, ctx)
    choices = post.split(',')
    if len(choices) <= 1:
        await ctx.message.add_reaction(IDGI)
    else:
        await ctx.channel.send(f"{random.choice(choices)}!", reference=ctx.message)


@TBotD.command()
async def now(ctx):
    """What time is it?"""
    bl.log(now, ctx)
    cnow = timeywimey.right_now()
    await ctx.channel.send(f"It is {timeywimey.epoch2iso(cnow)} in bot time! "
                           f"It is <t:{cnow}> in your timezone! Unix time: {cnow}")


@TBotD.command()
async def ping(ctx, *, _: str = ""):
    """Pong!"""
    bl.log(ping, ctx)
    await ctx.channel.send("Pong!")


@TBotD.command(aliases=['teleport'])
async def portal(ctx: commands.Context, *, arg: str = ""):
    """Create a portal to facilitate inter-channel travel. eg. !portal #silly funny doge."""
    bl.log(portal, ctx)

    if ctx.guild is None:
        await ctx.message.add_reaction(IDGI)
        return

    if not ctx.message.raw_channel_mentions:
        await ctx.message.add_reaction(IDGI)
        return

    channel = ctx.guild.get_channel_or_thread(ctx.message.raw_channel_mentions[0])
    if not isinstance(channel, discord.TextChannel):
        await ctx.message.add_reaction(IDGI)
        return

    what = arg.split(maxsplit=1)
    if len(what) == 2:
        what = what[1]
    else:
        what = ""
    try:
        # Post target portal
        embed = discord.Embed(title=f"Portal from #{ctx.channel}",
                              color=0xe01b24,
                              url=ctx.message.jump_url,
                              description=what)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ORANGE_PORTAL)
        target_msg = await channel.send(content=ctx.message.jump_url, embed=embed)

        # Post origin portal
        embed = discord.Embed(title=f"Portal to #{channel}",
                              color=0xe01b24,
                              url=target_msg.jump_url,
                              description=what)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=BLUE_PORTAL)
        await ctx.channel.send(content=target_msg.jump_url, embed=embed)

        # Edit target portal to correctly link to origin portal
        embed = discord.Embed(title=f"Portal from #{ctx.channel}",
                              color=0xe01b24,
                              url=ctx.message.jump_url,
                              description=what)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=ORANGE_PORTAL)
        await target_msg.edit(content=ctx.message.jump_url, embed=embed)

    except discord.errors.Forbidden:
        await ctx.message.add_reaction(DENIED)
        bl.error_log.exception("Incapable of posting portal in that channel.")
    except discord.errors.HTTPException:
        await ctx.message.add_reaction(DENIED)
        bl.error_log.exception("HTTPException, should not happen.")


@TBotD.command(hidden=True)
async def bottle(ctx: commands.Context):
    """This is deprecated for the time being! Use !choose instead."""
    bl.log(bottle, ctx)
    await ctx.reply("The !bottle command is now called !choose. Use that instead.")


@TBotD.command()
async def when(ctx: commands.Context, *, post: str = ""):
    """Parse a date!"""
    bl.log(when, ctx)
    now, then, parse_status = timeywimey.parse_time(post)
    if not parse_status:
        await ctx.reply("Sorry, I was unable to parse this message.")
        return
    content = f"I parse this as <t:{then}:F>, ie. <t:{then}:R>. This is ``{then}`` in Unix time. Relative timestamps: \n"
    formats = [':t', ':T', ':d', ':D', '', ':F', ':R']
    content += "".join([f"Type ``<t:{then}{flag}>`` to write <t:{then}{flag}>.\n" for flag in formats])
    await ctx.reply(content=content)


@TBotD.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return
    assert TBotD.user is not None
    if TBotD.user.mentioned_in(msg):
        await msg.add_reaction(random.choice([FLUSHED, WAVE, CONFOUNDED, WOOZY, CATHEARTS, CATPOUT, RAT, PLEADING]))
    await TBotD.process_commands(msg)


@TBotD.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    # Handle common errors using match case
    match type(error):
        case commands.MissingRequiredArgument():
            await ctx.message.add_reaction(IDGI)
        case commands.BadArgument():
            await ctx.message.add_reaction(IDGI)
        case commands.CommandOnCooldown(cooldown):
            await ctx.send(
                f"You're using this command too fast. Try again in {cooldown.retry_after:.2f} seconds."
            )
        case commands.MissingPermissions():
            await ctx.message.add_reaction(DENIED)
        case commands.BotMissingPermissions():
            await ctx.message.add_reaction(DENIED)
        case commands.NotOwner():
            await ctx.message.add_reaction(DENIED)
        case _:
            # For all other exceptions, log the error
            bl.error_log.exception(
                f"on_command_error : {error} : {ctx.message.content}"
            )
            await ctx.message.add_reaction(DENIED)


if __name__ == '__main__':
    TBotD.run(KEY)
