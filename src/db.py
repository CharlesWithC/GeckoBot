# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Database Functions of Gecko Bot

import os, json
import MySQLdb

config_txt = open("./db.conf","r").read()
config = json.loads(config_txt)

host = config["host"]
user = config["user"]
passwd = config["passwd"]
dbname = config["dbname"]

conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = dbname)
cur = conn.cursor()
cur.execute(f"SHOW TABLES")
if len(cur.fetchall()) != 13:
    # STAFF MANAGEMENT
    # administrative staff
    cur.execute(f"CREATE TABLE staffrole (guildid BIGINT, roleid BIGINT)")
    cur.execute(f"CREATE TABLE staffuser (guildid BIGINT, userid BIGINT)")
    # non-administrative staff
    cur.execute(f"CREATE TABLE nastaffrole (guildid BIGINT, roleid BIGINT)")
    cur.execute(f"CREATE TABLE nastaffuser (guildid BIGINT, userid BIGINT)")
    
    # SERVER MANAGEMENT
    cur.execute(f"CREATE TABLE serverstats (guildid BIGINT, categoryid BIGINT)")
    cur.execute(f"CREATE TABLE statsconfig (guildid BIGINT, categoryid BIGINT, channelid BIGINT, conf TEXT)")
    cur.execute(f"CREATE TABLE channelbind (guildid BIGINT, category VARCHAR(32), channelid BIGINT)")

    # USER MANAGEMENT
    cur.execute(f"CREATE TABLE reactionrole (guildid BIGINT, channelid BIGINT, msgid BIGINT)")
    cur.execute(f"CREATE TABLE rolebind (guildid BIGINT, channelid BIGINT, msgid BIGINT, role BIGINT, emoji VARCHAR(64))")
    cur.execute(f"CREATE TABLE userrole (guildid BIGINT, channelid BIGINT, msgid BIGINT, userid BIGINT, roleid BIGINT)")

    # MUSIC
    cur.execute(f"CREATE TABLE playlist (guildid BIGINT, userid BIGINT, title TEXT)")
    cur.execute(f"CREATE TABLE vcbind (guildid BIGINT, channelid BIGINT)")

    # FUN HOUSE
    cur.execute(f"CREATE TABLE finance (guildid BIGINT, userid BIGINT, last_checkin BIGINT, checkin_continuity BIGINT, \
        work_claim_time BIGINT, work_reward BIGINT, balance BIGINT)")
del cur

def newconn():
    conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = dbname)
    return conn