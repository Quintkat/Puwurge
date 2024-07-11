from mysql import connector
from dotenv import load_dotenv
import os

if os.path.isfile('.env'):
    load_dotenv()



def getConnection():
    """Returns a standard database connection"""
    return connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database='s98380_data'
    )


def _addChannel(channelID: int, maxAge: int):
    """Connects to the database and adds the channel and its max message age to it"""

    # First check if the channel is already in the database, in which case its max message age needs to be updated
    channels = _getChannels()
    for (channel, _) in channels:
        if channel == channelID:
            _updateChannel(channelID, maxAge)
            return
    
    # Otherwise insert it into the database
    db = getConnection()
    cursor = db.cursor()

    insertChannel = ("INSERT INTO channels (channel, maxAge) VALUES (%s, %s)")
    cursor.execute(insertChannel, [str(channelID), maxAge])

    db.commit()

    cursor.close()
    db.close()
    print(f'added channel {channelID} to deletion database with maxAge {maxAge} minutes')


def _updateChannel(channelID: int, maxAge: int):
    """Connects to the database and updates the max message age of a channel"""
    db = getConnection()
    cursor = db.cursor()

    updateMaxAge = "UPDATE channels SET maxAge = %s WHERE channel = %s;"
    cursor.execute(updateMaxAge, [maxAge, str(channelID)])

    db.commit()

    cursor.close()
    db.close()
    print(f'updated channel {channelID} in deletion database to have maxAge {maxAge} minutes')


def _deleteChannel(channelID: int):
    """Connects to the database and removes a channel from it"""
    db = getConnection()
    cursor = db.cursor()

    removeChannel = ("DELETE FROM channels WHERE channel = %s")
    cursor.execute(removeChannel, [str(channelID)])

    db.commit()

    cursor.close()
    db.close()
    print(f'removed channel {channelID} to deletion database')


def _getChannels() -> list[(int, int)]:
    """Connects to the database and fetches the channels and their max age"""
    print("_getChannels.start")
    db = getConnection()
    print("database connection", db)
    cursor = db.cursor()
    print("cursor", cursor)

    channels = []
    getAllChannels = ("SELECT channel, maxAge FROM channels")
    cursor.execute(getAllChannels)
    for (channel, maxAge) in cursor:
        channels.append((int(channel), maxAge))

    cursor.close()
    db.close()
    return channels


###
# The following functions are here, since the database connection raises an exception sometimes and crashes the bot if uncaught
###

def addChannel(channelID: int, maxAge: int) -> int:
    """Adds a channel and its max message age to the database for auto purging"""
    try:
        _addChannel(channelID, maxAge)
        return 0
    except Exception:
        return 1


def deleteChannel(channelID: int) -> int:
    """Removes a channel from the database. This stops it being auto purged"""
    try:
        _deleteChannel(channelID)
        return 0
    except Exception:
        return 1


def getChannels() -> list[(int, int)]:
    """Gets all channels in the database, alongside their max message age"""
    print("getChannels.start")
    try:
        return _getChannels()
    except Exception:
        return []