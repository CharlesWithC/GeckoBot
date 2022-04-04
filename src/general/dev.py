# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Developer-only Commands

import io
from bot import bot
from settings import *
import discord
from discord import Option
from discord.ext import commands
from db import *
from functions import *

@bot.slash_command(name="guilds", description="Bot Owner - Get guilds bot is in.")
@commands.is_owner()
async def DevGuilds(ctx):
    if ctx.author.id != BOTOWNER:
        return
    await ctx.defer()
    guilds = bot.guilds
    msg = ""
    for guild in guilds:
        msg += str(guild) + "\n"
    if len(msg) <= 2000:
        await ctx.respond(msg)
    else:
        f = io.BytesIO()
        f.write(msg.encode())
        f.seek(0)
        await ctx.respond(file=discord.File(fp=f, filename='Guilds.MD'))

@bot.slash_command(name="status", description="Bot Owner - Update bot activity status",)
@commands.is_owner()
async def UpdStatus(ctx, stype: Option(str, "Status type:", required = True, choices = ["Gaming", "Listening", "Watching", "Streaming"]),
    status: Option(str, "New status")):
    if ctx.author.id != BOTOWNER:
        return
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM settings WHERE skey = 'status'")
    t = b64e(f'[{stype}] {status}')
    cur.execute(f"INSERT INTO settings VALUES (0, 'status', '{t}')")
    conn.commit()
    await ctx.respond(f"Bot activity status updated to [{stype}] {status}")

    status = f"[{stype}] {status}"
    if status.startswith("[Gaming]"):
        await bot.change_presence(activity=discord.Game(name = status[9:]))
    elif status.startswith("[Streaming]"):
        await bot.change_presence(activity=discord.Streaming(name = status[12:].split("|")[0], url = status.split("|")[1]))
    elif status.startswith("[Listening]"):
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status[12:]))
    elif status.startswith("[Watching]"):
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status[11:]))