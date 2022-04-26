# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Database Functions

import os, sys, json
import MySQLdb

config_txt = ""
if sys.argv[0].endswith("main.py"):
    print("Initializing Database...")
    config_txt = open("./bot.conf","r").read()
elif sys.argv[0].endswith("test.py"):
    print("Initializing Test Database...")
    config_txt = open("./test.conf","r").read()
config = json.loads(config_txt)

host = config["database"]["host"]
user = config["database"]["user"]
passwd = config["database"]["passwd"]
dbname = config["database"]["dbname"]

conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = dbname)
cur = conn.cursor()

# STAFF MANAGEMENT
# administrative staff
cur.execute(f"CREATE TABLE IF NOT EXISTS staffrole (guildid BIGINT, roleid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS staffuser (guildid BIGINT, userid BIGINT)")
# non-administrative staff
cur.execute(f"CREATE TABLE IF NOT EXISTS nastaffrole (guildid BIGINT, roleid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS nastaffuser (guildid BIGINT, userid BIGINT)")

# SERVER MANAGEMENT
cur.execute(f"CREATE TABLE IF NOT EXISTS serverstats (guildid BIGINT, categoryid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS statsconfig (guildid BIGINT, categoryid BIGINT, channelid BIGINT, conf TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS channelbind (guildid BIGINT, category VARCHAR(32), channelid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS eventlog (guildid BIGINT, events TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS vcrecord (guildid BIGINT, minutes BIGINT, laststart BIGINT)") # clear each month
cur.execute(f"CREATE TABLE IF NOT EXISTS translate (guildid BIGINT, channelid BIGINT, fromlang TEXT, tolang TEXT)")

# USER MANAGEMENT
cur.execute(f"CREATE TABLE IF NOT EXISTS level (guildid BIGINT, userid BIGINT, level BIGINT, xp BIGINT, lastmsg BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS levelrole (guildid BIGINT, level BIGINT, roleid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS rankcard (guildid BIGINT, userid BIGINT, bgcolor TEXT, fgcolor TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS reactionrole (guildid BIGINT, channelid BIGINT, msgid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS rolebind (guildid BIGINT, channelid BIGINT, msgid BIGINT, role BIGINT, emoji VARCHAR(64))")
cur.execute(f"CREATE TABLE IF NOT EXISTS userrole (guildid BIGINT, channelid BIGINT, msgid BIGINT, userid BIGINT, roleid BIGINT)")

# BUTTON
cur.execute(f"CREATE TABLE IF NOT EXISTS button (buttonid BIGINT, guildid BIGINT, data TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS buttonview (buttonid BIGINT, customid TEXT)")

# EMBED
cur.execute(f"CREATE TABLE IF NOT EXISTS embed (embedid BIGINT, guildid BIGINT, data TEXT)")    

# CHAT
cur.execute(f"CREATE TABLE IF NOT EXISTS chataction (guildid BIGINT, keywords TEXT, action VARCHAR(64))")

# FORM
cur.execute(f"CREATE TABLE IF NOT EXISTS form (formid BIGINT, guildid BIGINT, data TEXT, callback TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS formentry (formid BIGINT, userid BIGINT, data TEXT)") # record all forms user submitted
cur.execute(f"CREATE TABLE IF NOT EXISTS suggestion (guildid BIGINT, userid BIGINT, messageid BIGINT, subject TEXT, content TEXT, upvote BIGINT, downvote BIGINT)")

# MUSIC
cur.execute(f"CREATE TABLE IF NOT EXISTS playlist (guildid BIGINT, userid BIGINT, title TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS vcbind (guildid BIGINT, channelid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS favourite (userid BIGINT, songs TEXT)")

# FUN HOUSE
cur.execute(f"CREATE TABLE IF NOT EXISTS finance (guildid BIGINT, userid BIGINT, last_checkin BIGINT, checkin_continuity BIGINT, \
    work_claim_time BIGINT, work_reward BIGINT, balance BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS connectfour (gameid BIGINT, red BIGINT, blue BIGINT, \
    guildid BIGINT, chnid BIGINT, msgid BIGINT, bet BIGINT, state TEXT, customid TEXT, lastop BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS connectfour_leaderboard (userid BIGINT, won BIGINT, lost BIGINT, draw BIGINT, earning BIGINT)")

# TRUCKERSMP
cur.execute(f"CREATE TABLE IF NOT EXISTS truckersmp (mpid BIGINT, name TEXT, tmpdata TEXT, lastupd BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS vtc (vtcid BIGINT, name TEXT, tmpdata TEXT, members LONGTEXT, lastupd BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS steam (mpid BIGINT, steamid BIGINT, name TEXT, steamdata TEXT, lastupd BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS tmpbind (mpid BIGINT, discordid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS vtcbind (guildid BIGINT, vtcid BIGINT, name TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS eventping (guildid BIGINT, vtcid BIGINT, channelid BIGINT, msg TEXT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS eventpinged (vtcid BIGINT, eventid BIGINT)")
cur.execute(f"CREATE TABLE IF NOT EXISTS eventcache (vtcid BIGINT, data MEDIUMTEXT, lastupd BIGINT)")

# PREMIUM
cur.execute(f"CREATE TABLE IF NOT EXISTS premium (guildid BIGINT, tier BIGINT, expire BIGINT)")

# GENERAL SETTINGS
cur.execute(f"CREATE TABLE IF NOT EXISTS settings (guildid BIGINT, skey TEXT, sval TEXT)")

cur.execute(f"UPDATE vcrecord SET laststart = 0")
conn.commit()
del cur

def newconn():
    conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = dbname)
    return conn