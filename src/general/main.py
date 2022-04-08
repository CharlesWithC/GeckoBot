# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio

import general.staff.chat
import general.crypto
import general.dev
import general.help
import general.music
import general.games.finance
import general.games.four
import general.staff.button
import general.staff.embed
import general.staff.form
import general.staff.reaction_role
import general.staff.staff
import general.staff.stats_display
import general.staff.vcrecord

from bot import bot
from db import newconn
from settings import *
from functions import *

SETUP_MSG = """Gecko is a developing bot that can help you make your community better.
I'm ready to use slash commands and you type / to see a list of my commands.
Use /about for basic information about Gecko and /help for help.

You should set up dedicated channels for specific functions, tell me by using `/setchannel`.
Form    - Where notifications will be sent when a user submit an entry.
Four    - Where players will play connect four games.
Finance - Where players will play finance games.
Music   - Where players will request for songs. If you don't set this up, only staff will be allowed to play music.
          If you want the bot to stick to a radio station and not being interrupted, then do not set it.
          *A bot can only be in one voice channel at the same time*
Deleted - Where deleted messages will be posted
Log     - Where bot audit log will be sent.
Error   - Where important error notifications will be sent. (This should be rare)
**NOTE** 
1.For four, finance and music, you can set channel to "all" so that player can use related commands in any channels.
2.If the channel got deleted, it will be considered as that the channel hasn't been set up. And users cannot use related commands.

Have a nice day!"""

@bot.event
async def on_guild_join(guild):
    try:
        channel = await guild.owner.create_dm()
        await channel.send(f"Hi, {guild.owner.name}\n" + SETUP_MSG)
    except:
        await guild.text_channels[0].send(f"Gecko's here!\n<@{guild.owner.id}>, it seems I cannot DM you. Please allow that and there's something necessary to tell you! After that send !setup and I'll resend the DM.")
        return

@bot.slash_command(name="gstats", description="Gecko Bot Stats")
async def stats(ctx):
    # total servers and total users
    total_servers = len(bot.guilds)
    total_users = 0
    total_channels = 0
    for guild in bot.guilds:
        total_users += len(guild.members)
        total_channels += len(guild.text_channels)
    ping = bot.latency
    
    embed = discord.Embed(title="Gecko Stats", color=GECKOCLR)
    embed.set_thumbnail(url=BOT_ICON)
    embed.add_field(name="Total Servers", value=total_servers)
    embed.add_field(name="Total Users", value=total_users)
    embed.add_field(name="Total Channels", value=total_channels)
    embed.add_field(name="Ping", value=f"{int(ping*1000)}ms")
    embed.set_footer(text="Gecko", icon_url=BOT_ICON)
    await ctx.respond(embed=embed)

@bot.slash_command(name="setup", description="Server Owner - A DM to server owner about Gecko's basic information.")
async def BotSetup(ctx):
    await ctx.defer()
    guild = ctx.guild
    if not guild is None:
        try:
            if ctx.author.id != guild.owner.id:
                return
            channel = await guild.owner.create_dm()
            await channel.send(f"Hi, {guild.owner.name}\n" + SETUP_MSG)
            await ctx.respond(f"Check your DM")
        except:
            await ctx.respond(f"I still cannot DM you")
    else:
        await ctx.respond(f"Hi, {ctx.author.name}\n" + SETUP_MSG)

@bot.slash_command(name="setchannel", description="Staff - Set default channels where specific messages will be dealt with.")
async def SetChannel(ctx, category: discord.Option(str, "The category of message.", required = True, choices = ["form", "four", "finance", "music", "deleted", "log", "error"]),
    channel: discord.Option(str, "Channel for messages, type 'all' for four / finance / music to allow all channels", required = True)):
    
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

    if not category in ["form", "four", "finance", "music", "error", "log", "deleted"]:
        await ctx.respond(f"{category} is not a valid category.", ephemeral = True)
        return

    if category in ["four", "finance", "music"] and channel == "all":
        channel = 0
    else:
        if not channel.startswith("<#") or not channel.endswith(">"):
            await ctx.respond(f"{channel} is not a valid channel.", ephemeral = True)
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
        await ctx.respond(f"<#{channel}> has been configured as {category} channel.\nMake sure I always have access to it.\nUnless you want to stop dealing with those messages, then delete the channel.")
    else:
        await ctx.respond(f"Members can use {category} commands in any channels.")

async def UpdateBotStatus():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    while 1:
        cur.execute(f"SELECT sval FROM settings WHERE skey = 'status' AND guildid = 0")
        t = cur.fetchall()
        status = "[Gaming] with Charles"
        if len(t) > 0:
            status = b64d(t[0][0])
        if status.startswith("[Gaming]"):
            await bot.change_presence(activity=discord.Game(name = status[9:]))
        elif status.startswith("[Streaming]"):
            await bot.change_presence(activity=discord.Streaming(name = status[12:].split("|")[0], url = status.split("|")[1]))
        elif status.startswith("[Listening]"):
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=status[12:]))
        elif status.startswith("[Watching]"):
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status[11:]))
        await asyncio.sleep(60)

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

    await ctx.channel.purge(limit = count, reason = "Gecko Channel Purge by " + ctx.author.name)

@bot.slash_command(name="ping", description="Get the bot's ping to discord API.")
async def Ping(ctx):
    await ctx.respond(f"Pong! {int(bot.latency * 1000)}ms.")
    
bot.loop.create_task(UpdateBotStatus())