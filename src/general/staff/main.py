# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio
import sys, os
from time import time
from datetime import datetime
import chat_exporter, minify_html, io

from bot import bot, shard
from db import newconn
from settings import *
from functions import *

SETUP_MSG = """Gecko is a multi-purpose moderation bot that can help you make your community better.
Use /about for basic information about Gecko and /help for help.

You should set up dedicated channels for specific functions, tell me by using `/setchannel`.
**NOTE** If you don't set up those channels, relevant functions might not work.
**Necessary**
GeckoUPD   - The channel to follow #gecko-upd from [Gecko Community](https://discord.gg/wNTaaBZ5qd) where updates / maintenance schedules are published.
Error      - Where important error notifications will be sent. (This should be rare)
**Optional**
Four       - Where players will play connect four games.
Finance    - Where players will play finance games.
Music      - Where players will request for songs. If you don't set this up, only staff will be allowed to play music.
             If you want the bot to stick to a radio station and not being interrupted, then you don't need to set it.
             *A bot can only be in one voice channel at the same time*
Level      - Where level updates will be posted. 
             If not set, levels will still be counted but updates will not be posted.
Suggestion - Where suggestions will be posted and voted.
**Optional (for staff)**
Form       - Where notifications will be sent when a user submit an entry. 
             If not set, forms will still be accepted but updates will not be posted.
             You can retrieve en entry with `/form entry`.
EventLog   - Where server events (messages / members etc) will be logged.
BotLog     - Where bot audit log will be sent.
**NOTE** 
1.For four, finance and music, you can set channel to "all" so that player can use relevant commands in any channels.
2.For level, if you set channel to "all", the level update will be posted at the channel where the user sent the last message before upgrading.
3.If the channel got deleted, it will be considered as that the channel hasn't been set up. And users cannot use relevant commands."""

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
async def SetChannel(ctx, category: discord.Option(str, "The category of message.", required = True, choices = ["GeckoUPD", "Error", "Four", "Finance", "Music", "Level", "Suggestion", "Form", "EventLog", "BotLog"]),
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

    category = category.lower()

    if not category in ["geckoupd", "error", "four", "finance", "music", "level", "suggestion", "form", "eventlog", "botlog"]:
        await ctx.respond(f"{category} is not a valid category.", ephemeral = True)
        return

    if remove == "Yes":
        if category == "geckoupd":
            await ctx.respond(f"Gecko does not support unfollowing channel, please go to **Server Settings** - **Integrations**")
            return

        cur.execute(f"DELETE FROM channelbind WHERE guildid = {guild.id} AND category = '{category}'")
        conn.commit()
        await ctx.respond(f"{category} channel bind removed.")
    else:
        if category in ["four", "finance", "music", "level"] and channel == "all":
            channel = 0
        else:
            if category == "geckoupd":
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
            await ctx.respond(f"<#{channel}> has been configured as {category} channel.")
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

@bot.slash_command(name="dm", description="DM a member through Gecko. Your message will be forwarded in embed.")
async def dm(ctx, user: discord.Option(discord.User, "Member to DM, must be in this guild", required = True),
        msg: discord.Option(str, "Message to be sent to the member", required = True),
        showauthor: discord.Option(str, "Show your name on the message, default Yes", required = False, choices = ["Yes", "No"])):
    
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
    
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return
    
    if user.bot:
        await ctx.respond("You can't DM bots.", ephemeral = True)
        return
    
    if user.id == bot.user.id:
        await ctx.respond("You can't DM me.", ephemeral = True)
        return
    
    if ctx.guild.get_member(user.id) is None:
        await ctx.respond(f"{user} is not in this guild.", ephemeral = True)
        return

    if msg != None:
        msg = msg.replace("\\n","\n")
    
    try:
        channel = await user.create_dm()
        if channel is None:
            await ctx.respond(f"I cannot DM the member", ephemeral = True)
            return
        embed=discord.Embed(title=f"Message from staff of {ctx.guild.name}", description=msg, color=GECKOCLR)
        if showauthor == "Yes":
            avatar = ""
            if ctx.author.avatar != None:
                avatar = ctx.author.avatar.url
            embed.set_author(name=ctx.author.name, icon_url=avatar)
        await channel.send(embed = embed)
        await ctx.respond(f"DM sent", ephemeral = True)
    except:
        import traceback
        traceback.print_exc()
        await ctx.respond(f"I cannot DM the member", ephemeral = True)

@bot.slash_command(name="transcript", description="Create a transcript of the channel")
async def transcript(ctx, channel: discord.Option(discord.TextChannel, "Channel to create transcript, default the channel where command is executed", required = False),
        limit: discord.Option(int, "Message limit, limitted by premium tier", required = False)):
    await ctx.defer()
    if ctx.guild is None:
        await ctx.respond(f"You can only use this command in guilds, not in DMs.")
        return
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    if channel is None:
        channel = ctx.channel

    premium = GetPremium(ctx.guild)
    if limit != None:
        if limit >= 300 and premium >= 2:
            await ctx.respond("Max transcript messages: 300.\n\nThis cannot be increased as it will dramatically slow down the bot.", ephemeral = True)
            return
        elif limit >= 150 and premium == 1:
            await ctx.respond("Premium Tier 1: 150 transcript messages.\nPremium Tier 2: 300 transcript messages.\n\nFind out more by using `/premium`", ephemeral = True)
            return
        elif limit >= 50 and premium == 0:
            await ctx.respond("Free guilds: 50 transcript messages.\nPremium Tier 1: 150 transcript messages.\nPremium Tier 2: 300 transcript messages.\n\nFind out more by using `/premium`", ephemeral = True)
            return
    else:
        if premium == 0:
            limit = 50
        elif premium == 1:
            limit = 150
        elif premium == 2:
            limit = 300

    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM settings WHERE skey = 'transcript' AND guildid = {ctx.guild.id}")
    t = cur.fetchall()
    if len(t) > 0:
        await ctx.respond("Gecko can create transcript of only one channel at the same time.", ephemeral = True)
        return
    cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 'transcript', 0)")
    conn.commit()

    try:
        data = await chat_exporter.export(channel, limit = limit)
        data = minify_html.minify(data, minify_js=True, minify_css=True, remove_processing_instructions=True, remove_bangs=True)
    except:
        import traceback
        traceback.print_exc()
        await ctx.respond("I cannot create transcript. Make sure I have read_message_history permission.", ephemeral = True)
        cur.execute(f"DELETE FROM settings WHERE skey = 'transcript' AND guildid = {ctx.guild.id}")
        conn.commit()
        return
    await ctx.respond(content=f"Transcript of {channel.name} created by {ctx.author.name}#{ctx.author.discriminator}", file=discord.File(io.BytesIO(data.encode()), filename=f"transcript-{channel.name}.html"))

    cur.execute(f"DELETE FROM settings WHERE skey = 'transcript' AND guildid = {ctx.guild.id}")
    conn.commit()