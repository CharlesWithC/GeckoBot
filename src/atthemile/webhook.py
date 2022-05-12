# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# At The Mile Logistics VTC exclusive

import os, json, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from time import time
from datetime import datetime
from random import randint

from flask import Flask, request
from bot import tbot
from settings import *
from functions import *
import threading
import asyncio
from db import newconn
atmflask = Flask(__name__)

ATMGUILD = 929761730089877626
APPLICANT = 942478809175830588

ATMGUILD = 929761730089877626
CHNID = 969667013549121667
MSGID = 969766478679269416
UPDID = 941537154360823870

ADMINROLES = [929761730547032135, 941544365950644224, 941544363614433320, 941903394703020072]

LEVEL = {0: 941548241126834206, 2000: 941544375790489660, 10000: 941544368928596008, 15000: 969678264832503828, 25000: 941544370467901480, 40000: 969727939686039572, 50000: 941544372669907045, 75000: 969678270398341220, 80000: 969727945075732570, 100000: 941544373710094456, 150000: 969727950016643122, 200000: 969727954433245234, 250000: 969678280112353340, 300000: 969727958749155348, 350000: 969727962905735178, 400000: 969727966999379988, 450000: 969727971428536440, 500000: 941734703210311740, 600000: 969727975358607380, 700000: 969727979368370188, 800000: 969728350564282398, 900000: 969678286332518460, 1000000: 941734710470651964}

def GetLevel(point):
    pnts = list(LEVEL.keys())[::-1]
    for pnt in pnts:
        if point >= pnt:
            return LEVEL[pnt]

# @atmflask.route("/atm/applicant")
# def ATMapplicant():
#     guild = tbot.get_guild(ATMGUILD)
#     role = guild.get_role(APPLICANT)
#     userid = request.args.get("userid")
#     channel = tbot.get_channel(941562364174688256)
#     try:
#         userid = int(userid)
#     except:
#         tbot.loop.create_task(channel.send(f"Invalid user ID: {userid}. Applicant role not given."))
#         return {"success": False, "message": "Invalid user ID!"}
#     user = guild.get_member(userid)
#     if user is None:
#         tbot.loop.create_task(channel.send(f"User not found: {userid}. Applicant role not given."))
#         return {"success": False, "msg": "User not found!"}
#     tbot.loop.create_task(user.add_roles(role, reason = "Applicant from website"))
#     return {"success": True}

def TSeparator(num):
    num = str(num)
    if len(num) <= 3:
        return num
    return TSeparator(num[:-3]) + "," + num[-3:]

async def updmsg(embed):
    channel = tbot.get_channel(CHNID)
    message = await channel.fetch_message(MSGID)
    await message.edit(embed = embed)

@atmflask.route("/internal/mile")
def mile():
    if request.remote_addr != "127.0.0.1":
        return "Access denied!"
    mile = int(request.args.get("mile"))
    user = int(request.args.get("user"))
    userid = user
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT mile, totpnt FROM atm WHERE userid = {userid}")
    t = cur.fetchall()
    org = 0
    tot = 0
    if len(t) == 0:
        cur.execute(f"INSERT INTO atm VALUES ({userid}, {mile}, 0, {mile})")
    else:
        cur.execute(f"UPDATE atm SET mile = mile + {mile}, totpnt = totpnt + {mile} WHERE userid = {userid}")
        org = t[0][1]
        tot = t[0][1] + mile
    conn.commit()
    
    guild = tbot.get_guild(ATMGUILD)
    orglvl = GetLevel(org)
    totlvl = GetLevel(tot)

    if totlvl != orglvl:
        role = None
        try:
            role = guild.get_role(orglvl)
            u = guild.get_member(userid)
            tbot.loop.create_task(u.remove_roles(role, reason = "ATM Driver Rank Up"))
        except:
            import traceback
            traceback.print_exc()
            pass
        try:
            role = guild.get_role(totlvl)
            u = guild.get_member(userid)
            tbot.loop.create_task(u.add_roles(role, reason = "ATM Driver Rank Up"))
        except:
            import traceback
            traceback.print_exc()
            pass
        channel = tbot.get_channel(UPDID)
        embed = discord.Embed(title = f"Rank Up", description = f"<@{user}> has ranked up to {role.mention}!", color = TMPCLR)
        tbot.loop.create_task(channel.send(embed = embed))
    
    cur.execute(f"SELECT userid, totpnt, mile, eventpnt FROM atm ORDER BY totpnt DESC")
    t = cur.fetchall()
    msg = "**Driver Rankings**\n*Miles + Event Points = **Total Points***\n"
    lstlvl = 0
    for tt in t:
        lvl = GetLevel(tt[1])
        if lvl != lstlvl:
            msg += f"\n<@&{lvl}>\n"
            lstlvl = lvl
        msg += f"<@{tt[0]}> {TSeparator(tt[2])} + {TSeparator(tt[3])} = **{TSeparator(tt[1])}**\n"
    
    embed = discord.Embed(title = "At The Mile Logistics", description = msg, color = TMPCLR)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/icons/929761730089877626/a_0df4f6de129299542fc0a6ca4b72d737.gif")
    embed.set_footer(text = f"Powered by Gecko | CharlesWithC ", icon_url = GECKOICON)
    embed.timestamp = datetime.now()
    tbot.loop.create_task(updmsg(embed))

    return {"success": True}

@atmflask.route("/internal/event")
def event():
    if request.remote_addr != "127.0.0.1":
        return "Access denied!"
    conn = newconn()
    cur = conn.cursor()

    users = request.args.get("users")
    point = int(request.args.get("point"))

    guild = tbot.get_guild(ATMGUILD)
    channel = tbot.get_channel(UPDID)
    users = users.split(",")
    ret = ""
    for user in users:        
        ret += f"<@{user}> "

    embed = discord.Embed(title = f"Event Point", description = f"{TSeparator(point)} points have been given to {ret}!", color = TMPCLR)
    mmm = tbot.loop.create_task(channel.send(embed = embed))
    
    for user in users:
        userid = int(user)

        cur.execute(f"SELECT eventpnt, totpnt FROM atm WHERE userid = {userid}")
        t = cur.fetchall()
        org = 0
        tot = 0
        if len(t) == 0:
            cur.execute(f"INSERT INTO atm VALUES ({userid}, 0, {point}, {point})")
        else:
            cur.execute(f"UPDATE atm SET eventpnt = eventpnt + {point}, totpnt = totpnt + {point} WHERE userid = {userid}")
            org = t[0][1]
            tot = t[0][1] + point
        conn.commit()
        
        orglvl = GetLevel(org)
        totlvl = GetLevel(tot)

        if totlvl != orglvl:
            role = None
            try:
                role = guild.get_role(orglvl)
                u = guild.get_member(userid)
                tbot.loop.create_task(u.remove_roles(role, reason = "ATM Driver Rank Up"))
            except:
                pass
            try:
                role = guild.get_role(totlvl)
                u = guild.get_member(userid)
                tbot.loop.create_task(u.add_roles(role, reason = "ATM Driver Rank Up"))
            except:
                pass
            embed = discord.Embed(title = f"Rank Up", description = f"<@{userid}> has ranked up to {role.mention}!", color = TMPCLR)
            tbot.loop.create_task(channel.send(embed = embed))
    
    cur.execute(f"SELECT userid, totpnt, mile, eventpnt FROM atm ORDER BY totpnt DESC")
    t = cur.fetchall()
    msg = "**Driver Rankings**\n*Miles + Event Points = **Total Points***\n"
    lstlvl = 0
    for tt in t:
        lvl = GetLevel(tt[1])
        if lvl != lstlvl:
            msg += f"\n<@&{lvl}>\n"
            lstlvl = lvl
        msg += f"<@{tt[0]}> {TSeparator(tt[2])} + {TSeparator(tt[3])} = **{TSeparator(tt[1])}**\n"
        
    embed = discord.Embed(title = "At The Mile Logistics", description = msg, color = TMPCLR)
    embed.set_thumbnail(url = "https://cdn.discordapp.com/icons/929761730089877626/a_0df4f6de129299542fc0a6ca4b72d737.gif")
    embed.set_footer(text = f"Powered by Gecko | CharlesWithC ", icon_url = GECKOICON)
    embed.timestamp = datetime.now()
    tbot.loop.create_task(updmsg(embed))

    return {"success": True}

threading.Thread(target = atmflask.run, args = ("127.0.0.1", 58001)).start()