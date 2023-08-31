import configparser
from discord.ext import commands

config = configparser.ConfigParser()
config.read("config.ini")

KEY = config["config"]["key"]

DB_LOCATION = config["config"]["db_location"]
BACKUPS_LOCATION = config["config"]["backups_location"]

# Load cogs configuration
LOAD_REMINDERS = config.getboolean("cogs", "reminders", fallback=False)
LOAD_COUNTER = config.getboolean("cogs", "counter", fallback=False)
LOAD_FIXTWITTER = config.getboolean("cogs", "fixtwitter", fallback=False)
LOAD_YUD = config.getboolean("cogs", "yud", fallback=False)
LOAD_PART = config.getboolean("cogs", "part", fallback=False)
LOAD_OWNERTOOLS = config.getboolean("cogs", "ownertools", fallback=True)
LOAD_TBDTOOLS = config.getboolean("cogs", "tbdtools", fallback=False)

# TBD-specific
TBD_GUILD = int(config["tbd"]["TBD_GUILD"])
CW_CHANNEL = int(config["tbd"]["CW_CHANNEL"])
THREAD_WATCH_CHANNEL = int(config["tbd"]["THREAD_WATCH_CHANNEL"])
BLINDED_ROLE = int(config["tbd"]["BLINDED_ROLE"])

# Miscellaneous stuff, emoji and pictures. Nothing sensitive
config = configparser.ConfigParser()
config.read("symbols.ini")

BLUE_PORTAL = config["misc"]["BLUE_PORTAL"]
ORANGE_PORTAL = config["misc"]["ORANGE_PORTAL"]

# Bot reacts with IDGI if it couldn't parse a command
IDGI = config["misc"]["IDGI"]
# Bot reacts with NO to message if it doesn't allow something
DENIED = config["misc"]["DENIED"]
# Delete a post the bot made
DELETE = config["misc"]["DELETE"]

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
