import database
import discord
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, MissingPermissions
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import os

if os.path.isfile('.env'):
    load_dotenv()
    print('Loading environment variables from .env file')
else:
    print('Loading environment variables from server variables')



intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='~~', intents=intents)


@client.event
async def on_ready():
    # delete.start()
    pass


@client.command()
@has_permissions(manage_messages=True)
async def deleteHere(ctx):
    channel = ctx.channel
    maxAge = parseMaxAge(ctx.message.content)
    if maxAge == -1:
        await channel.send('can\'t recognise that time format, please enter it in days, hours, or minutes with for example `5d`, `12h`, or `10m`')
        return

    try:
        database.addChannel(channel.id, maxAge)
        await channel.send('oki!')
        await delete()
    except:
        await channel.send('something probably went wrong with the database connection, contact Anna :3')


# Returns the max age that was sent alongside the message in minutes
def parseMaxAge(message: str) -> int:
    hoursPerDay = 24
    minutesPerHour = 60
    default = 7*hoursPerDay*minutesPerHour
    split = message.split(' ')

    if len(split) == 1:
        return default
    elif len(split) == 2:
        time = split[1]
        try:
            amount = int(time[0:-1])
            identifier = time[-1].lower()
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
    if isinstance(error, MissingPermissions):
        await ctx.send('grrr only people with `manage_messages` permissions can set this')


@tasks.loop(minutes=1.0)
async def delete():
    now = datetime.now(tz=timezone.utc)
    for (channelID, maxAge) in database.getChannels():
        cutoff = now - timedelta(minutes=maxAge)
        channel = client.get_channel(channelID)
        print(f'Purging all messages in channel {channelID} before {cutoff} (UTC)')
        await channel.purge(limit=None, before=cutoff, reason='included in periodic channel purge', oldest_first=True)


@client.command()
@has_permissions(manage_messages=True)
async def stopDeletion(ctx):
    channel = ctx.channel
    database.deleteChannel(channel.id)
    await channel.send('oki!')


@stopDeletion.error
async def stopDeletionError(ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send('grrr only people with `manage_messages` permissions can set this')


@client.command()
async def info(ctx):
    channel = ctx.channel
    channels = database.getChannels()
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
