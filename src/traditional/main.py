# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio

import traditional.crypto
import traditional.dev
import traditional.help
import traditional.music
import traditional.games.finance
import traditional.games.four

from bot import tbot
from db import newconn
from settings import *
from functions import *

@tbot.command(name="stats", description="Gecko Bot Stats")
async def stats(ctx):
    # total servers and total users
    total_servers = len(tbot.guilds)
    total_users = 0
    total_channels = 0
    for guild in tbot.guilds:
        total_users += len(guild.members)
        total_channels += len(guild.text_channels)
    ping = tbot.latency
    
    embed = discord.Embed(title="Gecko Stats", color=GECKOCLR)
    embed.set_thumbnail(url=BOT_ICON)
    embed.add_field(name="Total Servers", value=total_servers)
    embed.add_field(name="Total Users", value=total_users)
    embed.add_field(name="Total Channels", value=total_channels)
    embed.add_field(name="Ping", value=f"{int(ping*1000)}ms")
    embed.set_footer(text="Gecko", icon_url=BOT_ICON)
    await ctx.send(embed=embed)

@tbot.command(name="setchannel", description="Staff - Set default channels where specific messages will be dealt with.")
async def SetChannel(ctx, category: str, channel: str):
    
    guild = ctx.guild
    if guild is None:
        await ctx.send(f"You can only use this command in guilds, not in DMs.")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.send("Only staff are allowed to run the command!")
        return

    conn = newconn()
    cur = conn.cursor()

    if not category in ["form", "four", "finance", "music", "error", "log", "deleted"]:
        await ctx.send(f"{category} is not a valid category.")
        return

    if category in ["four", "finance", "music"] and channel == "all":
        channel = 0
    else:
        if not channel.startswith("<#") or not channel.endswith(">"):
            await ctx.send(f"{channel} is not a valid channel.")
            return
        channel = int(channel[2:-1])
    
    cur.execute(f"SELECT * FROM channelbind WHERE guildid = {guild.id} AND category = '{category}'")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO channelbind VALUES ({guild.id}, '{category}', {channel})")
    else:
        cur.execute(f"UPDATE channelbind SET channelid = {channel} WHERE guildid = {guild.id} AND category = '{category}'")
    conn.commit()
    if channel != 0:
        await ctx.send(f"<#{channel}> has been configured as {category} channel.\nMake sure I always have access to it.\nUnless you want to stop dealing with those messages, then delete the channel.")
    else:
        await ctx.send(f"Members can use {category} commands in any channels.")

# non-interaction purge message
@tbot.command(name="purge", description="Staff - Purge messages.")
async def Purge(ctx, count: int):
    guild = ctx.guild
    if guild is None:
        await ctx.send(f"You can only use this command in guilds, not in DMs.")
        return

    if not isStaff(ctx.guild, ctx.author):
        return

    if count < 1 or count > 100:
        await ctx.send("You can only delete at most 100 messages at a time.")
        return

    await ctx.message.delete()
    await ctx.channel.purge(limit=count)

@tbot.command(name="ping", description="Get the bot's ping to discord API.")
async def tping(ctx):
    await ctx.send(f"Pong! {int(tbot.latency * 1000)}ms.")