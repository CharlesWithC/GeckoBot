# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions of Gecko Bot

from time import time, gmtime, strftime

def TimeDelta(timestamp): # returns human-readable delta
    delta = abs(time() - timestamp)
    if delta <= 1:
        return f"{round(delta, 3)} second"
    elif delta < 60:
        return f"{round(delta, 3)} seconds"
    else:
        if delta / 60 == 1:
            return f"1 minute"
        else:
            return f"{int(delta/60)} minutes"    

async def log(func, text):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [{func}] {text}"
    print(text)
    try:
        channel = bot.get_channel(LOG_CHANNEL[1])
        await channel.send(f"```{text}```")
    except:
        pass

def validateStrftime(s):
    try:
        strftime(s, gmtime())
        return True
    except:
        return False

def betterStrftime(s):
    t = gmtime()
    day = strftime('%-d', t)
    if day == "1" or day == "21" or day == "31":
        day = "st"
    elif day == "2" or day == "22":
        day = "nd"
    elif day == "3" or day == "23":
        day = "rd"
    else:
        day = "th"
    s = s.replace("%-d", "%-d" + day)
    ret = strftime(s, t)
    return ret