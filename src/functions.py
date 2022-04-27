# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

from time import time, gmtime, strftime
from settings import *
from db import newconn
from bot import bot
from base64 import b64encode, b64decode
import struct
import sys
import urllib.request
import re
import ssl
import discord
import requests
import json
from rapidfuzz import process

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

async def finance_log(text):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [Finance] {text}"
    print(text)
    try:
        channel = bot.get_channel(FINANCE_LOG_CHANNEL[1])
        await channel.send(f"```{text}```")
    except:
        pass   

async def log(func, text, guildid = None):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [{func}] {text}"
    print(text)
    try:
        channel = bot.get_channel(LOG_CHANNEL[1])
        await channel.send(f"```{text}```")
        if not guildid is None:
            conn = newconn()
            cur = conn.cursor()
            cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'botlog'")
            t = cur.fetchall()
            if len(t) > 0:
                chn = t[0][0]
                channel = bot.get_channel(chn)
                await channel.send(f"```{text}```")
    except:
        import traceback
        traceback.print_exc()
        pass

def b64e(s):
    try:
        return b64encode(s.encode()).decode()
    except:
        return s
    
def b64d(s):
    try:
        return b64decode(s.encode()).decode()
    except:
        return s

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

def isAdmin(guild, user):
    if guild.owner.id == user.id:
        return True
    
    for permission in user.guild_permissions:
        if permission[0] == "administrator" and permission[1]:
            return True

    if user.id == BOTOWNER:
        return True
    
    return False

def isStaff(guild, user):
    if isAdmin(guild, user):
        return True
        
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT roleid FROM staffrole WHERE guildid = {guild.id}")
    staffroleids = cur.fetchall()
    for staffroleid in staffroleids:
        for role in user.roles:
            if role.id == staffroleid[0]:
                return True
    
    cur.execute(f"SELECT * FROM staffuser WHERE guildid = {guild.id} AND userid = {user.id}")
    t = cur.fetchall()
    if len(t) > 0:
        return True
        
    return False

def GetCurrentSong(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    encoding = 'latin1' # default: iso-8859-1 for mp3 and utf-8 for ogg streams
    request = urllib.request.Request(url, headers={'Icy-MetaData': 1})  # request metadata
    
    with urllib.request.urlopen(request, context=ctx, timeout = 3) as response:
        metaint = int(response.headers['icy-metaint'])
        for _ in range(10): # # title may be empty initially, try several times
            response.read(metaint)  # skip to metadata
            metadata_length = struct.unpack('B', response.read(1))[0] * 16  # length byte
            metadata = response.read(metadata_length).rstrip(b'\0')
            
            # extract title from the metadata
            m = re.search(br"StreamTitle='([^']*)';", metadata)
            if m:
                title = m.group(1)
                if title:
                    return title.decode()
        else: 
            return -1
    
def CheckVCLock(guildid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM playlist WHERE guildid = {guildid} AND userid = -2")
    t = cur.fetchall()
    if len(t) > 0:
        return True
    return False

def CalcLevel(xp):
    i = 0
    while xp >= 5 / 6 * i * (2 * i * i + 27 * i + 91):
        i += 1
    if i-1 > 100:
        return 100
    return i-1

def CalcXP(i):
    return 5 / 6 * i * (2 * i * i + 27 * i + 91)

def GetPremium(guild):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT tier FROM premium WHERE guildid = {guild.id} AND expire > {int(time())}")
    t = cur.fetchall()
    if len(t) > 0:
        return t[0][0]
    return 0

def CheckPremium(guild, tier):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM premium WHERE guildid = {guild.id} AND tier >= {tier} AND expire > {int(time())}")
    t = cur.fetchall()
    if len(t) > 0:
        return True
    return False

def SearchVoice(inp):
    res = process.extract(inp, VOICES, limit = 10, score_cutoff = 60)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret
    
from libretranslatepy import LibreTranslateAPI
from langdetect import detect as ldetect

config_txt = ""
config_txt = open("./bot.conf","r").read()
config = json.loads(config_txt)
lt = LibreTranslateAPI(config["libretranslate"]["host"])
lt.api_key = config["libretranslate"]["key"]
langs = lt.languages()
name2code = {}
code2name = {}
allcode = []
for lang in langs:
    name2code[lang["name"] + f" ({lang['code']})"] = lang["code"]
    code2name[lang["code"]] = lang["name"] + f" ({lang['code']})"
    allcode.append(lang["code"])

def DetectLang(text):
    t = lt.detect(text)[0]
    if t["confidence"] == 0.0: # libretranslate failed
        fromlang = ldetect(text)
        if fromlang in allcode:
            return fromlang
        else:
            return "en"
    fromlang = t["language"]
    return fromlang

def Translate(text, tolang = "en", fromlang = None):
    if fromlang == None:
        fromlang = DetectLang(text)
    if fromlang == tolang:
        return (f"*I think this is already in the target language.*\n{text}", fromlang, tolang)
    if fromlang == "en" or tolang == "en":
        totext = lt.translate(text, fromlang, tolang)
        if totext.lower() == text.lower():
            return None
        return (totext, fromlang, tolang)
    entext = lt.translate(text, fromlang, "en")
    totext = lt.translate(entext, "en", tolang)
    if totext.lower() == text.lower():
        return None
    return (totext, fromlang, tolang)