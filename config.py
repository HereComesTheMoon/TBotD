import configparser
import discord
from discord.ext import commands

config = configparser.ConfigParser()
config.read("config.ini")

DB_LOCATION = config["config"]["db_location"]
BACKUPS_LOCATION = config["config"]["backups_location"]

KEY = config["config"]["key"]

SERVER_ID = int(config["tbd"]["SERVER"])

THREAD_WATCH_CHANNEL = int(config["tbd"]["THREAD_WATCH_CHANNEL"])
LOGGER_CHANNEL = int(config["tbd"]["LOGGER_CHANNEL"])
BOT_CHANNEL = int(config["tbd"]["BOT_CHANNEL"])

CW_BAN_ROLE = int(config["tbd"]["CW_BAN_ROLE"])
BLINDED_ROLE = int(config["tbd"]["BLINDED_ROLE"])
MUTED_ROLE = int(config["tbd"]["MUTED_ROLE"])
MOD_ROLE = int(config["tbd"]["MOD_ROLE"])

# Load cogs configuration
LOAD_REMINDERS = config.getboolean("cogs", "reminders", fallback=False)
LOAD_EMOJICOUNT = config.getboolean("cogs", "emojicount", fallback=False)
LOAD_TEMPROLES = config.getboolean("cogs", "temproles", fallback=False)
LOAD_THREADWATCH = config.getboolean("cogs", "threadwatch", fallback=False)
LOAD_FIXTWITTER = config.getboolean("cogs", "fixtwitter", fallback=False)
LOAD_YUD = config.getboolean("cogs", "yud", fallback=False)
LOAD_PART = config.getboolean("cogs", "part", fallback=False)
LOAD_MODERATION = config.getboolean("cogs", "moderation", fallback=False)
LOAD_OWNERTOOLS = config.getboolean("cogs", "ownertools", fallback=False)
LOAD_TBDTOOLS = config.getboolean("cogs", "tbdtools", fallback=False)


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
