# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
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
        
class ManageStatsDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("stats_display", "Manage Server Statistics Display")
    
    @manage.command(name = "setup", description = "Staff - Set everything up automatically and configure it using a template.")
    async def setup(self, ctx):
        if ctx.guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return
        guildid = ctx.guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
            
        await ctx.trigger_typing()
        try:
            guild = ctx.guild

            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) > 0:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if not category is None:
                        await ctx.respond(f"{ctx.author.name}, it has already been set up before.", ephemeral = True)
                        return
                except:
                    await ctx.respond(f"{ctx.author.name}, it has already been set up before.", ephemeral = True)
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
                await category.set_permissions(me, manage_channels = True, manage_roles = True, connect = True)
                try:
                    dev = bot.get_user(BOTOWNER)
                    await category.set_permissions(dev, manage_channels = True, manage_roles = True, connect = True)
                except:
                    pass
                await category.set_permissions(ctx.guild.default_role, connect = False)
            except:
                pass

            await ctx.respond(f"{ctx.author.name}, stats display have been enabled. You can edit the category name, move channel & category order as you wish.")

            cur.execute(f"INSERT INTO serverstats VALUES ({guildid}, {category.id})")
            conf1 = b64encode(b"{time: %A, %b %-d}").decode()
            cur.execute(f"INSERT INTO statsconfig VALUES ({guildid}, {category.id}, {channel1.id}, '{conf1}')")
            conf2 = b64encode(b"{online} / {members} Online").decode()
            cur.execute(f"INSERT INTO statsconfig VALUES ({guildid}, {category.id}, {channel2.id}, '{conf2}')")
            conn.commit()
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} created stats display category and channels.", ctx.guild.id)
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} added stats channel with configuration {b64decode(conf1.encode()).decode()}.", ctx.guild.id)
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} added stats channel with configuration {b64decode(conf2.encode()).decode()}.", ctx.guild.id)

        except Exception as e:
            await ctx.respond(f"{ctx.author.name}, I either cannot create category / channel, or cannot change channel permissions. Make sure I have Manage Channels and Manage Roles permission.")
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] !create_stats_channels executed by {ctx.author.name} failed due to {str(e)}", ctx.guild.id)

    @manage.command(name = "create", description = "Staff - Create a new stats channel and configure it by yourself.")
    async def create(self, ctx, 
        config: discord.Option(str, "Variables: {time: [strftime]} {members} {online} {@role} {@role online}", required = True)):
        
        if ctx.guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return
        guildid = ctx.guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
            
        await ctx.trigger_typing()
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                return
            else:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if category is None:
                        await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                        return
                except:
                    await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                    return
            
            conf = config
            vrf = conf
            while vrf.find("{") != -1:
                var = vrf[vrf.find("{")+1 : vrf.find("}")]
                vrf = vrf[vrf.find("}")+1:]
                
                while var.startswith(" "):
                    var = var[1:]

                if var.startswith("time:"):
                    if not validateStrftime(var):
                        await ctx.respond(f"{ctx.author.name}, invalid strftime format: {var.repalce('time:','')}", ephemeral = True)
                        return

                if not var.startswith("time:") and var != "members" and var != "online":
                    var = var.split()
                    role = var[0]
                    if not role.startswith("<@&") or not role.endswith(">") or len(var) == 2 and var[1] != "online" or len(var) > 2:
                        await ctx.respond(f"{ctx.author.name}, invalid variable {{{var}}}.\nOnly `{{time: strftime format}}` `{{members}}` `{{online}}` `{{@role}}` `{{@role online}}` are accepted.", ephemeral = True)
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

            await ctx.respond(f"{ctx.author.name}, stats display channel has been created with configuration `{conf}`.")

            conf = b64encode(conf.encode()).decode()
            cur.execute(f"INSERT INTO statsconfig VALUES ({guildid}, {category.id}, {channel.id}, '{conf}')")
            conn.commit()
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} added stats channel with configuration {b64decode(conf.encode()).decode()}.", ctx.guild.id)
        
        except Exception as e:
            await ctx.respond(f"{ctx.author.name}, I either cannot create category / channel, or cannot change channel permissions. Make sure I have Manage Channels and Manage Roles permission.")
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] '/stats_display create' executed by {ctx.author.name} failed due to {str(e)}", ctx.guild.id)

    @manage.command(name = "edit", description = "Staff - Edit an existing stats channel.")
    async def edit(self, ctx, 
        channelid: discord.Option(str, "Channel ID of the stats channel to edit. You can enable Developer Mode to see it.", required = True),
        config: discord.Option(str, "Variables: {time: [strftime]} {members} {online} {@role} {@role online}", required = True)):

        if ctx.guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return
        guildid = ctx.guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
            
        await ctx.trigger_typing()
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                return
            else:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if category is None:
                        await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                        return
                except:
                    await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                    return
            
            try:
                channelid = int(channelid)
                channel = bot.get_channel(channelid)
                if channel is None:
                    await ctx.respond(f"{ctx.author.name}, cannot fetch channel `{channelid}`", ephemeral = True)
                    return
            except:
                await ctx.respond(f"{ctx.author.name}, cannot fetch channel `{channelid}`", ephemeral = True)
                return

            cur.execute(f"SELECT * FROM statsconfig WHERE guildid = {guild.id} AND categoryid = {category.id} AND channelid = {channelid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, channel `{channelid}` is not a stats channel.", ephemeral = True)
                return

            conf = config
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
                        await ctx.respond(f"{ctx.author.name}, invalid strftime format: {var.repalce('time:','')}", ephemeral = True)
                        return

                if not var.startswith("time:") or var != "members" and var != "online":
                    var = var.split()
                    role = var[0]
                    if not role.startswith("<@&") or not role.endswith(">") or len(var) == 2 and var[1] != "online" or len(var) > 2:
                        await ctx.respond(f"{ctx.author.name}, invalid variable {{{var}}}.\nOnly `{{time: strftime format}}` `{{members}}` `{{online}}` `{{@role}}` `{{@role online}}` are accepted.", ephemeral = True)
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
                        await ctx.respond(f"{ctx.author.name}, invalid strftime format: {var.repalce('time:','')}", ephemeral = True)
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
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} updated stats channel {channelid} configuration to {conf}.", ctx.guild.id)

            await channel.edit(name = chnname)

            await ctx.respond(f"{ctx.author.name}, stats display channel {channelid} configuration has been updated to `{conf}`.")
            
        except Exception as e:
            await log("ServerStats", f"Unknown exception: {str(e)}", ctx.guild.id)

    @manage.command(name = "remove", description = "Staff - Remove a stats channel.")
    async def remove(self, ctx,
        channelid: discord.Option(str, "Channel ID of the stats channel to edit. You can enable Developer Mode to see it.", required = True)):
        
        if ctx.guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return
        guildid = ctx.guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
            
        await ctx.trigger_typing()
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                return
            else:
                try:
                    categoryid = t[0][0]
                    category = bot.get_channel(categoryid)
                    if category is None:
                        await ctx.respond(f"{ctx.author.name}, the stats display channel does not exist and you cannot delete it", ephemeral = True)
                        return
                except:
                    if category is None:
                        await ctx.respond(f"{ctx.author.name}, the stats display channel does not exist and you cannot delete it", ephemeral = True)
                        return
                    return
            
            try:
                channelid = int(channelid)
                channel = bot.get_channel(channelid)
                if channel is None:
                    await ctx.respond(f"{ctx.author.name}, cannot fetch channel `{channelid}`", ephemeral = True)
                    return
            except:
                await ctx.respond(f"{ctx.author.name}, cannot fetch channel `{channelid}`", ephemeral = True)
                return

            cur.execute(f"SELECT * FROM statsconfig WHERE guildid = {guild.id} AND categoryid = {category.id} AND channelid = {channelid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, channel `{channelid}` is not a stats channel.", ephemeral = True)
                return

            cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guild.id} AND categoryid = {category.id} AND channelid = {channelid}")
            conn.commit()
            await channel.delete()
            await ctx.respond(f"{ctx.author.name}, stats display channel {channelid} deleted.")
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} deleted stats channel {channelid}", ctx.guild.id)

            cur.execute(f"SELECT * FROM statsconfig WHERE guildid = {guild.id}")
            if len(cur.fetchall()) == 0:
                cur.execute(f"DELETE FROM statsconfig serverstats WHERE guildid = {guild.id}")
                conn.commit()
                try:
                    await category.delete()
                    await ctx.respond(f"{ctx.author.name}, no stats display channel is left. Server stats category is deleted automatically.")
                    await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] Server stats category deleted automatically as no stats channel is left.", ctx.guild.id)
                except:
                    pass

        except Exception as e:
            await log("ServerStats", f"Unknown exception: {str(e)}", ctx.guild.id)

    @manage.command(name = "destroy", description = "Staff - Disable stats display for this server and delete bound category and channels.")
    async def destroy(self, ctx):
        if ctx.guild is None:
            await ctx.respond("You can only use this command in guilds, not in DMs.")
            return
        guildid = ctx.guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()
            
        await ctx.trigger_typing()
        try:
            guild = ctx.guild
            category = None
            cur.execute(f"SELECT categoryid FROM serverstats WHERE guildid = {guild.id}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, stats display isn't enabled.\nUse `/stats_display setup` to start.", ephemeral = True)
                return
            categoryid = t[0][0]

            cur.execute(f"SELECT channelid FROM statsconfig WHERE guildid = {guild.id}")
            t = cur.fetchall()
            for tt in t:
                try:
                    channel = bot.get_channel(tt[0])
                    await channel.delete()
                except:
                    pass
            try:
                category = bot.get_channel(categoryid)
                await category.delete()
            except:
                pass

            cur.execute(f"DELETE FROM statsconfig WHERE guildid = {guild.id}")
            cur.execute(f"DELETE FROM serverstats WHERE guildid = {guild.id}")
            conn.commit()

            await ctx.respond(f"{ctx.author.name}, stats display disabled and bound category and channels have been deleted.")
            await log("ServerStats", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author.name} disabled stats display function and deleted bound category and channels.", ctx.guild.id)
        
        except Exception as e:
            await log("ServerStats", f"Unknown exception: {str(e)}", ctx.guild.id)

bot.add_cog(ManageStatsDisplay(bot))

ss_get_channel_fail = []
async def StatsDisplayUpdate():
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
            
                await log("ServerStats", f"[{guild} ({guildid})] Server stats function for this server is closed as bot cannot access the server.", ctx.guild.id)
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

                    await log("ServerStats", f"[{guild} ({guildid})] Server stats channel {channelid} expired as bot cannot access the channel.", ctx.guild.id)  
                    try:
                        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'error'")
                        t = cur.fetchall()
                        if len(t) != 0:
                            errchannelid = t[0][0]
                            errchannel = bot.get_channel(errchannelid)
                            embed = discord.Embed(title=f"Staff Notice", description=f"Server stats channel `{channelid}` has expired as I cannot access it. Stats will no longer be updated.", color=0x0000DD)
                            await errchannel.send(embed=embed)
                    except Exception as e:
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

bot.loop.create_task(StatsDisplayUpdate())