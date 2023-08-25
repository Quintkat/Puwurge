import database
import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions

from helpers import parseMaxAge, getReadableMaxAge

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
SAFEMODE = os.environ.get('SAFE_MODE', 'false').lower() == 'true'
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

    if SAFEMODE:
        await channel.send(f'SAFEMODE: would have added this channel for future auto purging with max message age of {getReadableMaxAge(maxAge)}')
        return

    # Attempt to add channel to database
    result = database.addChannel(channel.id, maxAge)
    if result == 1:
        await channel.send('sorry, something went wrong :/ please try again (it will probably work this time :3 )')
    else:
        await channel.send(f'oki! Auto purging set up with max message age of {getReadableMaxAge(maxAge)} (the first purge in this channel will be in the next first purge cycle :3 )')


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
        if SAFEMODE:
            print(f'SAFEMODE: Would purge all messages in channel {channelID} before {cutoff} (UTC)')
            continue
        
        print(f'Purging all messages in channel {channelID} before {cutoff} (UTC)')
        try:
            await channel.purge(limit=None, before=cutoff, reason='included in periodic channel purge', oldest_first=True)
        except Exception:
            print(f'Something went wrong while purging in {channelID}, will try again on next cycle')


@client.command()
@has_permissions(manage_messages=True)
async def stopDeletion(ctx):
    """Command to deactivate auto purging in a channel"""
    channel = ctx.channel
    if SAFEMODE:
        await channel.send('SAFEMODE: would have removed this channel from auto purges')
        return

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
            await channel.send(f'This channel auto deletes messages that are more than {getReadableMaxAge(maxAge)} old')
            return
    
    await channel.send(f'This channel does not have auto deletion set up')


TOKEN = os.environ.get('TOKEN')
client.run(TOKEN)
