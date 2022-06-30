import configparser
import discord
from discord.ext import commands
import sqlite3

MODE = 'tbd'

config = configparser.ConfigParser()
config.read('config.ini')
KEY = config['config']['key']

OWNER_ID = int(config['config']['OWNER'])

SERVER_ID = int(config[MODE]['SERVER'])

LOGGER_CHANNEL = int(config[MODE]['LOGGER_CHANNEL'])

BOT_JOINED_AT = float(config['config']['BOT_JOINED_AT'])

CW_BAN_ROLE = int(config[MODE]['CW_BAN_ROLE'])
BLINDED_ROLE = int(config[MODE]['BLINDED_ROLE'])
MUTED_ROLE = int(config[MODE]['MUTED_ROLE'])
MOD_ROLE = int(config[MODE]['MOD_ROLE'])

THREAD_WATCH_CHANNEL_ID = int(config[MODE]['THREAD_WATCH_CHANNEL_ID'])

TESTSERVER_ID = int(config['test']['SERVER'])

BLUE_PORTAL = config['misc']['BLUE_PORTAL']
ORANGE_PORTAL = config['misc']['ORANGE_PORTAL']

# Bot reacts with IDGI if it couldn't parse a command
IDGI = config['misc']['IDGI']
# Bot reacts with NO to message if it doesn't allow something
DENIED = config['misc']['DENIED']
# Owner reacts with XXX to message to delete it. Unnecessary at this point.
XXX = config['misc']['XXX']

# To alert mods
LOUDSPEAKER = config['misc']['LOUDSPEAKER']

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
    con.close()


if __name__ == '__main__':
    print("Initialising databases now! Don't worry, these are IF NOT EXISTS statements.")
    initialise_databases()
else:
    print("Waiting until ready!")
