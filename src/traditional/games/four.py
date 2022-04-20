# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Fun House - Connect Four

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ui import Button, View
from discord.ext import commands
from time import time, gmtime, strftime
from datetime import datetime
from random import randint

from bot import tbot
from settings import *
from functions import *
from db import newconn

from general.games.four import ConnectFourJoinButton

WHITE = ":white_circle:"
RED = ":red_circle:"
BLUE = ":blue_circle:"
NUM = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
TNUM = "".join(NUM)

@tbot.command(name="four", description="Connect Four - Start a game")
async def start(ctx):
    await ctx.channel.trigger_typing()
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return
    guildid = ctx.guild.id

    opponent = None
    bet = None
    t = ctx.message.content.split(" ")
    for tt in t[1:]:
        try:
            tt = int(tt)
            bet = tt
        except:
            opponent = tt.replace("<@!","<@")
            if not opponent.startswith("<@") or not opponent.endswith(">"):
                await ctx.send("Invalid opponent! You must tag the user.")
                return
            opponent = int(opponent[2:-1])

    conn = newconn()
    cur = conn.cursor()
    
    guildid = 0
    if not ctx.guild is None:
        guildid = ctx.guild.id

        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'four'")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.send(f"{ctx.author.name}, staff haven't set up a connect four game channel yet! Tell them to use `/setchannel four {{#channel}}` to set it up!")
            return
        if t[0][0] != ctx.channel.id and t[0][0] != 0:
            await ctx.send(f"This is not the channel for connect four games!")
            return
    
    if opponent is None:
        opponent = 0
    
    if bet is None:
        bet = 0
    else:
        cur.execute(f"SELECT balance FROM finance WHERE userid = {ctx.author.id} AND guildid = {ctx.guild.id}")
        t = cur.fetchall()
        if len(t) == 0 or t[0][0] < bet:
            await ctx.send(f"You don't have enough coins to bet.")
            return
    
    additional = "\n"
    if bet > 0:
        additional = f"The match starter bet {bet} :coin:, and their opponent have to pay {bet} :coin: to join.\n"
    
    view = View()
    uniq = f"{randint(1,100000)}{int(time()*100000)}"
    customid = f"GeckoConnectFourGame-{ctx.author.id}-{opponent}-{bet}-{uniq}"
    button = ConnectFourJoinButton(f"Join Match", customid)
    view.add_item(button)
    if opponent != 0:
        await ctx.send(content = f"<@{opponent}>, you are invited to join **Connect Four** match started by <@{ctx.author.id}>.\n{additional}Press 'Join Match' to start the game.", view = view)
    else:
        await ctx.send(content = f"<@{ctx.author.id}> started a **Connect Four** match.\n{additional}Press 'Join Match' to start the game.", view = view)
    cur.execute(f"INSERT INTO buttonview VALUES ({int(time())}, '{customid}')")
    conn.commit()

@tbot.command(name="fresult", description="Connect Four - Get the result (including the final state) of a given game.")
async def result(ctx, gameid: int):
    await ctx.channel.trigger_typing()    
    if ctx.guild is None:
        await ctx.send("You can only run this command in guilds!")
        return
    guildid = ctx.guild.id

    conn = newconn()
    cur = conn.cursor()

    try:
        gameid = int(gameid)
    except:
        await ctx.send(f"{gameid} is not a valid game ID.")
        return

    cur.execute(f"SELECT COUNT(*) FROM connectfour")
    t = cur.fetchall()
    if len(t) == 0 or t[0][0] < gameid:
        await ctx.send(f"{gameid} is not a valid game ID.")
        return
    
    cur.execute(f"SELECT * FROM connectfour WHERE ABS(gameid) = {gameid} AND guildid = {guildid}")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send(f"The game didn't happen in this guild and you cannot access it.")
        return

    cur.execute(f"SELECT red, blue, state FROM connectfour WHERE gameid = -{gameid} AND guildid = {guildid}")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send(f"The game hasn't ended yet.")
        return
    
    red = t[0][0]
    blue = t[0][1]
    result = f"{RED} <@{red}> vs {BLUE} <@{blue}>\n"
    state = t[0][2]
    won = state.split("|")[0]
    if won == "-1":
        result += f"{RED} <@{red}> won\n"
    elif won == "-2":
        result += f"{BLUE} <@{blue}> won\n"
    elif won == "-3":
        result += f"**Draw**\n"
    elif won == "0":
        result += f"**Game cancelled due to inactivity**\n"
    result += "\nFinal state:\n"
    state = state.split("|")[1]
    pstate = ""
    for i in range(6):
        pstate = state[i*7:(i+1)*7] + "\n" + pstate
    pstate = pstate.replace("0", WHITE)
    pstate = pstate.replace("1", RED)
    pstate = pstate.replace("2", BLUE)
    pstate = TNUM + "\n" + pstate
    result += pstate
    embed = discord.Embed(title = f"Connect Four - Game #{gameid}", description=result, color = GECKOCLR)

    await ctx.send(embed = embed)

@tbot.command(name="fleaderboard", description="Connect Four - Get the leaderboard.")
async def leaderboard(ctx):
    await ctx.channel.trigger_typing()    
    conn = newconn()
    cur = conn.cursor()

    t = ctx.message.content.split(" ")
    sortby = None
    if len(t) > 1:
        sortby = t[1]

    if sortby == "earnings":
        sortby = "earning"
    elif sortby == "wins":
        sortby = "won"
    elif sortby == "losses":
        sortby = "lost"
    if not sortby in ["earning", "won", "lost"]:
        sortby = "won" # decided by copilot
    cur.execute(f"SELECT userid, {sortby} FROM connectfour_leaderboard ORDER BY {sortby} DESC LIMIT 10")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send(f"Nobody has played the game.")
        return
    
    result = ""
    for i in range(len(t)):
        if sortby == "earning":
            result += f"{RANK_EMOJI[i+1]} **{bot.get_user(t[i][0]).name}**\n:coin: {t[i][1]}\n"
        elif sortby == "won":
            result += f"{RANK_EMOJI[i+1]} **{bot.get_user(t[i][0]).name}**\n:medal: {t[i][1]}\n"
        elif sortby == "lost":
            result += f"{RANK_EMOJI[i+1]} **{bot.get_user(t[i][0]).name}**\n:x: {t[i][1]}\n"
        
    embed = discord.Embed(title = "Connect Four - Leaderboard", description=result, color = GECKOCLR)
    embed.set_footer(text = "The leaderboard includes all players, throughout all guilds.", icon_url = GECKOICON)
    await ctx.send(embed = embed)

@tbot.command(name="fstatistics", description="Connect Four - Get your statistics.")
async def statistics(ctx):
    await ctx.channel.trigger_typing()    
    conn = newconn()
    cur = conn.cursor()

    cur.execute(f"SELECT won, lost, draw, earning FROM connectfour_leaderboard WHERE userid = {ctx.author.id}")
    t = cur.fetchall()
    if len(t) == 0:
        await ctx.send(f"You haven't played the game.")
        return
    
    result = f"**{ctx.author.name}**\n"
    embed = discord.Embed(title = f"{ctx.author}", description="```Connect Four - Statistics```", color = GECKOCLR)
    if not ctx.author.avatar is None:
        embed.set_thumbnail(url = ctx.author.avatar.url)
    embed.add_field(name = "Games", value = f"```{t[0][0]+t[0][1]+t[0][2]}```", inline = True)
    embed.add_field(name = chr(173), value = chr(173))
    embed.add_field(name = "Earnings", value = f"```{t[0][3]}```", inline = True)

    embed.add_field(name = "Wins", value = f"```{t[0][0]}```", inline = True)
    embed.add_field(name = "Draws", value = f"```{t[0][2]}```", inline = True)
    embed.add_field(name = "Losses", value = f"```{t[0][1]}```", inline = True)

    embed.set_footer(text = "The statistics include all games played, throughout all guilds.", icon_url = GECKOICON)
    await ctx.send(embed = embed)