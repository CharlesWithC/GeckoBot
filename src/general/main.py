# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# General Functions

import discord
import asyncio
import sys
from time import time

import general.staff.chat
import general.crypto
import general.dev
import general.help
import general.level
import general.music
import general.games.finance
import general.games.four
import general.staff.button
import general.staff.embed
import general.staff.eventlog
import general.staff.form
import general.staff.reaction_role
import general.staff.staff
import general.staff.stats_display
import general.staff.vcrecord

from bot import bot, shard
from db import newconn
from settings import *
from functions import *
from ad import UpdateAdStatus

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
Eventlog - Where server events (messages / members etc) will be logged.
Botlog   - Where bot audit log will be sent.
Error    - Where important error notifications will be sent. (This should be rare)
**NOTE** 
1.For four, finance and music, you can set channel to "all" so that player can use related commands in any channels.
2.For level, if you set channel to "all", the level update will be posted at the channel where the user sent the last message before upgrading.
3.If the channel got deleted, it will be considered as that the channel hasn't been set up. And users cannot use related commands.

Have a nice day!"""

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
    
    await guild.text_channels[0].send(f"Gecko's here!\nYou are suggested to check `/setup` and `/help`.")

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
            cur.execute(f"DELETE FROM {tt[0]} WHERE guildid = {guild.id}")
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
    icon_url = None
    if not ctx.guild.icon is None:
        icon_url = ctx.guild.icon.url
    embed.set_thumbnail(url = icon_url)
    embed.set_author(name = f"{ctx.guild.name}", icon_url = icon_url)
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
    embed.set_thumbnail(url=BOT_ICON)
    embed.add_field(name="Servers", value=f"```{total_servers}```")
    embed.add_field(name="Users", value=f"```{total_users}```")
    embed.add_field(name="Channels", value=f"```{total_channels}```")

    embed.add_field(name="Buttons", value=f"```{btncnt}```")
    embed.add_field(name="Forms", value=f"```{formcnt}```")
    embed.add_field(name="Embeds", value=f"```{embedcnt}```")
    
    embed.add_field(name="Shard", value=f"```{len(bot.shards)}```")
    embed.add_field(name="Ping", value=f"```{int(ping*1000)}ms```")

    embed.set_footer(text="Gecko", icon_url=BOT_ICON)
    await ctx.respond(embed=embed)

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

async def UpdateBotStatus():
    await bot.wait_until_ready()
    await asyncio.sleep(10)
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

@bot.slash_command(name="ping", description="Get the bot's ping to discord API.")
async def Ping(ctx):
    await ctx.respond(f"Pong! {int(bot.latency * 1000)}ms.")

@bot.slash_command(name="parse", description="Get original text message", guild_ids = [DEVGUILD])
async def ParseMsg(ctx, msg: discord.Option(str, "Message", required = True)):
    await ctx.respond(f"```{msg}```")
    
bot.loop.create_task(UpdateBotStatus())