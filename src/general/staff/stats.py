# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from base64 import b64encode, b64decode
from time import strftime, gmtime

from bot import bot
from settings import *
from functions import *
from db import newconn

# Variables:
# {time: [strftime format]}
# {members}
# {online}
# {@role}
# {@role online}
        
@bot.command(name="create_stats_channels")
async def CreateStatsChannel(ctx):
    conn = newconn()
    cur = conn.cursor()
    isAdmin = False
    if ctx.message.author.id in ADMIN_USER_ID:
        isAdmin = True
    for role in ctx.message.author.roles:
        if role.id in ADMIN_ROLE_ID:
            isAdmin = True
    guildid = ctx.guild.id
    
    if not isAdmin:
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !create_stats_channels command")
        return
    
    async with ctx.typing():
        try:
            guild = ctx.guild

            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) > 0:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if not category is None:
                        await ctx.message.reply(f"{ctx.message.author.name}, the server stats category already exists and you cannot create again.")
                        return
                except:
                    import traceback
                    traceback.print_exc()
                    await ctx.message.reply(f"{ctx.message.author.name}, the server stats category already exists and you cannot create again.")
                    return

                cur.execute(f"DELETE FROM serverstats WHERE guildid = {guild.id}")
                cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guild.id}")
                conn.commit()

            category = await guild.create_category("Server Stats")
            await category.move(beginning = True)

            channel1 = await category.create_voice_channel(betterStrftime('%A, %b %-d'))
            online = 0
            for member in guild.members:
                if member.status != discord.Status.offline:
                    online += 1
            channel2 = await category.create_voice_channel(f"{online} / {len(guild.members)} Online")
            
            try:
                me = bot.get_user(BOTID)
                dev = bot.get_user(OWNER)
                await category.set_permissions(me, manage_channels = True, manage_roles = True, connect = True)
                await category.set_permissions(dev, manage_channels = True, manage_roles = True, connect = True)
                await category.set_permissions(ctx.guild.default_role, connect = False)
            except:
                import traceback
                traceback.print_exc()
                pass

            await ctx.message.reply(f"{ctx.message.author.name}, server stats category and channels have been created. You can edit the category name, move channel & category order as you wish.")

            cur.execute(f"INSERT INTO serverstats VALUES ({guildid}, {category.id})")
            conf1 = b64encode(b"{time: %A, %b %-d}").decode()
            cur.execute(f"INSERT INTO statsconfig VALUES ({guildid}, {category.id}, {channel1.id}, '{conf1}')")
            conf2 = b64encode(b"{online} / {members} Online").decode()
            cur.execute(f"INSERT INTO statsconfig VALUES ({guildid}, {category.id}, {channel2.id}, '{conf2}')")
            conn.commit()
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} created server stats category and channels.")
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} added stats channel with configuration {b64decode(conf1.encode()).decode()}.")
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} added stats channel with configuration {b64decode(conf2.encode()).decode()}.")

        except Exception as e:
            await ctx.message.reply(f"{ctx.message.author.name}, I either cannot create category / channel, or cannot change channel permissions. Make sure I have Manage Channels and Manage Roles permission.")
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] !create_stats_channels executed by {ctx.message.author.name} failed due to {str(e)}")

@bot.command(name="add_stats_channel")
async def AddStatsChannel(ctx):
    conn = newconn()
    cur = conn.cursor()
    isAdmin = False
    if ctx.message.author.id in ADMIN_USER_ID:
        isAdmin = True
    for role in ctx.message.author.roles:
        if role.id in ADMIN_ROLE_ID:
            isAdmin = True
    guildid = ctx.guild.id
    
    if not isAdmin:
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !add_stats_channel command")
        return
    
    async with ctx.typing():
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                return
            else:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if category is None:
                        await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                        return
                except:
                    import traceback
                    traceback.print_exc()
                    await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                    return
            
            if len(ctx.message.content.split(" ")) == 1:
                await ctx.message.reply(f"!add_stats_channel {{configuration}}\n`{{time: strftime format}}` `{{members}}` `{{online}}` `{{@role}}` `{{@role online}}` are accepted variables in configuration.")
                return
            
            conf = " ".join(ctx.message.content.split(" ")[1:])
            vrf = conf
            while vrf.find("{") != -1:
                var = vrf[vrf.find("{")+1 : vrf.find("}")]
                vrf = vrf[vrf.find("}")+1:]
                
                while var.startswith(" "):
                    var = var[1:]

                if var.startswith("time:"):
                    if not validateStrftime(var):
                        await ctx.message.reply(f"{ctx.message.author.name}, invalid strftime format: {var.repalce('time:','')}")
                        return

                if not var.startswith("time:") and var != "members" and var != "online":
                    var = var.split()
                    role = var[0]
                    if not role.startswith("<@&") or not role.endswith(">") or len(var) == 2 and var[1] != "online" or len(var) > 2:
                        await ctx.message.reply(f"{ctx.message.author.name}, invalid variable {{{var}}}.\nOnly `{{time: strftime format}}` `{{members}}` `{{online}}` `{{@role}}` `{{@role online}}` are accepted.")
                        return

            online = 0
            for member in guild.members:
                if member.status != discord.Status.offline:
                    online += 1

            chnname = conf
            chnname = chnname.replace("{members}", str(len(guild.members)))
            chnname = chnname.replace("{online}", str(online))
            tmp = chnname
            while tmp.find("{") != -1:
                var = tmp[tmp.find("{")+1 : tmp.find("}")]
                orgvar = var
                tmp = tmp[tmp.find("}")+1:]
                
                while var.startswith(" "):
                    var = var[1:]
                    
                if var.startswith("time:"):
                    var = var.replace("time: ","").replace("time:", "")
                    chnname = chnname.replace(f"{{{orgvar}}}", betterStrftime(var))
                elif var.startswith("<@&"):
                    cnt = 0
                    role = int(var[var.find("<@&") + 3 : var.find(">")])
                    mustonline = False
                    if var.find("online") != -1:
                        mustonline = True
                    for member in guild.members:
                        for r in member.roles:
                            if r.id == role:
                                if mustonline and member.status != discord.Status.offline:
                                    cnt += 1
                                elif not mustonline:
                                    cnt += 1
                    chnname = chnname.replace(f"{{{orgvar}}}", str(cnt))
            
            channel = await category.create_voice_channel(chnname)

            await ctx.message.reply(f"{ctx.message.author.name}, server stats channel has been created for configuration `{conf}`.")

            conf = b64encode(conf.encode()).decode()
            cur.execute(f"INSERT INTO statsconfig VALUES ({guildid}, {category.id}, {channel.id}, '{conf}')")
            conn.commit()
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} added stats channel with configuration {b64decode(conf.encode()).decode()}.")
        
        except Exception as e:
            await ctx.message.reply(f"{ctx.message.author.name}, I either cannot create category / channel, or cannot change channel permissions. Make sure I have Manage Channels and Manage Roles permission.")
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] !add_stats_channels executed by {ctx.message.author.name} failed due to {str(e)}")

@bot.command(name="edit_stats_channel")
async def EditStatsChannel(ctx):
    conn = newconn()
    cur = conn.cursor()
    isAdmin = False
    if ctx.message.author.id in ADMIN_USER_ID:
        isAdmin = True
    for role in ctx.message.author.roles:
        if role.id in ADMIN_ROLE_ID:
            isAdmin = True
    guildid = ctx.guild.id
    
    if not isAdmin:
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !edit_stats_channel command")
        return
    
    async with ctx.typing():
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                return
            else:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if category is None:
                        await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                        return
                except:
                    import traceback
                    traceback.print_exc()
                    await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                    return
            
            if len(ctx.message.content.split()) < 3:
                await ctx.message.reply(f"{ctx.message.author.name}, invalid command!\nUsage: !edit_stats_channel {{channel id}} {{new configuration}}\nEnable developer mode then you can copy channel id.")
                return
            
            channelid = int(ctx.message.content.split()[1])
            try:
                channel = bot.get_channel(channelid)
                if channel is None:
                    await ctx.message.reply(f"{ctx.message.author.name}, cannot fetch channel #{channelid} (`{channelid}`)")
                    return
            except:
                await ctx.message.reply(f"{ctx.message.author.name}, cannot fetch channel #{channelid} (`{channelid}`)")
                return

            cur.execute(f"SELECT * FROM statsconfig WHERE guildid = {guild.id} AND categoryid = {category.id} AND channelid = {channelid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.message.reply(f"{ctx.message.author.name}, channel #{channelid} (`{channelid}`) not bound to a server config.")
                return

            conf = " ".join(ctx.message.content.split(" ")[2:])

            online = 0
            for member in guild.members:
                if member.status != discord.Status.offline:
                    online += 1
            chnname = conf
            chnname = chnname.replace("{members}", str(len(guild.members)))
            chnname = chnname.replace("{online}", str(online))

            vrf = chnname
            while vrf.find("{") != -1:
                var = vrf[vrf.find("{")+1 : vrf.find("}")]
                vrf = vrf[vrf.find("}")+1:]
                
                while var.startswith(" "):
                    var = var[1:]

                if var.startswith("time:"):
                    if not validateStrftime(var):
                        await ctx.message.reply(f"{ctx.message.author.name}, invalid strftime format: {var.repalce('time:','')}")
                        return

                if not var.startswith("time:") or var != "members" and var != "online":
                    var = var.split()
                    role = var[0]
                    if not role.startswith("<@&") or not role.endswith(">") or len(var) == 2 and var[1] != "online" or len(var) > 2:
                        await ctx.message.reply(f"{ctx.message.author.name}, invalid variable {{{var}}}.\nOnly `{{time: strftime format}}` `{{members}}` `{{online}}` `{{@role}}` `{{@role online}}` are accepted.")
                        return

            tmp = chnname
            while tmp.find("{") != -1:
                var = tmp[tmp.find("{")+1 : tmp.find("}")]
                tmp = tmp[tmp.find("}")+1:]
                orgvar = var
                
                while var.startswith(" "):
                    var = var[1:]

                if var.startswith("time:"):
                    var = var.replace("time: ","").replace("time:", "")
                    if not validateStrftime(var):
                        await ctx.message.reply(f"{ctx.message.author.name}, invalid strftime format: {var.repalce('time:','')}")
                        return
                    chnname = chnname.replace(f"{{{orgvar}}}", betterStrftime(var))
                elif var.startswith("<@&"):
                    cnt = 0
                    role = int(var[var.find("<@&") + 3 : var.find(">")])
                    mustonline = False
                    if var.find("online") != -1:
                        mustonline = True
                    for member in guild.members:
                        for r in member.roles:
                            if r.id == role:
                                if mustonline and member.status != discord.Status.offline:
                                    cnt += 1
                                elif not mustonline:
                                    cnt += 1
                    chnname = chnname.replace(f"{{{orgvar}}}", str(cnt))
            
            cur.execute(f"UPDATE statsconfig SET conf = '{b64encode(conf.encode()).decode()}' WHERE guildid = {guildid} AND channelid = {channelid}")
            conn.commit()
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} updated stats channel {channel} ({channelid}) configuration to {b64decode(conf.encode()).decode()}.")

            await channel.edit(name = chnname)

            await ctx.message.reply(f"{ctx.message.author.name}, server stats channel <#{channelid}> (`{channelid}`) configuration has been updated to `{conf}`.")
            
        except Exception as e:
            await log("ServerStats", f"Unknown exception: {str(e)}")

@bot.command(name="delete_stats_channel")
async def DeleteStatsChannel(ctx):
    conn = newconn()
    cur = conn.cursor()
    isAdmin = False
    if ctx.message.author.id in ADMIN_USER_ID:
        isAdmin = True
    for role in ctx.message.author.roles:
        if role.id in ADMIN_ROLE_ID:
            isAdmin = True
    guildid = ctx.guild.id
    
    if not isAdmin:
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !delete_stats_channel command")
        return
    
    async with ctx.typing():
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                return
            else:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if category is None:
                        await ctx.message.reply(f"{ctx.message.author.name}, the server stats category doesn't exist and you cannot delete it")
                        return
                except:
                    import traceback
                    traceback.print_exc()
                    if category is None:
                        await ctx.message.reply(f"{ctx.message.author.name}, the server stats category doesn't exist and you cannot delete it")
                        return
                    return
            
            if len(ctx.message.content.split()) != 2:
                await ctx.message.reply(f"{ctx.message.author.name}, invalid command!\nUsage: !delete_stats_channels {{channel id}}\nEnable developer mode then you can copy channel id.")
                return
            
            channelid = int(ctx.message.content.split()[1])
            try:
                channel = bot.get_channel(channelid)
                if channel is None:
                    await ctx.message.reply(f"{ctx.message.author.name}, cannot fetch channel #{channelid} (`{channelid}`)")
                    return
            except:
                await ctx.message.reply(f"{ctx.message.author.name}, cannot fetch channel #{channelid} (`{channelid}`)")
                return

            cur.execute(f"SELECT * FROM statsconfig WHERE guildid = {guild.id} AND categoryid = {category.id} AND channelid = {channelid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.message.reply(f"{ctx.message.author.name}, channel #{channelid} (`{channelid}`) not bound to a server config.")
                return

            cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guild.id} AND categoryid = {category.id} AND channelid = {channelid}")
            conn.commit()
            await channel.delete()
            await ctx.message.reply(f"{ctx.message.author.name}, channel #{channelid} (`{channelid}`) deleted.")
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} deleted stats channel {channel} ({channelid})")

            cur.execute(f"SELECT * FROM statsconfig WHERE guildid = {guild.id}")
            if len(cur.fetchall()) == 0:
                cur.execute(f"DELETE FROM statsconfig serverstats WHERE guildid = {guild.id}")
                conn.commit()
                try:
                    await category.delete()
                    await ctx.message.reply(f"{ctx.message.author.name}, no server stats channel is left. Server stats category is deleted automatically.")
                    await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] Server stats category deleted automatically as no stats channel is left.")
                except:
                    pass

        except Exception as e:
            await log("ServerStats", f"Unknown exception: {str(e)}")

@bot.command(name="delete_all_stats_channels")
async def DeleteAllStatsChannels(ctx):
    conn = newconn()
    cur = conn.cursor()
    isAdmin = False
    if ctx.message.author.id in ADMIN_USER_ID:
        isAdmin = True
    for role in ctx.message.author.roles:
        if role.id in ADMIN_ROLE_ID:
            isAdmin = True
    guildid = ctx.guild.id
    
    if not isAdmin:
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !delete_all_stats_channels command")
        return
    
    async with ctx.typing():
        try:
            guild = ctx.guild
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.message.reply(f"{ctx.message.author.name}, server stats display isn't enabled for this server.\nUse `!create_stats_channels` to start out.")
                return
            categoryid = t[0][0]

            cur.execute(f"SELECT channelid FROM statsconfig WHERE guildid = {guild.id}")
            t = cur.fetchall()
            for tt in t:
                try:
                    channel = bot.get_channel(tt[0])
                    await channel.delete()
                except:
                    import traceback
                    traceback.print_exc()
                    pass
            try:
                category = bot.get_channel(categoryid)
                await category.delete()
            except:
                import traceback
                traceback.print_exc()
                pass

            cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guild.id}")
            cur.execute(f"DELETE FROM serverstats WHERE guildid = {guild.id}")
            conn.commit()

            await ctx.message.reply(f"{ctx.message.author.name}, all server stats channels and category as been deleted.")
            await log("ServerStats", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} deleted all server stats channel and category")
        
        except Exception as e:
            await log("ServerStats", f"Unknown exception: {str(e)}")

ss_get_channel_fail = []
async def ServerStats():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    while not bot.is_closed():
        cur.execute(f"SELECT guildid, categoryid FROM serverstats")
        d = cur.fetchall()
        for dd in d:
            guildid = dd[0]
            categoryid = dd[1]

            if ss_get_channel_fail.count((guildid, 0)) > 10:
                while ss_get_channel_fail.count((guildid, 0)) > 0:
                    ss_get_channel_fail.remove((guildid, 0))

                cur.execute(f"DELETE FROM serverstats WHERE guildid = {guildid}")
                cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guildid}")
                conn.commit()
            
                await log("ServerStats", f"[{guild} ({guildid})] Server stats function for this server is closed as bot cannot access the server.")
                continue

            guild = None
            try:
                guild = bot.get_guild(guildid)
                if guild is None:
                    ss_get_channel_fail.append((guildid, 0))
                    continue
            except:
                ss_get_channel_fail.append((guildid, 0))
                continue

            cur.execute(f"SELECT channelid, conf FROM statsconfig WHERE guildid = {guildid} AND categoryid = {categoryid}")
            t = cur.fetchall()
            for tt in t:
                channelid = tt[0]
                conf = b64decode(tt[1].encode()).decode()

                if ss_get_channel_fail.count((guildid, channelid)) > 10:
                    while ss_get_channel_fail.count((guildid, channelid)) > 0:
                        ss_get_channel_fail.remove((guildid, channelid))
                    cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guildid} AND categoryid = {categoryid} AND channelid = {channelid}")
                    conn.commit()

                    try:
                        await log("ServerStats", f"[{guild} ({guildid})] Server stats channel {channelid} expired as bot cannot access the channel.")
                        adminchn = bot.get_channel(STAFF_CHANNEL[1])
                        embed = discord.Embed(title=f"Staff Notice", description=f"Server stats channel <#{channelid}> (`{channelid}`) has expired as I cannot access it. Stats will no longer be updated.", url=f"https://discord.com/channels/{guildid}/{channelid}", color=0x0000DD)
                        await adminchn.send(embed=embed)
                    except Exception as e:
                        await log("ServerStats", f"[{guild} ({guildid})] Server stats channel {channelid} expired as bot cannot access the channel. {str(e)}")
                        pass
                    continue

                channel = None

                try:
                    channel = bot.get_channel(channelid)
                    if channel is None:
                        ss_get_channel_fail.append((guildid, channelid))
                        continue
                except:
                    ss_get_channel_fail.append((guildid, channelid))
                    continue
                
                online = 0
                for member in guild.members:
                    if member.status != discord.Status.offline:
                        online += 1
                chnname = conf
                chnname = chnname.replace("{members}", str(len(guild.members)))
                chnname = chnname.replace("{online}", str(online))
                tmp = chnname
                while tmp.find("{") != -1:
                    var = tmp[tmp.find("{")+1 : tmp.find("}")]
                    orgvar = var
                    tmp = tmp[tmp.find("}")+1:]
                    while var.startswith(" "):
                        var = var[1:]
                    if var.startswith("time:"):
                        var = var.replace("time: ","").replace("time:", "")
                        chnname = chnname.replace(f"{{{orgvar}}}", betterStrftime(var))
                    elif var.startswith("<@&"):
                        cnt = 0
                        role = int(var[var.find("<@&") + 3 : var.find(">")])
                        mustonline = False
                        if var.find("online") != -1:
                            mustonline = True
                        for member in guild.members:
                            for r in member.roles:
                                if r.id == role:
                                    if mustonline and member.status != discord.Status.offline:
                                        cnt += 1
                                    elif not mustonline:
                                        cnt += 1
                        chnname = chnname.replace(f"{{{orgvar}}}", str(cnt))
                
                if chnname != channel.name:
                    channel = await channel.edit(name = chnname)
            
                await asyncio.sleep(0.5)

        await asyncio.sleep(60)

bot.loop.create_task(ServerStats())