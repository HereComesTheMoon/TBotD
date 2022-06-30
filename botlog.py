import logging
from discord.ext import commands
import timeywimey

# This handles custom logging messages.
# This handler logs called commands.
# There's the issue of handling sensitive data when people use !remindme, but I need to store the reminders anyway,
# so there is no way around that.

command_log = logging.getLogger('command_log')
command_log.setLevel(logging.INFO)
command_log_handler = logging.FileHandler(filename='./logs/commands.log', mode='a')
# command_log_handler.setLevel(logging.INFO)
command_log_handler.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(message)s',
                                                   datefmt='%d/%m/%Y, %H:%M:%S'))
command_log.addHandler(command_log_handler)

# Log custom errors!
error_log = logging.getLogger('error_log')
error_log.setLevel(logging.WARNING)
error_log_handler = logging.FileHandler(filename='./logs/errors.log', mode='a')
error_log_handler.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(message)s',
                                                 datefmt='%d/%m/%Y, %H:%M:%S'))
error_log.addHandler(error_log_handler)

joinleave_log = logging.getLogger('joinleave_log')
joinleave_log.setLevel(logging.WARNING)
joinleave_log_handler = logging.FileHandler(filename='./logs/joinleave.log', mode='a')
joinleave_log_handler.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(message)s',
                                                 datefmt='%d/%m/%Y, %H:%M:%S'))
joinleave_log.addHandler(joinleave_log_handler)


def log(fun: commands.command, ctx: commands.Context):
    command_log.info(f"{fun.name} called by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id}) "
                     f"in '{ctx.channel}' with text: {ctx.message.clean_content}")


def notification_triggered(p: tuple):
    cnow = timeywimey.right_now()
    command_log.info(f"Reminder triggered at {cnow}: {p}")

# discord.py logs errors and debug information via the logging python module. It is strongly recommended that the
# logging module is configured, as no errors or warnings will be output if it is not set up.
# Default setup:
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='./logs/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s',
                                       datefmt='%d/%m/%Y, %H:%M:%S'))
logger.addHandler(handler)
