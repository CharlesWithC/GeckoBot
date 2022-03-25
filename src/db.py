# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Database Functions of Gecko Bot

import os
import sqlite3

DATABASE_EXIST = os.path.exists("database.db")
conn = sqlite3.connect("database.db", check_same_thread = False)
cur = conn.cursor()
if not DATABASE_EXIST:
    cur.execute(f"CREATE TABLE finance (userid INT, last_checkin INT, checkin_continuity INT, \
        work_claim_time INT, work_reward INT, balance INT)")
    cur.execute(f"CREATE TABLE selfrole (guildid INT, channelid INT, msgid INT, title TEXT, description TEXT, imgurl TEXT)")
    cur.execute(f"CREATE TABLE rolebind (guildid INT, channelid INT, msgid INT, role INT, emoji VARCHAR(64))")
    cur.execute(f"CREATE TABLE userrole (guildid INT, channelid INT, msgid INT, userid INT, roleid INT)")
    cur.execute(f"CREATE TABLE serverstats (guildid INT, categoryid INT)")
    cur.execute(f"CREATE TABLE statsconfig (guildid INT, categoryid INT, channelid INT, conf TEXT)")
del cur

def newconn():
    conn = sqlite3.connect("database.db", check_same_thread = False)
    return conn