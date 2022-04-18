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

SETUP_MSG = """Gecko is a developing bot that can help you make your community better.
I'm ready to use slash commands and you type / to see a list of my commands.
Use /about for basic information about Gecko and /help for help.

You should set up dedicated channels for specific functions, tell me by using `/setchannel`.
Form     - Where notifications will be sent when a user submit an entry.
Four     - Where players will play connect four games.
Finance  - Where players will play finance games.
Music    - Where players will request for songs. If you don't set this up, only staff will be allowed to play music.
           If you want the bot to stick to a radio station and not being interrupted, then do not set it.
           *A bot can only be in one voice channel at the same time*
Level    - Where level updates will be posted.
GeckoUPD - The channel to follow #gecko-upd from **Gecko Community** where updates / maintenance schedules are published.
Eventlog - Where server events (messages / members etc) will be logged.
Botlog   - Where bot audit log will be sent.
Error    - Where important error notifications will be sent. (This should be rare)
**NOTE** 
1.For four, finance and music, you can set channel to "all" so that player can use related commands in any channels.
2.For level, if you set channel to "all", the level update will be posted at the channel where the user sent the last message before upgrading.
3.If the channel got deleted, it will be considered as that the channel hasn't been set up. And users cannot use related commands.

Have a nice day!"""

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
async def SetChannel(ctx, category: discord.Option(str, "The category of message.", required = True, choices = ["form", "four", "finance", "music", "level", "GeckoUPD", "eventlog", "botlog", "error"]),
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

    if not category in ["form", "four", "finance", "music", "level", "GeckoUPD", "error", "botlog", "eventlog"]:
        await ctx.respond(f"{category} is not a valid category.", ephemeral = True)
        return

    if remove == "Yes":
        if category == "GeckoUPD":
            await ctx.respond(f"Gecko does not support unfollowing channel, please go to **Server Settings** - **Integrations**")
            return

        cur.execute(f"DELETE FROM channelbind WHERE guildid = {guild.id} AND category = '{category}'")
        conn.commit()
        await ctx.respond(f"{category} channel bind removed.")
    else:
        if category in ["four", "finance", "music", "level"] and channel == "all":
            channel = 0
        else:
            if category == "GeckoUPD":
                try:
                    if not channel.startswith("<#") or not channel.endswith(">"):
                        await ctx.respond(f"{channel} is not a valid channel.", ephemeral = True)
                        return
                    channel = int(channel[2:-1])
                    channel = bot.get_channel(channel)
                    if channel is None:
                        await ctx.respond(f"Channel does not exist.", ephemeral = True)
                        return
                    destination = bot.get_channel(ANNOUNCEMENT_CHANNEL[1])
                    if destination is None:
                        await ctx.respond(f"Channel to follow (Gecko Update Channel) does not exist, this should be fixed very soon.\nYou could join [**Gecko Community**]({SUPPORT}) and let us know.")
                        return
                    await destination.follow(destination = channel)
                except:
                    import traceback
                    traceback.print_exc()
                    await ctx.respond(f"Something wrong happened.", ephemeral = True)
                    return
                await ctx.respond(f"<#{channel.id}> is now following **Gecko Update Channel**\nTo unfollow, please go to **Server Settings** - **Integrations**")
                return

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