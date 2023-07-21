import database
import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import os

# Either load the env vars from a local env file (when testing stuff locally) or it's already been loaded (running on server)
if os.path.isfile('.env'):
    load_dotenv()
    print('Loading environment variables from .env file')
else:
    print('Loading environment variables from server variables')


# Safe mode allows you to run the bot and test stuff, without having actual results on the database or existing messages
SAFEMODE = os.environ.get('SAFE_MODE', False).lower() == 'true'
if SAFEMODE:
    print('Safe mode is on')


# Boilerplate
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='~~', intents=intents)


@client.event
async def on_ready():
    delete.start()


@client.command()
@has_permissions(manage_messages=True)
async def deleteHere(ctx):
    """Command to activate auto purging in a channel

    Also used to update the max age of messages in the channel if the channel is already registered.
    The default max age is 7 days, if it's left out in the command message.
    Syntax: ~~deleteHere (<max age>[m, h, d])
    """
    channel = ctx.channel
    
    # Check if max age can be parsed
    maxAge = parseMaxAge(ctx.message.content)
    if maxAge == -1:
        await channel.send('can\'t recognise that time format, please enter it in days, hours, or minutes with for example `5d`, `12h`, or `10m`')
        return

    # Attempt to add channel to database
    result = database.addChannel(channel.id, maxAge)
    if result == 1:
        await channel.send('sorry, something went wrong :/ please try again (it will probably work this time :3 )')
    else:
        await channel.send('oki! (the first purge at this max age will be in the next first purge cycle :3 )')


def parseMaxAge(message: str) -> int:
    """Returns the max age that was sent alongside the message in minutes
    
    If the max age could not be parsed, it returns -1
    """
    hoursPerDay = 24
    minutesPerHour = 60
    default = 7*hoursPerDay*minutesPerHour
    split = message.split(' ')

    if len(split) == 1:
        return default
    elif len(split) == 2:
        time = split[1]     # Would be like '5d'
        try:
            amount = int(time[0:-1])        # Would be like 5
            identifier = time[-1].lower()   # Would be like 'd'
            match identifier:
                case 'd':
                    return amount*hoursPerDay*minutesPerHour
                
                case 'h':
                    return amount*minutesPerHour

                case 'm':
                    return amount
                
                case _:
                    return -1
        except Exception:
            return -1
    else:
        return -1


@deleteHere.error
async def deleteHereError(ctx, error):
    """Handles missing permissions"""
    if isinstance(error, MissingPermissions):
        await ctx.send('grrr only people with `manage_messages` permissions can do this')


@tasks.loop(minutes=1.0)
async def delete():
    """The task that runs on a loop that auto purges the message"""
    now = datetime.now(tz=timezone.utc)
    for (channelID, maxAge) in database.getChannels():
        cutoff = now - timedelta(minutes=maxAge)
        channel = client.get_channel(channelID)
        
        print(f'Purging all messages in channel {channelID} before {cutoff} (UTC)')
        await channel.purge(limit=None, before=cutoff, reason='included in periodic channel purge', oldest_first=True)


@client.command()
@has_permissions(manage_messages=True)
async def stopDeletion(ctx):
    """Command to deactivate auto purging in a channel"""
    channel = ctx.channel
    result = database.deleteChannel(channel.id)
    if result == 1:
        await channel.send('sorry, something went wrong :/ please try again (it will probably work this time :3 )')
    else:
        await channel.send('oki! the channel won\'t be included in auto purges anymore :3')


@stopDeletion.error
async def stopDeletionError(ctx, error):
    """Handles missing permissions"""
    if isinstance(error, MissingPermissions):
        await ctx.send('grrr only people with `manage_messages` permissions can do this')


@client.command()
async def info(ctx):
    """Command to get info about the auto purging status of a channel
    
    Shows the max message age
    """
    channel = ctx.channel
    channels = database.getChannels()
    
    # Find the channel if possible
    for (channelID, maxAge) in channels:
        if channelID == channel.id:
            if (maxAge/24)/60 == (maxAge//24)//60:
                await channel.send(f'This channel auto deletes messages that are more than {maxAge//24//60} days old')
            elif maxAge/60 == maxAge//60:
                await channel.send(f'This channel auto deletes messages that are more than {maxAge//60} hours old')
            else:
                await channel.send(f'This channel auto deletes messages that are more than {maxAge} minutes old')
            return
    
    await channel.send(f'This channel does not have auto deletion set up')


TOKEN = os.environ.get('TOKEN')
client.run(TOKEN)
