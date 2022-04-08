# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Developer-only Commands

import io
from bot import tbot
from settings import *
import discord
from discord import Option
from discord.ext import commands
from db import *
from functions import *

@tbot.command(name="guilds", description="Bot Owner - Get guilds bot is in.", guild_ids = [DEVGUILD])
@commands.is_owner()
async def tDevGuilds(ctx):
    if ctx.author.id != BOTOWNER:
        return
    guilds = bot.guilds
    msg = ""
    for guild in guilds:
        msg += f"{guild} (`{guild.id}`)\n"
    if len(msg) <= 2000:
        await ctx.send(msg)
    else:
        f = io.BytesIO()
        f.write(msg.encode())
        f.seek(0)
        await ctx.send(file=discord.File(fp=f, filename='Guilds.MD'))

@tbot.command(name="status", description="Bot Owner - Update bot activity status", guild_ids = [DEVGUILD])
@commands.is_owner()
async def tUpdStatus(ctx):
    if ctx.author.id != BOTOWNER:
        return
    d = ctx.message.content.split(" ")
    stype = d[1]
    status = " ".join(d[2:])
    if not stype in ["Gaming", "Listening", "Watching", "Streaming"]:
        await ctx.send("Invalid status type.")
        return
        
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM settings WHERE skey = 'status'")
    t = b64e(f'[{stype}] {status}')
    cur.execute(f"INSERT INTO settings VALUES (0, 'status', '{t}')")
    conn.commit()
    await ctx.send(f"Bot activity status updated to [{stype}] {status}")

    status = f"[{stype}] {status}"
    if status.startswith("[Gaming]"):
        await tbot.change_presence(activity=discord.Game(name = status[9:]))
    elif status.startswith("[Streaming]"):
        await tbot.change_presence(activity=discord.Streaming(name = status[12:].split("|")[0], url = status.split("|")[1]))
    elif status.startswith("[Listening]"):
        await tbot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status[12:]))
    elif status.startswith("[Watching]"):
        await tbot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status[11:]))