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


def getReadableMaxAge(minutes: int) -> str:
    """Returns a human readable conversion of minutes to days or hours or minutes"""
    if minutes/24/60 == minutes//24//60:
        return f'{minutes//24//60} days'
    elif minutes/60 == minutes//60:
        return f'{minutes//60} hours'
    else:
        return f'{minutes} minutes'