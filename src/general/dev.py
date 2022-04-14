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

@bot.slash_command(name="guilds", description="Bot Owner - Get guilds bot is in.", guild_ids = [DEVGUILD])
@commands.is_owner()
async def DevGuilds(ctx):
    if ctx.author.id != BOTOWNER:
        return
    await ctx.defer()
    guilds = bot.guilds
    msg = ""
    for guild in guilds:
        msg += f"{guild} (`{guild.id}`) | **Owner** {guild.owner}\n"
    if len(msg) <= 2000:
        await ctx.respond(msg)
    else:
        f = io.BytesIO()
        f.write(msg.encode())
        f.seek(0)
        await ctx.respond(file=discord.File(fp=f, filename='Guilds.MD'))

@bot.slash_command(name="status", description="Bot Owner - Update bot activity status", guild_ids = [DEVGUILD])
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

@bot.slash_command(name="block", description="Bot Owner - Block a guild", guild_ids = [DEVGUILD])
@commands.is_owner()
async def BlockGuild(ctx, guild: Option(str, "Guild ID", required = True),
        reason: Option(str, "Reason for blocking", required = False)):
    if ctx.author.id != BOTOWNER:
        return
    guild = int(guild)
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM settings WHERE guildid = {guild} AND skey = 'block'")
    if cur.fetchone():
        await ctx.respond("Guild is already blocked.")
        return
    cur.execute(f"INSERT INTO settings VALUES ({guild}, 'block', '1')")
    conn.commit()
    guild = bot.get_guild(guild)
    try:
        if reason is None:
            await guild.text_channels[0].send(f"The guild has been blocked by Gecko Moderator.\nGecko has left the server and it will leave automatically if you invite again.\nTo appeal the ban, join Gecko support server.")
        else:
            await guild.text_channels[0].send(f"The guild has been blocked by Gecko Moderator.\nReason: {reason}\nGecko has left the server and it will leave automatically if you invite again.")
    except:
        pass
    await guild.leave()
    await ctx.respond("Guild blocked.")
    try:
        channel = bot.get_channel(GUILDUPD[1])
        await channel.send(f"**Block** {guild.name} (`{guild.id}`) - Owner: {str(guild.owner)}")
    except:
        import traceback
        traceback.print_exc()
        pass

@bot.slash_command(name="unblock", description="Bot Owner - Unblock a guild", guild_ids = [DEVGUILD])
@commands.is_owner()
async def UnblockGuild(ctx, guild: Option(str, "Guild ID", required = True)):
    if ctx.author.id != BOTOWNER:
        return
    guild = int(guild)
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM settings WHERE guildid = {guild} AND skey = 'block'")
    if not cur.fetchone():
        await ctx.respond("Guild not blocked.")
        return
    cur.execute(f"DELETE FROM settings WHERE guildid = {guild} AND skey = 'block'")
    conn.commit()
    await ctx.respond("Guild unblocked.")
    try:
        channel = bot.get_channel(GUILDUPD[1])
        await channel.send(f"**Unblock** `{guild}`")
    except:
        import traceback
        traceback.print_exc()
        pass