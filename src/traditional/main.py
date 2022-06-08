# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio

import traditional.crypto
import traditional.dev
import traditional.help
import traditional.level
import traditional.music
import traditional.games.finance
import traditional.games.four

import os
from bot import bot, tbot, shard
from db import newconn
from settings import *
from functions import *
from time import time, sleep
from datetime import datetime

from io import BytesIO

import pyttsx3
import importlib

@tbot.command(name="user", description="Get user information")
async def getuser(ctx, user: discord.Member):
    guild = ctx.guild
    if guild is None:
        await ctx.send(f"You can only use this command in guilds, not in DMs.")
        return
    actv = "*No activity*"
    if user.activity != None and user.activity.name != None:
        actv = user.activity.name
    embed = discord.Embed(title = f"{user.name}#{user.discriminator}", description=f"**Activity**: {actv}", color = GECKOCLR)
    if not user.avatar is None:
        embed.set_thumbnail(url = user.avatar.url)
    if not user.banner is None:
        embed.set_image(url = user.banner.url)

    embed.add_field(name = "Status", value = f"{STATUS[str(user.status)]}", inline = False)

    embed.add_field(name = "Member Since", value = f"<t:{int(user.joined_at.timestamp())}>", inline = True)
    embed.add_field(name = "Account Creation", value = f"<t:{int(user.created_at.timestamp())}>", inline = True)
    if not user.premium_since is None:
        embed.add_field(name = "Boosting Since", value = f"<t:{int(user.premium_since.timestamp())}>", inline = True)
        
    roles = ""
    for role in user.roles:
        if role != user.guild.default_role:
            roles += f"<@&{role.id}> "
    embed.add_field(name = "Roles", value = roles, inline = False)

    embed.set_footer(text = f"ID: {user.id}")

    await ctx.send(embed = embed)

@tbot.command(name="server", description="Get server information")
async def getserver(ctx):
    guild = ctx.guild
    if guild is None:
        await ctx.send(f"You can only use this command in guilds, not in DMs.")
        return
    embed = discord.Embed(title = f"{ctx.guild.name}", description=f"**Description**: {ctx.guild.description}", color = GECKOCLR)
    embed.add_field(name = "Owner", value = f"```{ctx.guild.owner}```", inline = True)
    embed.add_field(name = "Members", value = f"```{ctx.guild.member_count}```", inline = True)
    embed.add_field(name = "Roles", value = f"```{len(ctx.guild.roles)}```", inline = True)
    embed.add_field(name = "Categories", value = f"```{len(ctx.guild.categories)}```", inline = True)
    embed.add_field(name = "Text Channels", value = f"```{len(ctx.guild.text_channels)}```", inline = True)
    embed.add_field(name = "Voice Channels", value = f"```{len(ctx.guild.voice_channels)}```", inline = True)
    if not ctx.guild.icon is None:
        icon_url = ctx.guild.icon.url
        embed.set_thumbnail(url = icon_url)
        embed.set_author(name = f"{ctx.guild.name}", icon_url = icon_url)
    else:
        embed.set_author(name = f"{ctx.guild.name}")
    embed.set_footer(text = f"ID: {ctx.guild.id} | Server Creation: {ctx.guild.created_at.strftime('%m/%d/%Y')}")
    await ctx.send(embed = embed)

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
    
    btncnt = 0
    formcnt = 0
    embedcnt = 0
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM button")
    btncnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM form")
    formcnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM embed")
    embedcnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM suggestion")
    suggestioncnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM ticketrecord")
    ticketreccnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM pollvote")
    pollvotecnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM truckersmp")
    tmpcnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM vtc")
    vtccnt = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM vtcbind")
    vtcbindcnt = cur.fetchone()[0]
    
    embed = discord.Embed(title="Gecko Stats", description="Shard refers to prefix command bot.", color=GECKOCLR)
    embed.set_thumbnail(url=GECKOICON)
    embed.add_field(name="Servers", value=f"```{total_servers}```")
    embed.add_field(name="Users", value=f"```{total_users}```")
    embed.add_field(name="Channels", value=f"```{total_channels}```")

    embed.add_field(name="Buttons", value=f"```{btncnt}```")
    embed.add_field(name="Forms", value=f"```{formcnt}```")
    embed.add_field(name="Embeds", value=f"```{embedcnt}```")

    embed.add_field(name="Suggestions", value=f"```{suggestioncnt}```")
    embed.add_field(name="Tickets", value=f"```{ticketreccnt}```")
    embed.add_field(name="Poll Votes", value=f"```{pollvotecnt}```")

    embed.add_field(name="TMP Players", value=f"```{tmpcnt}```")
    embed.add_field(name="Cached VTC", value=f"```{vtccnt}```")
    embed.add_field(name="Bound VTC", value=f"```{vtcbindcnt}```")

    embed.add_field(name="Shard", value=f"```{len(tbot.shards)}```")
    embed.add_field(name="Ping", value=f"```{int(ping*1000)}ms```")

    embed.set_footer(text="Gecko", icon_url=GECKOICON)
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

    category = category.lower()

    if not category in ["geckoupd", "error", "four", "finance", "music", "level", "suggestion", "form", "eventlog", "botlog"]:
        await ctx.send(f"{category} is not a valid category.")
        return

    if category in ["four", "finance", "music", "level"] and channel == "all":
        channel = 0
    else:
        if category == "geckoupd":
            try:
                if not channel.startswith("<#") or not channel.endswith(">"):
                    await ctx.send(f"{channel} is not a valid channel.")
                    return
                channel = int(channel[2:-1])
                channel = bot.get_channel(channel)
                if channel is None:
                    await ctx.send(f"Channel does not exist.")
                    return
                destination = bot.get_channel(ANNOUNCEMENT_CHANNEL[1])
                if destination is None:
                    await ctx.send(f"Channel to follow (Gecko Update Channel) does not exist, this should be fixed very soon.\nYou could join [**Gecko Community**]({SUPPORT}) and let us know.")
                    return
                await destination.follow(destination = channel)
            except:
                import traceback
                traceback.print_exc()
                await ctx.send(f"Something wrong happened.")
                return
            await ctx.send(f"<#{channel.id}> is now following **Gecko Update Channel**\nTo unfollow, please go to **Server Settings** - **Integrations**")
            return

        if not channel.startswith("<#") or not channel.endswith(">"):
            await ctx.send(f"{channel} is not a valid channel.")
            return
        channel = int(channel[2:-1])
        chn = bot.get_channel(channel)
        if chn is None:
            await ctx.send(f"{channel} is not a valid channel.")
            return
    cur.execute(f"SELECT * FROM channelbind WHERE guildid = {guild.id} AND category = '{category}'")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO channelbind VALUES ({guild.id}, '{category}', {channel})")
    else:
        cur.execute(f"UPDATE channelbind SET channelid = {channel} WHERE guildid = {guild.id} AND category = '{category}'")
    conn.commit()
    if channel != 0:
        await ctx.send(f"<#{channel}> has been configured as {category} channel.")
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

    try:
        await ctx.channel.purge(limit = count + 1)
    except:
        await ctx.send("I don't have permission to delete messages.")

@tbot.command(name="ping", description="Get the bot's ping to discord API.")
async def tping(ctx):
    await ctx.send(f"Pong! {int(tbot.latency * 1000)}ms.")

@tbot.command(name="parse", description="Get original text message", guild_ids = [DEVGUILD])
async def ParseMsg(ctx):
    if ctx.message.reference != None:
        message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if message != None:
            await message.reply(f"```{message.content}```", mention_author = False)
    if len(ctx.message.content.split(' ')) > 1:
        await ctx.reply(f"```{' '.join(ctx.message.content.split(' ')[1:])}```", mention_author = False)

@tbot.command(name="premium", description="Get Gecko Premium subscription status, and information about premium.")
async def Premium(ctx):
    await ctx.channel.trigger_typing()
    conn = newconn()
    cur = conn.cursor()

    current = f"**{ctx.guild.name}** is not subscribed Gecko Premium."
    cur.execute(f"SELECT tier, expire FROM premium WHERE guildid = {ctx.guild.id}")
    t = cur.fetchall()
    if len(t) > 0:
        tier = t[0][0]
        expire = t[0][1]
        if tier > 0:
            if expire > time():
                current = f"**{ctx.guild.name}**: Gecko Premium Tier **{tier}**.\nExpires on: {datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}"
            else:
                current = f"**{ctx.guild.name}**: **Expired** Gecko Premium Tier **{tier}**.\nExpired on: {datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}"

    embed = discord.Embed(title = "Gecko Premium", description = current, color = GECKOCLR)
    embed.add_field(name = "Buttons", value = "Free: **10**\nTier 1: **30**\nTier 2: **100**", inline = True)
    embed.add_field(name = "Embeds", value = "Free: **10**\nTier 1: **30**\nTier 2: **100**", inline = True)
    embed.add_field(name = "Forms", value = "Free: **5**\nTier 1: **30**\nTier 2: **50**", inline = True)
    embed.add_field(name = "Reaction Role (Messages)", value = "Free: **10**\nTier 1: **30**\nTier 2: **50**", inline = True)
    embed.add_field(name = "Voice Channel Recorder", value = "Free: **10 hours / month**\nTier 1: **30 hours / month**\nTier 2: **100 hours / month**", inline = True)
    embed.add_field(name = "Other", value = "Any Premium Tier: **Radio**, **Rank Card with image background**", inline = False)
    embed.add_field(name = "Note", value = f"Gecko is giving away **Free Premium** to the first 100 guilds!\nIf your guild isn't given premium ,join [support server]({SUPPORT}) and ask for it!", inline = False)

    embed.timestamp = datetime.now()
    embed.set_thumbnail(url = GECKOICON)
    embed.set_footer(text = f"Gecko Premium ", icon_url = GECKOICON)

    await ctx.send(embed = embed)