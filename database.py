from mysql import connector
from dotenv import load_dotenv
import os

if os.path.isfile('.env'):
    load_dotenv()



def getConnection():
    return connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database='s98380_data'
    )


def _addChannel(channelID: int, maxAge: int):
    channels = _getChannels()
    for (channel, _) in channels:
        if channel == channelID:
            _updateChannel(channelID, maxAge)
            return
        
    db = getConnection()
    cursor = db.cursor()

    insertChannel = ("INSERT INTO channels (channel, maxAge) VALUES (%s, %s)")
    cursor.execute(insertChannel, [str(channelID), maxAge])

    db.commit()

    cursor.close()
    db.close()
    print(f'added channel {channelID} to deletion database')


def _updateChannel(channelID: int, maxAge: int):
    db = getConnection()
    cursor = db.cursor()

    updateMaxAge = "UPDATE channels SET maxAge = %s WHERE channel = %s;"
    cursor.execute(updateMaxAge, [maxAge, str(channelID)])

    db.commit()

    cursor.close()
    db.close()
    print(f'updated channel {channelID} in deletion database to have maxAge {maxAge} minutes')


def _deleteChannel(channelID: int):
    db = getConnection()
    cursor = db.cursor()

    removeChannel = ("DELETE FROM channels WHERE channel = %s")
    cursor.execute(removeChannel, [str(channelID)])

    db.commit()

    cursor.close()
    db.close()
    print(f'removed channel {channelID} to deletion database')


def _getChannels() -> list[(int, int)]:
    db = getConnection()
    cursor = db.cursor()

    channels = []
    getAllChannels = ("SELECT channel, maxAge FROM channels")
    cursor.execute(getAllChannels)
    for (channel, maxAge) in cursor:
        channels.append((int(channel), maxAge))

    cursor.close()
    db.close()
    return channels


def addChannel(channelID: int, maxAge: int) -> int:
    try:
        _addChannel(channelID, maxAge)
        return 0
    except Exception:
        return 1


def deleteChannel(channelID: int) -> int:
    try:
        _deleteChannel(channelID)
        return 0
    except Exception:
        return 1


def getChannels() -> list[(int, int)]:
    try:
        return _getChannels()
    except Exception:
        return []