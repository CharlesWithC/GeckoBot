# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Fun House - Finance

import os, asyncio
import discord
from time import time, gmtime, strftime
from datetime import datetime
from random import randint
from base64 import b64encode, b64decode

from bot import bot
from settings import *
from functions import *
from db import newconn

async def finance_log(text):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [Finance] {text}"
    print(text)
    try:
        channel = bot.get_channel(FINANCE_LOG_CHANNEL[1])
        await channel.send(f"```{text}```")
    except:
        pass
    
@bot.slash_command(name="balance", description="Finance Game - Get your balance.")
async def FinanceBalance(ctx):
    conn = newconn()
    cur = conn.cursor()
    
    guildid = 0
    if not ctx.guild is None:
        guildid = ctx.guild.id

        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'finance'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a finance game channel yet! Tell them to use `/setchannel finance {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for finance games!", ephemeral = True)
            return
        
    await ctx.trigger_typing()
    userid = ctx.author.id
    cur.execute(f"SELECT balance FROM finance WHERE userid = {userid} AND guildid = {guildid}")
    t = cur.fetchall()
    if len(t) == 0: # user not found, create user
        cur.execute(f"INSERT INTO finance VALUES ({guildid}, {userid}, 0, 0, 0, 0, 0)")
        t = [[0]]
    balance = t[0][0]

    cur.execute(f"SELECT userid FROM finance WHERE guildid = {guildid} ORDER BY balance DESC")
    t = cur.fetchall()
    rank = 0
    for tt in t:
        rank += 1
        if userid == tt[0]:
            break
    
    embed = discord.Embed(description=f"{ctx.author.name}, you have **{balance}** :coin:, ranking **#{rank}**.", color=0x0000DD)
    await ctx.respond(embed=embed)
    
@bot.slash_command(name="checkin", description="Finance Game - Do daily checkin to earn coins.")
async def FinanceCheckIn(ctx):
    conn = newconn()
    cur = conn.cursor()
    
    guildid = 0
    if not ctx.guild is None:
        guildid = ctx.guild.id

        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'finance'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a finance game channel yet! Tell them to use `/setchannel finance {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for finance games!", ephemeral = True)
            return

    await ctx.trigger_typing()
    userid = ctx.author.id
    cur.execute(f"SELECT last_checkin, checkin_continuity, balance FROM finance WHERE userid = {userid} AND guildid = {guildid}")
    t = cur.fetchall()
    if len(t) == 0: # user not found, create user
        cur.execute(f"INSERT INTO finance VALUES ({guildid}, {userid}, 0, 0, 0, 0, 0)")
        t = [[0, 0, 0]]
    
    last_checkin = t[0][0]
    checkin_continuity = t[0][1]
    balance = t[0][2]

    bonus = 0
    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0)
    last = datetime.fromtimestamp(last_checkin)
    last = datetime(last.year, last.month, last.day, 0)
    if today == last:
        embed = discord.Embed(description=f"{ctx.author.name}, you have already checked in today, come back tomorrow!", color=0xDD0000)
        await ctx.respond(embed=embed)
    else:
        if (today - last).days == 1:
            checkin_continuity += 1
            bonus = checkin_continuity * 2 + 1
        else:
            checkin_continuity = 0
        reward = FINANCE_CHECKIN_BASE_REWARD
        for _ in range(checkin_continuity):
            reward *= 1.05
        reward = int(reward)
        reward += randint(-100, 100)
        balance = balance + reward
        cur.execute(f"UPDATE finance SET last_checkin = {time()} WHERE userid = {userid} AND guildid = {guildid}")
        cur.execute(f"UPDATE finance SET checkin_continuity = {checkin_continuity} WHERE userid = {userid} AND guildid = {guildid}")
        cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid} AND guildid = {guildid}")
        conn.commit()
        if bonus == 0:
            embed = discord.Embed(description=f"{ctx.author.name}, you earned **{reward}** :coin:!", color=0x00DD00)
            await ctx.respond(embed=embed)
            await finance_log(f"{ctx.author} ({ctx.author.id}) earned {reward} coins for checking in, current balance {balance}.")
        else:
            embed = discord.Embed(description=f"{ctx.author.name}, **{checkin_continuity + 1} days in a row!** You earned {reward} :coin:!", color=0x00DD00)
            await ctx.respond(embed=embed)
            await finance_log(f"{ctx.author} ({ctx.author.id}) earned {reward} coins for checking in {checkin_continuity + 1} days in a row, current balance {balance}.")

@bot.slash_command(name="work", description="Finance Game - Work to earn coins.")
async def FinanceWork(ctx):
    conn = newconn()
    cur = conn.cursor()

    guildid = 0
    if not ctx.guild is None:
        guildid = ctx.guild.id
        
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'finance'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a finance game channel yet! Tell them to use `/setchannel finance {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for finance games!", ephemeral = True)
            return

    await ctx.trigger_typing()
    userid = ctx.author.id
    cur.execute(f"SELECT work_claim_time, work_reward, balance FROM finance WHERE userid = {userid} AND guildid = {guildid}")
    t = cur.fetchall()
    if len(t) == 0: # user not found, create user
        cur.execute(f"INSERT INTO finance VALUES ({guildid}, {userid}, 0, 0, 0, 0, 0)")
        t = [[0, 0, 0]]
    
    work_claim_time = t[0][0]
    work_reward = t[0][1]
    balance = t[0][2]

    if work_claim_time > time():
        if work_reward > 0:
            embed = discord.Embed(description=f"{ctx.author.name}, you haven't finished the last delivery! Come back after **{TimeDelta(work_claim_time)}**.", color=0xDD0000)
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(description=f"{ctx.author.name}, you are still resting! Come back after **{TimeDelta(work_claim_time)}**.", color=0xDD0000)
            await ctx.respond(embed=embed)

    else:
        balance += work_reward
        if randint(1,24) == 24 and work_reward != 0 and time() - work_claim_time <= 600: # rest, only if re-work
            work_claim_time = int(time() + 30 * 60)
            work_reward = 0

            cur.execute(f"UPDATE finance SET work_claim_time = {work_claim_time} WHERE userid = {userid} AND guildid = {guildid}")
            cur.execute(f"UPDATE finance SET work_reward = {work_reward} WHERE userid = {userid} AND guildid = {guildid}")
            cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid} AND guildid = {guildid}")
            conn.commit()

            embed = discord.Embed(description=f"{ctx.author.name}, you finished your delivery and earned **{work_reward}** :coin:. However you are too tired and need to have a rest. Come back after 30 minutes!", color=0x00DD00)
            await ctx.respond(embed=embed)
            await finance_log(f"{ctx.author} ({ctx.author.id}) earned {work_reward} coins from working, current balance {balance}.")

        else: # new work
            last_reward = work_reward

            length = randint(30, 120)
            work_claim_time = int(time() + length * 60)
            work_reward = 200 + randint(-100, 100)

            cur.execute(f"UPDATE finance SET work_claim_time = {work_claim_time} WHERE userid = {userid} AND guildid = {guildid}")
            cur.execute(f"UPDATE finance SET work_reward = {work_reward} WHERE userid = {userid} AND guildid = {guildid}")
            cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid} AND guildid = {guildid}")
            conn.commit()

            if last_reward != 0:
                embed = discord.Embed(description=f"{ctx.author.name}, you earned **{last_reward}** :coin: from your last job. And you started working again, this job will finish in **{length} minutes** and you will earn **{work_reward}** :coin:.", color=0x00DD00)
                await ctx.respond(embed=embed)
                await finance_log(f"{ctx.author} ({ctx.author.id}) earned {last_reward} coins from working, current balance {balance}.")

            else:
                embed = discord.Embed(description=f"{ctx.author.name}, you started working, the job will finish in **{length} minutes** and you will earn **{work_reward}** :coin:.", color=0x00DD00)
                await ctx.respond(embed=embed)

@bot.slash_command(name="claim", description="Finance Game - Claim the reward from your last work.")
async def FinanceClaim(ctx):
    conn = newconn()
    cur = conn.cursor()

    guildid = 0
    if not ctx.guild is None:
        guildid = ctx.guild.id
        
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'finance'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a finance game channel yet! Tell them to use `/setchannel finance {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for finance games!", ephemeral = True)
            return
        
    await ctx.trigger_typing()
    userid = ctx.author.id
    cur.execute(f"SELECT work_claim_time, work_reward, balance FROM finance WHERE userid = {userid} AND guildid = {guildid}")
    t = cur.fetchall()
    if len(t) == 0: # user not found, create user
        cur.execute(f"INSERT INTO finance VALUES ({guildid}, {userid}, 0, 0, 0, 0, 0)")
        t = [[0, 0, 0]]
    
    work_claim_time = t[0][0]
    work_reward = t[0][1]
    balance = t[0][2]

    if work_reward == 0:
        embed = discord.Embed(description=f"{ctx.author.name}, you are not working! Use !work to start working.", color=0xDD0000)
        await ctx.respond(embed=embed)

    elif work_claim_time > time():
        embed = discord.Embed(description=f"{ctx.author.name}, you haven't finished the delivery! Come back after **{TimeDelta(work_claim_time)}**.", color=0xDD0000)
        await ctx.respond(embed=embed)

    else:
        balance += work_reward

        cur.execute(f"UPDATE finance SET work_reward = 0 WHERE userid = {userid} AND guildid = {guildid}")
        cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid} AND guildid = {guildid}")
        conn.commit()

        embed = discord.Embed(description=f"{ctx.author.name}, you earned **{work_reward}** :coin: from your last job!", color=0x00DD00)
        await ctx.respond(embed=embed)
        await finance_log(f"{ctx.author} ({ctx.author.id}) earned {work_reward} coins from working, current balance {balance}.")

@bot.slash_command(name="richest", description="Finance Game - Get the richest players in this guild.")
async def FinanceRichest(ctx):
    conn = newconn()
    cur = conn.cursor()

    guildid = 0
    if not ctx.guild is None:
        guildid = ctx.guild.id
        
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'finance'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"{ctx.author.name}, staff haven't set up a finance game channel yet! Tell them to use `/setchannel finance {{#channel}}` to set it up!", ephemeral = True)
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.respond(f"This is not the channel for finance games!", ephemeral = True)
            return
        
    await ctx.trigger_typing()
    cur.execute(f"SELECT userid, balance FROM finance WHERE guildid = {guildid} AND userid != {BOTOWNER} ORDER BY balance DESC")
    t = cur.fetchall()

    msg = ""
    rank = 0
    for tt in t:
        rank += 1
        if rank > 10:
            break
        
        msg += f"**{RANK_EMOJI[rank]} {bot.get_user(tt[0]).name}**\n:coin: {tt[1]}\n\n"
    
    embed = discord.Embed(title="**Top 10 richest players**", description=msg, color=0x0000DD)
    await ctx.respond(embed=embed)