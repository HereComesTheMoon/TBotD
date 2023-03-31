import configparser
import discord
from discord.ext import commands
import sqlite3

# Two modes: 'tbd' and 'test'. 'test' should not be used anymore.
MODE = 'tbd'

config = configparser.ConfigParser()
config.read('config.ini')


KEY = config['config']['key']
OWNER_ID = int(config['config']['OWNER'])

BOT_JOINED_AT = float(config['config']['BOT_JOINED_AT'])


SERVER_ID = int(config[MODE]['SERVER'])

THREAD_WATCH_CHANNEL = int(config[MODE]['THREAD_WATCH_CHANNEL'])
LOGGER_CHANNEL = int(config[MODE]['LOGGER_CHANNEL'])
BOT_CHANNEL = int(config[MODE]['BOT_CHANNEL'])

CW_BAN_ROLE = int(config[MODE]['CW_BAN_ROLE'])
BLINDED_ROLE = int(config[MODE]['BLINDED_ROLE'])
MUTED_ROLE = int(config[MODE]['MUTED_ROLE'])
MOD_ROLE = int(config[MODE]['MOD_ROLE'])


# TESTSERVER_ID = int(config['test']['SERVER'])


# Miscellaneous stuff, emoji and pictures. Nothing sensitive
config = configparser.ConfigParser()
config.read('symbols.ini')

BLUE_PORTAL = config['misc']['BLUE_PORTAL']
ORANGE_PORTAL = config['misc']['ORANGE_PORTAL']

# Bot reacts with IDGI if it couldn't parse a command
IDGI = config['misc']['IDGI']
# Bot reacts with NO to message if it doesn't allow something
DENIED = config['misc']['DENIED']

# To alert mods
LOUDSPEAKER = config['misc']['LOUDSPEAKER']

# 'fun':
FLUSHED = config['misc']['FLUSHED']
WAVE = config['misc']['WAVE']
CONFOUNDED = config['misc']['CONFOUNDED']
WOOZY = config['misc']['WOOZY']
CATHEARTS = config['misc']['CATHEARTS']
CATPOUT = config['misc']['CATPOUT']
RAT = config['misc']['RAT']
PLEADING = config['misc']['PLEADING']
CATSCREAM = config['misc']['CATSCREAM']


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID

    return commands.check(predicate)


def on_tbd(msg: discord.Message) -> bool:
    guild = msg.guild
    if guild:
        return msg.guild.id == SERVER_ID
    return False

def in_bot_channel(msg: discord.Message) -> bool:
    guild = msg.guild
    if guild: # breaks if on not-TBD server, like everything else
        return msg.channel.id == BOT_CHANNEL
    return False

def in_dms(msg: discord.Message) -> bool:
    return isinstance(msg.channel, discord.channel.DMChannel)
        

def initialise_databases():
    with sqlite3.connect('db.db') as con:
        cur = con.cursor()
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       memories (userID INTEGER, postID INTEGER, postUrl TEXT, reminder TEXT, queryMade INT, queryDue INT, status TEXT);''')
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       remove_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)''')
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       add_at (user_id INTEGER, role_id INTEGER, due INTEGER, status TEXT)''')
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       emojis_default (name TEXT, uses INT)''')
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       emojis_custom (emoji_id INTEGER, name TEXT, url TEXT, uses INT)''')
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       suggestions (date INT, userID INT, postID INT, t TEXT, b TEXT, d TEXT)''')
        cur.execute('''CREATE TABLE 
                       IF NOT EXISTS 
                       used_titles (date INT, t TEXT, b TEXT, d TEXT)''')
        cur.execute('''CREATE TABLE
                       IF NOT EXISTS
                       yud_called (date INT, userID INT)''')
        cur.execute('''CREATE TABLE
                       IF NOT EXISTS
                       yud_reminder (date_due INT, userID INT)''')
    con.close()


if __name__ == '__main__':
    print("Initialising databases now! Don't worry, these are IF NOT EXISTS statements.")
    initialise_databases()
else:
    print("Waiting until ready!")
