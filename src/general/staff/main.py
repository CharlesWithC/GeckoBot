# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio
import sys, os
from time import time
from datetime import datetime

from bot import bot, shard
from db import newconn
from settings import *
from functions import *

@bot.slash_command(name="setup", description="Hint to setup Gecko in the guild.")
async def BotSetup(ctx):
    await ctx.defer()
    guild = ctx.guild
    if not guild is None:
        try:
            channel = await ctx.author.create_dm()
            await channel.send(f"Hi, {ctx.author.name}\n" + SETUP_MSG)
            await ctx.respond(f"Check your DM")
        except:
            await ctx.respond(f"I cannot DM you")
    else:
        await ctx.respond(f"Hi, {ctx.author.name}\n" + SETUP_MSG)

@bot.slash_command(name="setchannel", description="Staff - Set default channels where specific messages will be dealt with.")
async def SetChannel(ctx, category: discord.Option(str, "The category of message.", required = True, choices = ["form", "four", "finance", "music", "level", "eventlog", "botlog", "error"]),
    channel: discord.Option(str, "Channel for messages, type 'all' for four / finance / music to allow all channels", required = True),
    remove: discord.Option(str, "Whether to unbind the category and the channel", required = False, choices = ["Yes", "No"])):
    
    await ctx.defer()
    guild = ctx.guild
    if guild is None:
        await ctx.respond(f"You can only use this command in guilds, not in DMs.")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()

    if not category in ["form", "four", "finance", "music", "level", "error", "botlog", "eventlog"]:
        await ctx.respond(f"{category} is not a valid category.", ephemeral = True)
        return

    if remove == "Yes":
        cur.execute(f"DELETE FROM channelbind WHERE guildid = {guild.id} AND category = '{category}'")
        conn.commit()
        await ctx.respond(f"{category} channel bind removed.")
    else:
        if category in ["four", "finance", "music", "level"] and channel == "all":
            channel = 0
        else:
            if not channel.startswith("<#") or not channel.endswith(">"):
                await ctx.respond(f"{channel} is not a valid channel.", ephemeral = True)
                return
            channel = int(channel[2:-1])
            chn = bot.get_channel(channel)
            if chn is None:
                await ctx.respond(f"{channel} is not a valid channel.", ephemeral = True)
                return
        cur.execute(f"SELECT * FROM channelbind WHERE guildid = {guild.id} AND category = '{category}'")
        t = cur.fetchall()
        if len(t) == 0:
            cur.execute(f"INSERT INTO channelbind VALUES ({guild.id}, '{category}', {channel})")
        else:
            cur.execute(f"UPDATE channelbind SET channelid = {channel} WHERE guildid = {guild.id} AND category = '{category}'")
        conn.commit()
        if channel != 0:
            await ctx.respond(f"<#{channel}> has been configured as {category} channel.\nMake sure I always have access to it.\nUnless you want to stop dealing with those messages, then delete the channel.")
        else:
            await ctx.respond(f"Members can use {category} commands in any channels.")
            
@bot.slash_command(name="purge", description="Staff - Purge messages.")
async def Purge(ctx, count: discord.Option(int, "Number of messages to delete.", required = True)):
    await ctx.defer()
    guild = ctx.guild
    if guild is None:
        await ctx.respond(f"You can only use this command in guilds, not in DMs.")
        return

    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    if count < 1 or count > 100:
        await ctx.respond("You can only delete at most 100 messages at a time.", ephemeral = True)
        return

    try:
        await ctx.channel.purge(limit = count + 1)
    except:
        await ctx.respond("I don't have permission to delete messages.", ephemeral = True)