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
import time
from datetime import datetime

@bot.slash_command(name="guilds", description="Bot Owner - Get guilds bot is in.", guild_ids = [DEVGUILD])
@commands.is_owner()
async def DevGuilds(ctx):
    if ctx.author.id != BOTOWNER:
        return
    await ctx.defer()
    guilds = bot.guilds
    msg = ""
    for guild in guilds:
        msg += f"{guild} (`{guild.id}`) | **Owner** `{guild.owner}`\n"
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

@bot.slash_command(name="givepremium", description="Bot Owner - Give a guild premium", guild_ids = [DEVGUILD])
@commands.is_owner()
async def GivePremium(ctx, guildid: Option(str, "Guild ID", required = True),
        days: Option(int, "Days of premium", required = True),
        tier: Option(int, "Premium Tier (0, 1, 2). Higher tier overrides lower tier.", required = True)):
    if ctx.author.id != BOTOWNER:
        return
    guildid = int(guildid)
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()

    expire = int(time.time())
    cur.execute(f"SELECT expire FROM premium WHERE guildid = {guildid} AND expire > {int(time.time())}")
    t = cur.fetchall()
    if len(t) > 0:
        expire = t[0][0]
    expire += (days * 86400)
    if days == 0:
        expire = 0
    cur.execute(f"DELETE FROM premium WHERE guildid = {guildid}")
    cur.execute(f"INSERT INTO premium VALUES ({guildid}, {tier}, {expire})")
    conn.commit()
    dt = datetime.fromtimestamp(expire)
    await ctx.respond(f"{guildid} is given Premium Tier {tier}, expire on {datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}")
    try:
        channel = bot.get_channel(GUILDUPD[1])
        await channel.send(f"**Premium** `{guildid}` Tier **{tier}** Expire **{datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}**")
    except:
        pass

@bot.slash_command(name="giveallpremium", description="Bot Owner - Give all guilds premium", guild_ids = [DEVGUILD])
@commands.is_owner()
async def GiveAllPremium(ctx, days: Option(int, "Days of premium", required = True),
        tier: Option(int, "Premium Tier (0, 1, 2). Higher tier overrides lower tier.", required = True)):
    if ctx.author.id != BOTOWNER:
        return
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    
    msgs1 = ""
    msgs2 = ""

    for guild in bot.guilds:
        guildid = guild.id
        expire = int(time.time())
        cur.execute(f"SELECT expire FROM premium WHERE guildid = {guildid} AND expire > {int(time.time())}")
        t = cur.fetchall()
        if len(t) > 0:
            expire = t[0][0]
        expire += (days * 86400)
        if days == 0:
            expire = 0
        cur.execute(f"DELETE FROM premium WHERE guildid = {guildid}")
        cur.execute(f"INSERT INTO premium VALUES ({guildid}, {tier}, {expire})")
        conn.commit()
        dt = datetime.fromtimestamp(expire)
        msgs1 += f"{guildid} is given Premium Tier {tier}, expire on {datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}\n"
        msgs2 += f"**Premium** `{guildid}` Tier **{tier}** Expire **{datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}**\n"

    if len(msgs1) <= 2000:
        await ctx.respond(msgs1)
    else:
        f = io.BytesIO()
        f.write(msg.encode())
        f.seek(0)
        await ctx.respond(file=discord.File(fp=msg1, filename='PremiumUpdate.MD'))
    try:
        channel = bot.get_channel(GUILDUPD[1])
        if len(msgs2) <= 2000:
            await channel.send(msgs2)
        else:
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            await channel.send(file=discord.File(fp=msgs2, filename='PremiumUpdate.MD'))
    except:
        pass

@bot.slash_command(name="checkpremium", description="Bot Owner - Check guild premium status", guild_ids = [DEVGUILD])
@commands.is_owner()
async def CheckPremium(ctx, guildid: Option(str, "Guild ID", required = True)):
    if ctx.author.id != BOTOWNER:
        return
    guildid = int(guildid)
    await ctx.defer()
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT tier, expire FROM premium WHERE guildid = {guildid} AND expire > {int(time.time())}")
    t = cur.fetchall()
    if len(t) > 0:
        expire = t[0][1]
        dt = datetime.fromtimestamp(expire).strftime('%Y-%m-%d')
        await ctx.respond(f"`{guildid}` Premium Tier {t[0][0]} expires on {dt}")
    else:
        await ctx.respond(f"`{guildid}` isn't subscribed to Premium.")