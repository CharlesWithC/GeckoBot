# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio
import sys, os
from time import time
from datetime import datetime

import general.staff.chat
import general.crypto
import general.dev
import general.help
import general.level
import general.music
import general.poll
import general.suggestion
import general.translate
import general.vc
import general.games.finance
import general.games.four
import general.staff.main
import general.staff.button
import general.staff.embed
import general.staff.eventlog
import general.staff.form
import general.staff.reaction_role
import general.staff.staff
import general.staff.stats_display
import general.staff.ticket
import general.staff.vcrecord

from bot import bot, shard
from db import newconn
from settings import *
from functions import *
from ad import UpdateAdStatus

@bot.event
async def on_guild_join(guild):
    try:
        channel = bot.get_channel(GUILDUPD[1])
        await channel.send(f"**Join** {guild.name} (`{guild.id}`) - Owner: {str(guild.owner)}")
    except:
        import traceback
        traceback.print_exc()
        pass

    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM settings WHERE guildid = {guild.id} AND skey = 'block'")
    if cur.fetchone():
        try:
            channel = bot.get_channel(GUILDUPD[1])
            await channel.send(f"**Blocked** {guild.name} (`{guild.id}`) - Owner: {str(guild.owner)}")
        except:
            import traceback
            traceback.print_exc()
            pass
        await guild.text_channels[0].send(f"The guild has been blocked by Gecko Moderator.\nTo appeal the ban, join Gecko support server. You have to find the link on your own to show your will to get unblocked.")
        await guild.leave()
        return
    
    expire = 0
    tier = 1
    guildid = guild.id
    if len(bot.guilds) <= 100:
        expire = int(time())+6*30*86400
        try:
            await guild.text_channels[0].send(f"Gecko's here!\nYou are suggested to check `/setup` and `/help`.\n\nAs **{guild.name}** is within the first 100 guilds to invite **Gecko**, premium of 180 days is rewarded!")
        except:
            pass
    else:
        expire = int(time())+7*86400
        try:
            await guild.text_channels[0].send(f"Gecko's here!\nYou are suggested to check `/setup` and `/help`.\n\nPremium of one week is rewarded and you can try out all premium functions including custom rank card, voice channel recorder etc.")
        except:
            pass

    cur.execute(f"INSERT INTO premium VALUES ({guildid}, {tier}, {expire})")
    conn.commit()
    dt = datetime.fromtimestamp(expire)
    try:
        channel = bot.get_channel(GUILDUPD[1])
        await channel.send(f"**Premium** `{guildid}` Tier **{tier}** Expire **{datetime.fromtimestamp(expire).strftime('%Y-%m-%d')}** *Auto*")
    except:
        import traceback
        traceback.print_exc()
        pass

@bot.event
async def on_guild_remove(guild):
    try:
        channel = bot.get_channel(GUILDUPD[1])
        await channel.send(f"**Leave** {guild.name} (`{guild.id}`) - Owner: {str(guild.owner)}")
    except:
        import traceback
        traceback.print_exc()
        pass
    
    conn = newconn()
    cur = conn.cursor()
    blocked = False
    cur.execute(f"SELECT * FROM settings WHERE guildid = {guild.id} AND skey = 'block'")
    t = cur.fetchall()
    if len(t) > 0:
        blocked = True
    cur.execute(f"SELECT buttonid FROM button WHERE guildid = {guild.id}")
    t = cur.fetchall()
    for tt in t:
        try:
            cur.execute(f"DELETE FROM buttonview WHERE buttonid = {tt[0]}")
        except:
            pass
    cur.execute(f"SHOW TABLES")
    t = cur.fetchall()
    for tt in t:
        try:
            cur.execute(f"UPDATE {tt[0]} SET guildid = -{guild.id} WHERE guildid = {guild.id}")
        except:
            pass
    if blocked:
        cur.execute(f"INSERT INTO settings VALUES ({guild.id}, 'block', '1')")
    conn.commit()

@bot.slash_command(name="user", description="Get information of a user")
async def getuser(ctx, user: discord.Option(discord.User, "User", required = True)):
    guild = ctx.guild
    if guild is None:
        await ctx.respond(f"You can only use this command in guilds, not in DMs.")
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

    await ctx.respond(embed = embed)

@bot.slash_command(name="server", description="Get server information")
async def getserver(ctx):
    guild = ctx.guild
    if guild is None:
        await ctx.respond(f"You can only use this command in guilds, not in DMs.")
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
    await ctx.respond(embed = embed)

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
    
    embed = discord.Embed(title="Gecko Stats", description="Shard refers to slash command bot.", color=GECKOCLR)
    embed.set_thumbnail(url=GECKOICON)
    embed.add_field(name="Servers", value=f"```{total_servers}```")
    embed.add_field(name="Users", value=f"```{total_users}```")
    embed.add_field(name="Channels", value=f"```{total_channels}```")

    embed.add_field(name="Buttons", value=f"```{btncnt}```")
    embed.add_field(name="Forms", value=f"```{formcnt}```")
    embed.add_field(name="Embeds", value=f"```{embedcnt}```")
    
    embed.add_field(name="Shard", value=f"```{len(bot.shards)}```")
    embed.add_field(name="Ping", value=f"```{int(ping*1000)}ms```")

    embed.set_footer(text="Gecko", icon_url=GECKOICON)
    await ctx.respond(embed=embed)

async def UpdateBotStatus():
    await bot.wait_until_ready()
    while not bot.is_ready():
        await asyncio.sleep(3)
    while not bot.is_closed():
        conn = newconn()
        cur = conn.cursor()
        try:
            lastadupd = 0
            cur.execute(f"SELECT sval FROM settings WHERE skey = 'lastadupd'")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO settings VALUES (0, 'lastadupd', '0')")
                conn.commit()
            else:
                lastadupd = int(t[0][0])
            total_servers = len(bot.guilds)
            total_users = 0
            for guild in bot.guilds:
                total_users += len(guild.members)
            if sys.argv[0].find("test") == -1 and time()-lastadupd > 60*30:
                UpdateAdStatus(total_servers, len(bot.shards), total_users)
                cur.execute(f"UPDATE settings SET sval = '{int(time())}' WHERE skey = 'lastadupd'")
                conn.commit()

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
            
        except:
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)

@bot.slash_command(name="ping", description="Get the bot's ping to discord API.")
async def Ping(ctx):
    await ctx.respond(f"Pong! {int(bot.latency * 1000)}ms.")

@bot.slash_command(name="parse", description="Get original text message")
async def ParseMsg(ctx, msg: discord.Option(str, "Message", required = True)):
    await ctx.respond(f"```{msg}```")

@bot.slash_command(name="premium", description="Get Gecko Premium subscription status, and information about premium.")
async def Premium(ctx):
    await ctx.defer()
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
    embed.add_field(name = "Ticket", value = "Free: **3**\nTier 1: **15**\nTier 2: **50**", inline = True)
    embed.add_field(name = "Transcript (Messages)", value = "Free: **50**\nTier 1: **150**\nTier 2: **300**", inline = True)
    embed.add_field(name = "Reaction Role (Messages)", value = "Free: **10**\nTier 1: **30**\nTier 2: **50**", inline = True)
    embed.add_field(name = "Voice Channel Recorder", value = "Free: **10 hours / month**\nTier 1: **30 hours / month**\nTier 2: **100 hours / month**", inline = True)
    embed.add_field(name = "Other", value = "Any Premium Tier: **Radio**, **Rank Card with image background**, **TruckersMP VTC Online Member Update**", inline = False)
    embed.add_field(name = "Note", value = f"Gecko is giving away **Free Premium** to the first 100 guilds!\nIf your guild isn't given premium ,join [support server]({SUPPORT}) and ask for it!", inline = False)

    embed.timestamp = datetime.now()
    embed.set_thumbnail(url = GECKOICON)
    embed.set_footer(text = f"Gecko Premium ", icon_url = GECKOICON)

    await ctx.respond(embed = embed)

bot.loop.create_task(UpdateBotStatus())