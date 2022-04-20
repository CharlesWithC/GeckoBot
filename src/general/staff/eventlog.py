# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Event Log Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands

from bot import bot
from settings import *
from functions import *
from db import newconn

EVENTS = ["message_delete", "bulk_message_delete", "message_edit",
    "guild_channel_create", "guild_channel_delete", 
    "member_join", "member_remove", "member_update", "member_ban", "member_unban",
    "invite_create"]

econn = newconn() # event conn
@bot.event
async def on_message_delete(message):
    if message.guild is None:
        return
    if message.author.id == BOTID or message.author.bot == True:
        return
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()

    if message.author.id == BOTID:
        return

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {message.guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "message_delete" in events:
        return
        
    guildid = message.guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        channel = bot.get_channel(t[0][0])
        if channel != None:
            try:
                embeds = []
                files = []
                embed = discord.Embed(title=f"#{message.channel}", description=message.content, color = GECKOCLR)
                icon_url = None
                if not message.author.avatar is None:
                    icon_url = message.author.avatar.url
                embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=icon_url)
                embed.set_footer(text=f"Event: message_delete", icon_url = GECKOICON)
                embeds.append(embed)

                tot = len(message.attachments)
                for i in range(0, tot):
                    isimage = message.attachments[i].content_type.startswith("image")
                    if isimage:
                        embed = discord.Embed(title=f"#{message.channel}", description=f"*Message {message.id} Attachment*", color = GECKOCLR)
                        icon_url = None
                        if not message.author.avatar is None:
                            icon_url = message.author.avatar.url
                        embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=icon_url)
                        embed.set_image(url=message.attachments[i].url)
                        embed.set_footer(text=f"Event: message_delete", icon_url = GECKOICON)
                        embeds.append(embed)
                    else:
                        response = requests.get(message.attachments[i].url)
                        data = io.BytesIO(response.content)
                        files.append(discord.File(data, filename = f"Message-{message.id}-Attachment-{i+1}-"+message.attachments[i].filename))

                await channel.send(embeds = embeds, files = files)
            except:
                import traceback
                traceback.print_exc()
                pass

@bot.event
async def on_bulk_message_delete(messages):
    if messages[0].guild is None:
        return
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {messages[0].guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "bulk_message_delete" in events:
        return
        
    guildid = messages[0].guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        channel = bot.get_channel(t[0][0])
        if channel != None:
            msg = ""
            embeds = []
            files = []
            for message in messages:
                if message.author.id == BOTID or message.author.bot == True:
                    continue
                try:
                    if len(embeds) == 10 or len(files) == 10:
                        await channel.send(embeds = embeds, files = files)
                        embeds = []
                        files = []

                    if len(msg + f"**{message.author}** (`{message.author.id}`): {message.content}\n\n") > 2000:
                        embed = discord.Embed(title=f"#{message.channel}", description=msg, color = GECKOCLR)
                        embed.set_footer(text=f"Event: bulk_message_delete", icon_url = GECKOICON)
                        embeds.append(embed)
                        msg = ""
                    
                    if message.content != None and message.content != "":
                        msg += f"**{message.author}** (`{message.author.id}`): {message.content}\n\n"

                    tot = len(message.attachments)
                    for i in range(0, tot):
                        if len(embeds) == 10 or len(files) == 10:
                            await channel.send(embeds = embeds, files = files)
                            embeds = []
                            files = []
                        isimage = message.attachments[i].content_type.startswith("image")
                        if isimage:
                            embed = discord.Embed(title=f"#{message.channel}", description=f"*Message {message.id} Attachment*", color = GECKOCLR)
                            icon_url = None
                            if not message.author.avatar is None:
                                icon_url = message.author.avatar.url
                            embed.set_author(name=f"{message.author} ({message.author.id})", icon_url=icon_url)
                            embed.set_image(url=message.attachments[i].url)
                            embed.set_footer(text=f"Event: bulk_message_delete", icon_url = GECKOICON)
                            embeds.append(embed)
                        else:
                            response = requests.get(message.attachments[i].url)
                            data = io.BytesIO(response.content)
                            files.append(discord.File(data, filename = f"Message-{message.id}-Attachment-{i+1}-"+message.attachments[i].filename))
                except:
                    import traceback
                    traceback.print_exc()
                    pass

            if msg != "":
                embed = discord.Embed(title=f"#{message.channel}", description=msg, color = GECKOCLR)
                embed.set_footer(text=f"Event: bulk_message_delete", icon_url = GECKOICON)
                embeds.append(embed)

            if len(embeds) + len(files) > 0:
                await channel.send(embeds = embeds, files = files)

@bot.event
async def on_message_edit(before, after):
    if before.guild is None:
        return
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()
        
    if before.author.id == BOTID:
        return

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {before.guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "message_edit" in events:
        return
        
    guildid = before.guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        channel = bot.get_channel(t[0][0])
        if channel != None:
            try:
                url = f"https://discord.com/channels/{guildid}/{before.channel.id}/{before.id}"
                embed = discord.Embed(title=f"#{before.channel}", url=url, description=f"{before.content}", color = GECKOCLR)
                icon_url = None
                if not before.author.avatar is None:
                    icon_url = before.author.avatar.url
                embed.set_author(name=f"{before.author} ({before.author.id})", icon_url=icon_url)
                embed.set_footer(text=f"Event: message_edit", icon_url = GECKOICON)
                await channel.send(embed = embed)
            except:
                pass

@bot.event
async def on_guild_channel_create(channel):
    if channel.guild is None:
        return
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {channel.guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "guild_channel_create" in events:
        return
        
    guildid = channel.guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        chn = bot.get_channel(t[0][0])
        if chn != None:
            try:
                url = f"https://discord.com/channels/{guildid}/{channel.id}"
                embed = discord.Embed(title=f"#{channel}", url=url, description=f"Position: {channel.position}\nUnder **{channel.category}**", color = GECKOCLR)
                embed.set_footer(text=f"Event: guild_channel_create", icon_url = GECKOICON)
                await chn.send(embed = embed)
            except:
                pass

@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild is None:
        return
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {channel.guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "guild_channel_delete" in events:
        return
        
    guildid = channel.guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        chn = bot.get_channel(t[0][0])
        if chn != None:
            try:
                embed = discord.Embed(title=f"#{channel}", color = GECKOCLR)
                embed.set_footer(text=f"Event: guild_channel_delete", icon_url = GECKOICON)
                await chn.send(embed = embed)
            except:
                pass

@bot.event
async def on_member_update(before, after):
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()
    
    if before.id == BOTID:
        return

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {after.guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "member_update" in events:
        return
    
    if before.name == after.name and before.display_name == after.display_name and before.discriminator == after.discriminator:
        return
        
    guildid = after.guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        chn = bot.get_channel(t[0][0])
        if chn != None:
            try:
                embed = discord.Embed(title=f"{after}", description=f"<@{after.id}> ({after.id})", color = GECKOCLR)
                if before.name != after.name:
                    embed.add_field(name="Name", value=f"{before.name} -> {after.name}", inline=True)
                if before.discriminator != after.discriminator:
                    embed.add_field(name="Discriminator", value=f"{before.discriminator} -> {after.discriminator}", inline=True)
                if before.display_name != after.display_name:
                    embed.add_field(name="Display Name", value=f"{before.display_name} -> {after.display_name}", inline=True)
                embed.set_footer(text=f"Event: member_update", icon_url = GECKOICON)
                await chn.send(embed = embed)
            except:
                import traceback
                traceback.print_exc()
                pass

@bot.event
async def on_member_ban(guild, user):
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()

    if user.id == BOTID:
        return

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "member_ban" in events:
        return
        
    guildid = guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        chn = bot.get_channel(t[0][0])
        if chn != None:
            try:
                embed = discord.Embed(title=f"{user}", description=f"{user.id}", color = GECKOCLR)
                embed.set_footer(text=f"Event: member_ban", icon_url = GECKOICON)
                await chn.send(embed = embed)
            except:
                pass

@bot.event
async def on_member_unban(guild, user):
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()

    if user.id == BOTID:
        return

    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "member_unban" in events:
        return
        
    guildid = guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        chn = bot.get_channel(t[0][0])
        if chn != None:
            try:
                embed = discord.Embed(title=f"{user}", description=f"{user.id}", color = GECKOCLR)
                embed.set_footer(text=f"Event: member_unban", icon_url = GECKOICON)
                await chn.send(embed = embed)
            except:
                pass

@bot.event
async def on_invite_create(invite):
    global econn
    try:
        cur = econn.cursor()
    except:
        econn = newconn()
        cur = econn.cursor()


    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {invite.guild.id}")
    events = cur.fetchall()
    if len(events) == 0:
        return
    events = events[0][0]
    if not "invite_create" in events:
        return
        
    guildid = invite.guild.id
    cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
    t = cur.fetchall()
    if len(t) > 0:
        chn = bot.get_channel(t[0][0])
        if chn != None:
            try:
                channelurl = f"https://discord.com/channels/{invite.guild.id}/{invite.channel.id}/{invite.id}"
                expire = "Never"
                if invite.max_age != 0:
                    expire = f"<t:{int(time()+invite.max_age)}:R>"
                embed = discord.Embed(title=f"{invite.id}", url=invite.url, description=f"URL: {invite.url}\nChannel: [#{invite.channel}]({channelurl})\nExpire: {expire}", color = GECKOCLR)
                embed.set_footer(text=f"Event: invite_create", icon_url = GECKOICON)
                await chn.send(embed = embed)
            except:
                pass

@bot.slash_command(name="eventlog", description="Enable / Disable an event log")
async def eventlog(ctx, event: discord.Option(str, "Event", required = True, choices = EVENTS), 
        enable: discord.Option(str, "Enable / Disable", required = False, choices = ["Enable", "Disable"], default = "Enable")):
    
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
        
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()
    
    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {ctx.guild.id}")
    t = cur.fetchall()
    events = []
    if len(t) > 0:
        events = t[0][0].split(",")
    if enable == "Enable":
        if not event in events:
            events.append(event)
    else:
        if event in events:
            events.remove(event)
    events = ",".join(events)
    cur.execute(f"DELETE FROM eventlog WHERE guildid = {ctx.guild.id}")
    cur.execute(f"INSERT INTO eventlog VALUES ({ctx.guild.id}, '{events}')")
    conn.commit()

    await ctx.respond(f"Event {event} log has been {enable.lower()}d")

@bot.slash_command(name="logging", description="Show what events are being logged")
async def logging(ctx):
    if ctx.guild is None:
        await ctx.respond("You can only run this command in guilds!")
        return
        
    if not isStaff(ctx.guild, ctx.author):
        await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
        return

    conn = newconn()
    cur = conn.cursor()
    
    cur.execute(f"SELECT events FROM eventlog WHERE guildid = {ctx.guild.id}")
    t = cur.fetchall()
    events = []
    if len(t) > 0:
        events = t[0][0].split(",")
    if len(events) == 0:
        await ctx.respond("No events are being logged!")
        return
    msg = ""
    for event in events:
        msg += f":white_check_mark: {event}\n"
    for event in EVENTS:
        if not event in events:
            msg += f":x: {event}\n"
    embed = discord.Embed(title=f"Events", description=msg, color = GECKOCLR)
    embed.set_footer(text=f"Gecko Event Log", icon_url = GECKOICON)
    await ctx.respond(embed = embed)