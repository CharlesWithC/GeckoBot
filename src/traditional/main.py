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

from bot import tbot
from db import newconn
from settings import *
from functions import *

@tbot.command(name="user", description="Get user information")
async def getuser(ctx, user: discord.Member):
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
    embed = discord.Embed(title = f"{ctx.guild.name}", description=f"**Description**: {ctx.guild.description}", color = GECKOCLR)
    embed.add_field(name = "Owner", value = f"```{ctx.guild.owner}```", inline = True)
    embed.add_field(name = "Members", value = f"```{ctx.guild.member_count}```", inline = True)
    embed.add_field(name = "Roles", value = f"```{len(ctx.guild.roles)}```", inline = True)
    embed.add_field(name = "Categories", value = f"```{len(ctx.guild.categories)}```", inline = True)
    embed.add_field(name = "Text Channels", value = f"```{len(ctx.guild.text_channels)}```", inline = True)
    embed.add_field(name = "Voice Channels", value = f"```{len(ctx.guild.voice_channels)}```", inline = True)
    icon_url = None
    if not ctx.guild.icon is None:
        icon_url = ctx.guild.icon.url
    embed.set_thumbnail(url = icon_url)
    embed.set_author(name = f"{ctx.guild.name}", icon_url = icon_url)
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
    
    embed = discord.Embed(title="Gecko Stats", color=GECKOCLR)
    embed.set_thumbnail(url=BOT_ICON)
    embed.add_field(name="Total Servers", value=f"```{total_servers}```")
    embed.add_field(name="Total Users", value=f"```{total_users}```")
    embed.add_field(name="Total Channels", value=f"```{total_channels}```")
    embed.add_field(name="Ping", value=f"```{int(ping*1000)}ms```")
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

    if not category in ["form", "four", "finance", "music", "level", "error", "log", "deleted"]:
        await ctx.send(f"{category} is not a valid category.")
        return

    if category in ["four", "finance", "music", "level"] and channel == "all":
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