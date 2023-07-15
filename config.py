import configparser
from aiosqlite import connect, Connection
import discord
from discord.ext import commands
import os

# Two modes: 'tbd' and 'test'. 'test' should not be used anymore.
MODE = "tbd"

config = configparser.ConfigParser()
config.read("config.ini")


KEY = config["config"]["key"]

BOT_JOINED_AT = float(config["config"]["BOT_JOINED_AT"])


SERVER_ID = int(config[MODE]["SERVER"])

THREAD_WATCH_CHANNEL = int(config[MODE]["THREAD_WATCH_CHANNEL"])
LOGGER_CHANNEL = int(config[MODE]["LOGGER_CHANNEL"])
BOT_CHANNEL = int(config[MODE]["BOT_CHANNEL"])

CW_BAN_ROLE = int(config[MODE]["CW_BAN_ROLE"])
BLINDED_ROLE = int(config[MODE]["BLINDED_ROLE"])
MUTED_ROLE = int(config[MODE]["MUTED_ROLE"])
MOD_ROLE = int(config[MODE]["MOD_ROLE"])

# Load cogs configuration
LOAD_REMINDERS = config.getboolean("cogs", "reminders", fallback=False)
LOAD_DB = config.getboolean("cogs", "db", fallback=False)
LOAD_TEMPROLES = config.getboolean("cogs", "temproles", fallback=False)
LOAD_THREADWATCH = config.getboolean("cogs", "threadwatch", fallback=False)
LOAD_FIXTWITTER = config.getboolean("cogs", "fixtwitter", fallback=False)
LOAD_YUD = config.getboolean("cogs", "yud", fallback=False)
LOAD_PART = config.getboolean("cogs", "part", fallback=False)
LOAD_MODERATION = config.getboolean("cogs", "moderation", fallback=False)
LOAD_OWNERTOOLS = config.getboolean("cogs", "ownertools", fallback=False)


# TESTSERVER_ID = int(config['test']['SERVER'])


# Miscellaneous stuff, emoji and pictures. Nothing sensitive
config = configparser.ConfigParser()
config.read("symbols.ini")

BLUE_PORTAL = config["misc"]["BLUE_PORTAL"]
ORANGE_PORTAL = config["misc"]["ORANGE_PORTAL"]

# Bot reacts with IDGI if it couldn't parse a command
IDGI = config["misc"]["IDGI"]
# Bot reacts with NO to message if it doesn't allow something
DENIED = config["misc"]["DENIED"]

# To alert mods
LOUDSPEAKER = config["misc"]["LOUDSPEAKER"]

# 'fun':
FLUSHED = config["misc"]["FLUSHED"]
WAVE = config["misc"]["WAVE"]
CONFOUNDED = config["misc"]["CONFOUNDED"]
WOOZY = config["misc"]["WOOZY"]
CATHEARTS = config["misc"]["CATHEARTS"]
CATPOUT = config["misc"]["CATPOUT"]
RAT = config["misc"]["RAT"]
PLEADING = config["misc"]["PLEADING"]
CATSCREAM = config["misc"]["CATSCREAM"]


def on_tbd():
    async def predicate(ctx):
        guild = ctx.guild
        if guild:
            return ctx.guild.id == SERVER_ID
        return False

    return commands.check(predicate)


def in_bot_channel():
    def predicate(ctx) -> bool:
        guild = ctx.guild
        if guild:
            # breaks if on not-TBD server, like everything else
            return ctx.channel.id == BOT_CHANNEL
        return False

    return commands.check(predicate)


def in_dms(msg: discord.Message) -> bool:
    return isinstance(msg.channel, discord.channel.DMChannel)


async def initialise_database(location: str) -> Connection:
    if os.path.isfile(location):
        return await connect(location)

    con = await connect(location)
    async with con.cursor() as cur:
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             memories (userID INTEGER, postID INTEGER, postUrl TEXT, reminder TEXT, queryMade INT, queryDue INT, status TEXT);"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             remove_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             add_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             emojis_default (name TEXT, uses INT)"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             emojis_custom (emoji_id INTEGER, name TEXT, url TEXT, uses INT)"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             suggestions (date INT, userID INT, postID INT, t TEXT, b TEXT, d TEXT)"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             used_titles (date INT, t TEXT, b TEXT, d TEXT)"""
        )
        await cur.execute(
            """CREATE TABLE
                             IF NOT EXISTS
                             yuds (date INT, userID INT, postID INT, width INT, height INT, quality INT)"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             yudminders (userID INT, due INT);"""
        )
        await cur.execute(
            """CREATE TABLE 
                             IF NOT EXISTS 
                             part (userID INT, guildID INT, channelID INT, due INT, status TEXT);"""
        )
    return con
