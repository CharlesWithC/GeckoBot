# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Chat Action Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from datetime import datetime
import requests, io
from random import randint

from bot import bot
from settings import *
from functions import *
from db import newconn

class ManageChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("chat", "Manage chat action")
    
    @manage.command(name = "add", description = "Staff - Add Gecko's action when detected keyword in message.")
    async def add(self, ctx, keywords: discord.Option(str, "Keywords / Phrases, split with ','. Use '[join / leave]' for member join / leave actions.", required = True),
        action: discord.Option(str, "Gecko's action, if set to react, the reaction emoji will be needed", required = True, choices = ["delete", "timeout", "kick", "ban", "react", "message", "embed", "role"]),
        emoji: discord.Option(str, "Reaction emoji, required only when action is 'react'", required = False),
        content: discord.Option(str, "Message content, required only when action is 'message'", required = False),
        embedid: discord.Option(int, "Embed ID, required only when action is 'embed'", required = False),
        role: discord.Option(str, "Role to be given to user, startwith '-' to remove from user", required = False),
        channel: discord.Option(discord.TextChannel, "Channel to send hello / goodbye message, required only when keyword is [join / leave]", required = False)):

        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        conn = newconn()
        cur = conn.cursor()

        botuser = guild.get_member(BOTID)

        keywords=keywords.replace("|","")

        if action == "delete":
            if not botuser.guild_permissions.manage_messages:
                await ctx.respond("I don't have permission to delete messages.", ephemeral = True)
                return            

        elif action == "timeout":
            if not botuser.guild_permissions.moderate_members:
                await ctx.respond("I don't have permission to timeout members.", ephemeral = True)
                return

        elif action == "kick":
            if not botuser.guild_permissions.kick_members:
                await ctx.respond("I don't have permission to kick members.", ephemeral = True)
                return
        
        elif action == "ban":
            if not botuser.guild_permissions.ban_members:
                await ctx.respond("I don't have permission to ban members.", ephemeral = True)
                return
        
        elif action == "react":
            if not botuser.guild_permissions.add_reactions:
                await ctx.respond("I don't have permission to add reactions.", ephemeral = True)
                return
            if emoji is None or emoji == "":
                await ctx.respond("Reaction emoji is required as action is 'react'", ephemeral = True)
                return
            channel = ctx.channel
            message = await channel.send("Reaction test")
            try:
                await message.add_reaction(emoji)
                await message.delete()
            except:
                await ctx.respond(f"I cannot add reaction {emoji}. Make sure it's a valid emoji.", ephemeral = True)
                await message.delete()
                return
        
        elif action == "message":
            if content is None:
                await ctx.respond("Message content is required as action is 'message'", ephemeral = True)
                return
            if len(content) > 1000:
                await ctx.respond("Message content too long, it can be at most 1000 characters.", ephemeral = True)
                return
        
        elif action == "embed":
            if embedid is None:
                await ctx.respond("Embed ID is required as action is 'embed'", ephemeral = True)
                return
            cur.execute(f"SELECT * FROM embed WHERE embedid = {embedid} AND guildid = {guildid}")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond("Embed not found or does not belong to this guild.", ephemeral = True)
                return

        elif action == "role":
            if role is None:
                await ctx.respond("Role is required as action is 'role'", ephemeral = True)
                return
            if not botuser.guild_permissions.manage_roles:
                await ctx.respond("I don't have permission to manage roles.", ephemeral = True)
                return
            trole = role.replace(" ","").replace("-","")
            if not trole.startswith("<@&") or not trole.endswith(">"):
                await ctx.respond("Role must be a valid role mention.", ephemeral = True)
                return
            if "-" in role:
                role = -int(trole[3:-1])
            else:
                role = int(trole[3:-1])

        else:
            await ctx.respond("Invalid action!", ephemeral = True)
            return
        
        cur.execute(f"SELECT keywords FROM chataction WHERE guildid = {guildid} AND action = '{action}'")
        t  = cur.fetchall()
        existing = ""
        if len(t) > 0:
            existing = b64d(t[0][0]).split(",")
        else:
            cur.execute(f"INSERT INTO chataction VALUES ({guildid}, '', '{action}')")
        current = keywords.split(",")
        newone = ",".join(existing) + ","

        if "[leave]" in current or "[join]" in current:
            if role is None and not action in ["timeout", "kick", "ban"]:
                if channel is None:
                    await ctx.respond("Channel is required for `on member join / leave` action", ephemeral = True)
                    return
                if content is None and embedid is None:
                    await ctx.respond("Either message content or embed is required for `on member join / leave` action", ephemeral = True)
                    return
                if "[leave]" in current:
                    idx = current.index("[leave]")
                    current[idx] = current[idx] + "-" + str(channel.id)
                if "[join]" in current:
                    idx = current.index("[join]")
                    current[idx] = current[idx] + "-" + str(channel.id)

        for d in current:
            if not d in existing:
                if action == "react":
                    newone += d.lower().strip() + "|" + emoji + ","
                elif action == "message":
                    newone += d.lower().strip() + "|" + b64e(content) + ","
                elif action == "embed":
                    newone += d.lower().strip() + "|" + str(embedid) + ","
                elif action == "role":
                    newone += d.lower().strip() + "|" + str(role) + ","
                else:
                    newone += d.strip() + ","
        newone = newone.split(",")
        while newone.count("") > 0:
            newone.remove("")
        newone = list(dict.fromkeys(newone))
        newone = ",".join(newone)
        
        cur.execute(f"UPDATE chataction SET keywords = '{b64e(newone)}' WHERE guildid = {guildid} AND action = '{action}'")
        conn.commit()

        await ctx.respond(f"Chat action {action} for {keywords} added.")
        await log("Chat", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} added chat action {action} for {keywords}")

    @manage.command(name = "list", description = "Staff - List keywords Gecko will act on.")
    async def show(self, ctx,
        action: discord.Option(str, "Gecko's action, if set to react, the reaction emoji will be needed", choices = ["delete", "timeout", "kick", "ban", "react", "message", "embed", "role"])):

        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if not action in ["delete", "timeout", "kick", "ban", "react", "message", "embed", "role"]:
            await ctx.respond(f"Invalid action {action}.", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT keywords FROM chataction WHERE guildid = {guildid} AND action = '{action}'")
        t  = cur.fetchall()
        if len(t) == 0 or t[0][0] == "":
            await ctx.respond(f"No action found.", ephemeral = True)
            return
        msg = ""
        if action in ["timeout", "kick", "ban"]:
            msg = "When keywords below are found in messages: \n```"
            d = b64d(t[0][0]).split(",")
            for i in range(len(d)):
                if d[i].startswith("[join]-"):
                    d[i] = "[join]"
                d[i] = d[i].strip()
            msg += ", ".join(d)
            msg += f"```Gecko will **{action}** the author."
        elif action == "delete":
            msg = "When keywords below are found in messages: \n```"
            d = b64d(t[0][0]).split(",")
            for i in range(len(d)):
                if d[i].startswith("[join]-"):
                    d[i] = "[join]"
                d[i] = d[i].strip()
            msg += ", ".join(d)
            msg += f"```Gecko will **delete** the message."
        elif action == "role":
            d = {}
            t = b64d(t[0][0]).split(",")
            for tt in t:
                kw = tt.split("|")[0].strip()
                if kw.startswith("[join]-"):
                    kw = "[join]"
                if kw.startswith("[leave]-"):
                    kw = "[leave]"
                content = tt.split("|")[1]
                if not content in d.keys():
                    d[content] = [kw]
                else:
                    d[content].append(kw)
            msg = "Gecko will add / remove those roles when those keywords are found in messages:\n\n"
            for t in d.keys():
                if int(t) > 0:
                    msg += f"Add <@&{t}> : `{', '.join(d[t])}`\n"    
                else:
                    msg += f"Remove <@&{-int(t)}> : `{', '.join(d[t])}`\n"     
        elif action == "message":
            d = {}
            t = b64d(t[0][0]).split(",")
            for tt in t:
                kw = tt.split("|")[0].strip()
                if kw.startswith("[join]-"):
                    kw = "[join]"
                if kw.startswith("[leave]-"):
                    kw = "[leave]"
                content = tt.split("|")[1]
                if not b64d(content) in d.keys():
                    d[b64d(content)] = [kw]
                else:
                    d[b64d(content)].append(kw)
            msg = "Gecko will send those messages when those keywords are found in messages:\n\n"
            for t in d.keys():
                msg += f"**{', '.join(d[t])}**: `{t}`\n"
        elif action == "embed":
            d = {}
            t = b64d(t[0][0]).split(",")
            for tt in t:
                kw = tt.split("|")[0].strip()
                if kw.startswith("[join]-"):
                    kw = "[join]"
                if kw.startswith("[leave]-"):
                    kw = "[leave]"
                content = tt.split("|")[1]
                if not content in d.keys():
                    d[content] = [kw]
                else:
                    d[content].append(kw)
            msg = "Gecko will send those embeds when those keywords are found in messages:\n\n"
            for t in d.keys():
                msg += f"**Embed #{t}**: `{', '.join(d[t])}`\n"
        elif action == "react":
            d = {}
            t = b64d(t[0][0]).split(",")
            for tt in t:
                kw = tt.split("|")[0].strip()
                if kw.startswith("[join]-"):
                    kw = "[join]"
                if kw.startswith("[leave]-"):
                    kw = "[leave]"
                emoji = tt.split("|")[1]
                if not emoji in d.keys():
                    d[emoji] = [kw]
                else:
                    d[emoji].append(kw)
            msg = "Gecko will react those emojis when those keywords are found in messages:\n\n"
            for t in d.keys():
                msg += f"{t}: `{', '.join(d[t])}`\n"
        
        if len(msg) > 2000:
            f = io.BytesIO()
            f.write(msg.encode())
            f.seek(0)
            await ctx.respond(file=discord.File(fp=f, filename='ChatAction.MD'))
        else:
            await ctx.respond(msg)

    @manage.command(name = "remove", description = "Staff - Remove Gecko's action when detected keyword in message.")
    async def remove(self, ctx, keywords: discord.Option(str, "Keywords, split with ','"),
        action: discord.Option(str, "Gecko's action, if set to react, the reaction emoji will be needed", choices = ["delete", "timeout", "kick", "ban", "react", "message", "embed", "role"])):

        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
            
        keywords=keywords.replace("|","")

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT keywords FROM chataction WHERE guildid = {guildid} AND action = '{action}'")
        t  = cur.fetchall()
        existing = ""
        if len(t) > 0:
            existing = b64d(t[0][0]).split(",")
            for i in range(len(existing)):
                existing[i] = existing[i].strip()
                if existing[i].startswith("[join]-"):
                    existing[i] = "[join]"
                elif existing[i].startswith("[leave]-"):
                    existing[i] = "[leave]"
        toremove = keywords.lower().split(",")
        for i in range(len(toremove)):
            toremove[i] = toremove[i].strip()
        newone = ""
        for d in existing:
            if not d.split("|")[0] in toremove:
                newone += d + ","
        newone = newone.split(",")
        while newone.count("") > 0:
            newone.remove("")
        newone = list(dict.fromkeys(newone))
        newone = ",".join(newone)

        cur.execute(f"UPDATE chataction SET keywords = '{b64e(newone)}' WHERE guildid = {guildid} AND action = '{action}'")
        conn.commit()

        await ctx.respond(f"Chat action {action} for {keywords} removed.")
        await log("Chat", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} removed chat action {action} for {keywords}")

conn = newconn()
@bot.event
async def on_member_join(member):
    global conn
    try:
        cur = conn.cursor()
    except:
        conn = newconn()
        cur = conn.cursor()
    
    try:
        cur.execute(f"SELECT events FROM eventlog WHERE guildid = {member.guild.id}")
        events = cur.fetchall()
        if len(events) == 0:
            return
        events = events[0][0]
        if not "member_join" in events:
            return
            
        guildid = member.guild.id
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
        t = cur.fetchall()
        if len(t) > 0:
            chn = bot.get_channel(t[0][0])
            if chn != None:
                try:
                    embed = discord.Embed(title=f"{member}", description=f"{member.id}", color = GECKOCLR)
                    embed.set_footer(text=f"Event: member_join", icon_url = GECKOICON)
                    await chn.send(embed = embed)
                except:
                    pass
    except:
        pass

    haveresp = False
    guild = member.guild
    guildid = member.guild.id
    userid = member.id

    cur.execute(f"SELECT * FROM level WHERE guildid = {guildid} AND userid = {userid}")
    t = cur.fetchall()
    if len(t) > 0:
        cur.execute(f"DELETE FROM level WHERE guildid = {guildid} AND userid = {userid}")
    cur.execute(f"INSERT INTO level VALUES ({guildid}, {userid}, 0, 0, 0)")
    conn.commit()  

    botuser = guild.get_member(BOTID)
    cur.execute(f"SELECT keywords, action FROM chataction WHERE guildid = {guildid}")
    t = cur.fetchall()
    for tt in t:
        keywords = b64d(tt[0]).split(",")
        while keywords.count("") > 0:
            keywords.remove("")
        action = tt[1]

        for keyword in keywords:
            if keyword.startswith("[join]"):
                channel = None
                if not (keyword.find("-") == -1 or keyword.find("-") > keyword.find("|")):
                    channelid = int(keyword[keyword.find("-")+1: keyword.find("|")])
                    channel = bot.get_channel(channelid)
                if action == "timeout" and botuser.guild_permissions.moderate_members:
                    await member.timeout(datetime(9999,1,1), reason = "Gecko Chat Action")
                elif action == "kick" and botuser.guild_permissions.kick_members:
                    await member.kick(reason = "Gecko Chat Action")
                elif action == "ban" and botuser.guild_permissions.ban_members:
                    await member.ban(reason = "Gecko Chat Action")
                elif action == "message":
                    content = b64d(keyword.split("|")[1])
                    content = content.replace("{mention}", f"<@{member.id}>")
                    content = content.replace("{name}", member.name)
                    content = content.replace("{nametag}", str(member))
                    await channel.send(content)
                    haveresp = True
                elif action == "role" and botuser.guild_permissions.manage_roles:
                    roleid = int(keyword.split("|")[1])
                    rmv = False
                    if roleid < 0:
                        rmv = True
                        roleid = -roleid
                    role = discord.utils.get(guild.roles, id = roleid)
                    if role is None:
                        continue
                    if not rmv and not role in member.roles:
                        await member.add_roles(role, reason = "Gecko Chat Action Auto-Role")
                        if not haveresp:
                            await channel.send(f"<@{member.id}>, you are given {role.name} role.")
                    if rmv and role in member.roles:
                        await member.remove_roles(role, reason = "Gecko Chat Action Auto-Unrole")
                        if not haveresp:
                            await channel.send(f"<@{member.id}>, {role.name} role is removed.")
                elif action == "embed":
                    embedid = int(keyword.split("|")[1])
                    cur.execute(f"SELECT data FROM embed WHERE guildid = {guild.id} AND embedid = {embedid}")
                    t = cur.fetchall()
                    if len(t) == 0:
                        continue
                        
                    d = t[0][0].split("|")
                    title = b64d(d[0])
                    url = b64d(d[1])
                    description = b64d(d[2])
                    footer = b64d(d[3])
                    thumbnail_url = [b64d(d[4]), b64d(d[5])]
                    clr = d[6].split(" ")

                    footer_icon_url = ""

                    if footer.startswith("["):
                        footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
                        footer = footer[footer.find("]") + 1:]
                    
                    embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
                    embed.set_footer(text=footer, icon_url=footer_icon_url)
                    embed.set_thumbnail(url=thumbnail_url[0])
                    embed.set_image(url=thumbnail_url[1])
                    
                    await channel.send(embed=embed)
                    haveresp = True
                    
@bot.event
async def on_member_remove(member):
    global conn
    try:
        cur = conn.cursor()
    except:
        conn = newconn()
        cur = conn.cursor()
    guild = member.guild
    guildid = member.guild.id
    userid = member.id

    try:
        cur.execute(f"SELECT events FROM eventlog WHERE guildid = {member.guild.id}")
        events = cur.fetchall()
        if len(events) == 0:
            return
        events = events[0][0]
        if not "member_remove" in events:
            return
            
        guildid = member.guild.id
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'eventlog'")
        t = cur.fetchall()
        if len(t) > 0:
            chn = bot.get_channel(t[0][0])
            if chn != None:
                try:
                    embed = discord.Embed(title=f"{member}", description=f"{member.id}", color = GECKOCLR)
                    embed.set_footer(text=f"Event: member_remove", icon_url = GECKOICON)
                    await chn.send(embed = embed)
                except:
                    pass
    except:
        pass

    cur.execute(f"SELECT * FROM level WHERE guildid = {guildid} AND userid = {userid}")
    t = cur.fetchall()
    if len(t) > 0:
        cur.execute(f"DELETE FROM level WHERE guildid = {guildid} AND userid = {userid}")
        conn.commit()

    botuser = guild.get_member(BOTID)
    cur.execute(f"SELECT keywords, action FROM chataction WHERE guildid = {guildid}")
    t = cur.fetchall()
    for tt in t:
        keywords = b64d(tt[0]).split(",")
        while keywords.count("") > 0:
            keywords.remove("")
        action = tt[1]

        for keyword in keywords:
            if keyword.startswith("[leave]"):
                channel = None
                if not (keyword.find("-") == -1 or keyword.find("-") > keyword.find("|")):
                    channelid = int(keyword[keyword.find("-")+1: keyword.find("|")])
                    channel = bot.get_channel(channelid)
                if action == "timeout" and botuser.guild_permissions.moderate_members:
                    await member.timeout(datetime(9999,1,1), reason = "Gecko Chat Action")
                elif action == "kick" and botuser.guild_permissions.kick_members:
                    await member.kick(reason = "Gecko Chat Action")
                elif action == "ban" and botuser.guild_permissions.ban_members:
                    await member.ban(reason = "Gecko Chat Action")
                if action == "message":
                    content = b64d(keyword.split("|")[1])
                    content = content.replace("{mention}", f"<@{member.id}>")
                    content = content.replace("{name}", member.name)
                    content = content.replace("{nametag}", str(member))
                    await channel.send(content)
                elif action == "embed":
                    embedid = int(keyword.split("|")[1])
                    cur.execute(f"SELECT data FROM embed WHERE guildid = {guild.id} AND embedid = {embedid}")
                    t = cur.fetchall()
                    if len(t) == 0:
                        continue
                        
                    d = t[0][0].split("|")
                    title = b64d(d[0])
                    url = b64d(d[1])
                    description = b64d(d[2])
                    footer = b64d(d[3])
                    thumbnail_url = [b64d(d[4]), b64d(d[5])]
                    clr = d[6].split(" ")

                    footer_icon_url = ""

                    if footer.startswith("["):
                        footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
                        footer = footer[footer.find("]") + 1:]
                    
                    embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
                    embed.set_footer(text=footer, icon_url=footer_icon_url)
                    embed.set_thumbnail(url=thumbnail_url[0])
                    embed.set_image(url=thumbnail_url[1])
                    
                    await channel.send(embed=embed)

@bot.event
async def on_message(message):
    global conn
    try:
        cur = conn.cursor()
    except:
        conn = newconn()
        cur = conn.cursor()
    guild = message.guild
    if guild is None:
        return
    botuser = guild.get_member(BOTID)
    user = message.author
    userid = user.id
    guildid = message.guild.id
    msg = message.content
    msg = " "+msg.lower()+" "
    if user.id == BOTID or message.guild is None:
        return

    premium = GetPremium(message.guild)
    if premium > 0 and message.content != None:
        cur.execute(f"SELECT fromlang, tolang FROM translate WHERE guildid = {guildid} AND channelid = {message.channel.id}")
        t1 = cur.fetchall()
        cur.execute(f"SELECT fromlang, tolang FROM translate WHERE guildid = {guildid} AND channelid = 0")
        t2 = cur.fetchall()
        if len(t1) > 0 or len(t2) > 0:
            fromlang = "*"
            if len(t1) > 0 and len(t2) > 0:
                if t1[0][0] != "*" and t2[0][0] != "*":
                    fromlang = t1[0][0] + "," + t2[0][0]
            elif len(t1) > 0:
                fromlang = t1[0][0]
            elif len(t2) > 0:
                fromlang = t2[0][0]
                
            tolang = "en"
            if len(t2) > 0:
                tolang = t2[0][1]
            if len(t1) > 0:
                tolang = t1[0][1] # NOTE: Channel settings overal general settings

            dtc = DetectLang(message.content)
            if (fromlang == "*" or dtc in fromlang.split(",")) and dtc != tolang:
                res = Translate(message.content, tolang, fromlang = dtc)
                embed = discord.Embed(description = res[0], color = GECKOCLR)
                avatar = None
                if message.author.avatar != None and message.author.avatar.url != None:
                    avatar = message.author.avatar.url
                embed.timestamp = datetime.now()
                embed.set_author(name = f"{message.author.name}#{message.author.discriminator}", icon_url = avatar)
                embed.set_footer(text = f"{res[1]} -> {res[2]} • {TRANSLATE} ", icon_url = GECKOICON)
                
                await message.reply(embed = embed, mention_author = False)
                
    updlvl = 0

    if not user.bot:
        if len(msg) > 3:
            cur.execute(f"SELECT xp, level, lastmsg FROM level WHERE guildid = {guildid} AND userid = {userid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO level VALUES ({guildid}, {userid}, 0, 15, {int(time())})")
                conn.commit()
            else:
                xp = t[0][0]
                oldlvl = t[0][1]
                lastmsg = t[0][2]
                if time() - lastmsg >= 60:
                    cur.execute(f"SELECT sval FROM settings WHERE guildid = {guildid} AND skey = 'xprate'")
                    xprate = 1
                    t = cur.fetchall()
                    if len(t) > 0:
                        xprate = float(t[0][0])
                    xp += randint(15, 25) * xprate
                    level = CalcLevel(xp)
                    cur.execute(f"UPDATE level SET xp = {xp}, level = {level}, lastmsg = {int(time())} WHERE guildid = {guildid} AND userid = {userid}")
                    conn.commit()
                    if level > oldlvl:
                        updlvl = level
        if updlvl > 0:
            cur.execute(f"SELECT roleid FROM levelrole WHERE guildid = {guildid} AND level = {updlvl}")
            t = cur.fetchall()
            if len(t) > 0:
                role = guild.get_role(t[0][0])
                try:
                    await user.add_roles(role, reason = "Gecko Rank Role")
                except:
                    pass
                cur.execute(f"SELECT roleid FROM levelrole WHERE guildid = {guildid} AND level < {updlvl} ORDER BY level DESC LIMIT 1")
                t = cur.fetchall()
                if len(t) > 0:
                    role = guild.get_role(t[0][0])
                    try:
                        await user.remove_roles(role, reason = "Gecko Rank Role")
                    except:
                        pass

    haveresp = False
    cur.execute(f"SELECT keywords, action FROM chataction WHERE guildid = {message.guild.id}")
    t = cur.fetchall()
    for tt in t:
        keywords = b64d(tt[0]).split(",")
        while keywords.count("") > 0:
            keywords.remove("")
        action = tt[1]
        for keyword in keywords:
            if msg.find(keyword.split("|")[0]) == -1:
                continue
            idx = msg.index(keyword.split("|")[0])
            if not msg[idx-1].isalnum() and not msg[idx+len(keyword.split("|")[0])].isalnum():
                try:
                    if not isStaff(guild, user):
                        if action == "delete" and botuser.guild_permissions.manage_messages:
                            await message.delete()
                        elif action == "timeout" and botuser.guild_permissions.moderate_members:
                            await user.timeout(datetime(9999,1,1), reason = "Gecko Chat Action")
                        elif action == "kick" and botuser.guild_permissions.kick_members:
                            await user.kick(reason = "Gecko Chat Action")
                        elif action == "ban" and botuser.guild_permissions.ban_members:
                            await user.ban(reason = "Gecko Chat Action")
                    if action == "react" and botuser.guild_permissions.add_reactions:
                        await message.add_reaction(keyword.split("|")[1])
                    elif action == "message":
                        content = b64d(keyword.split("|")[1])
                        content = content.replace("{mention}", f"<@{user.id}>")
                        content = content.replace("{name}", user.name)
                        content = content.replace("{nametag}", str(user))
                        await message.channel.send(content)
                        haveresp = True
                    elif action == "role" and botuser.guild_permissions.manage_roles:
                        roleid = int(keyword.split("|")[1])
                        rmv = False
                        if roleid < 0:
                            rmv = True
                            roleid = -roleid
                        role = discord.utils.get(guild.roles, id = roleid)
                        if role is None:
                            continue
                        if not rmv:
                            if not role in user.roles:
                                await user.add_roles(role, reason = "Gecko Chat Action Auto-Role")
                                if not haveresp:
                                    await message.channel.send(f"<@{user.id}>, you are given {role.name} role.")
                            else:
                                if not haveresp:
                                    await message.channel.send(f"<@{user.id}>, you already have {role.name} role.")
                        if rmv:
                            if role in user.roles:
                                await user.remove_roles(role, reason = "Gecko Chat Action Auto-Unrole")
                                if not haveresp:
                                    await message.channel.send(f"<@{user.id}>, {role.name} role is removed.")
                            else:
                                if not haveresp:
                                    await message.channel.send(f"<@{user.id}>, you don't have {role.name} role.")
                    elif action == "embed":
                        embedid = int(keyword.split("|")[1])
                        cur.execute(f"SELECT data FROM embed WHERE guildid = {message.guild.id} AND embedid = {embedid}")
                        t = cur.fetchall()
                        if len(t) == 0:
                            continue
                            
                        d = t[0][0].split("|")
                        title = b64d(d[0])
                        url = b64d(d[1])
                        description = b64d(d[2])
                        footer = b64d(d[3])
                        thumbnail_url = [b64d(d[4]), b64d(d[5])]
                        clr = d[6].split(" ")

                        footer_icon_url = ""

                        if footer.startswith("["):
                            footer_icon_url = footer[footer.find("[") + 1: footer.find("]")].replace(" ","")
                            footer = footer[footer.find("]") + 1:]
                        
                        embed=discord.Embed(title=title, url=url, description=description, color=discord.Colour.from_rgb(int(clr[0]), int(clr[1]), int(clr[2])))
                        embed.set_footer(text=footer, icon_url=footer_icon_url)
                        embed.set_thumbnail(url=thumbnail_url[0])
                        embed.set_image(url=thumbnail_url[1])
                        
                        await message.channel.send(embed=embed)
                        haveresp = True

                except Exception as e:
                    await log("ChatAction", f"[Guild {message.guild} ({message.guild.id})] Unknown error occurred on {action} {user}: {str(e)}", message.guild.id)

    if updlvl > 0:
        # if bot can send message in the channel
        botuser = message.guild.get_member(bot.user.id)
        cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'level'")
        t = cur.fetchall()
        if len(t) > 0:
            if t[0][0] == 0:
                if message.channel.permissions_for(botuser).send_messages:
                    await message.channel.send(f"GG <@{user.id}>, you have upgraded to level {updlvl}!")
            else:
                channel = bot.get_channel(int(t[0][0]))
                if channel != None:
                    try:
                        if channel.permissions_for(botuser).send_messages:
                            await channel.send(f"GG <@{user.id}>, you have upgraded to level {updlvl}!")
                    except:
                        pass

@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message
    if message.guild is None or message.author.id == user.id \
        or message.author.bot or user.bot or message.author.id == BOTID: # no DM / no self-thumb / no bot
        return
    userid = message.author.id
    guildid = message.guild.id
    emoji = reaction.emoji
    THUMBSUP = '👍'
    if emoji == THUMBSUP:
        conn = newconn()
        cur = conn.cursor()
        # check if thumbsxp enabled
        cur.execute(f"SELECT * FROM settings WHERE guildid = {guildid} AND skey='thumbxp'")
        t = cur.fetchall()
        if len(t) > 0:
            updlvl = 0
            
            cur.execute(f"SELECT xp, level FROM level WHERE guildid = {guildid} AND userid = {userid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO level VALUES ({guildid}, {userid}, 0, 15, {int(time())})")
                conn.commit()
            else:
                xp = t[0][0]
                oldlvl = t[0][1]

                cur.execute(f"SELECT sval FROM settings WHERE guildid = {guildid} AND skey = 'xprate'")
                xprate = 1
                t = cur.fetchall()
                if len(t) > 0:
                    xprate = float(t[0][0])
                xp += 5 * xprate
                level = CalcLevel(xp)
                cur.execute(f"UPDATE level SET xp = {xp}, level = {level}, lastmsg = {int(time())} WHERE guildid = {guildid} AND userid = {userid}")
                conn.commit()
                if level > oldlvl:
                    updlvl = level

            if updlvl > 0:
                cur.execute(f"SELECT roleid FROM levelrole WHERE guildid = {guildid} AND level = {updlvl}")
                t = cur.fetchall()
                if len(t) > 0:
                    role = guild.get_role(t[0][0])
                    try:
                        await user.add_roles(role, reason = "Gecko Rank Role")
                    except:
                        pass
                    cur.execute(f"SELECT roleid FROM levelrole WHERE guildid = {guildid} AND level < {updlvl} ORDER BY level DESC LIMIT 1")
                    t = cur.fetchall()
                    if len(t) > 0:
                        role = guild.get_role(t[0][0])
                        try:
                            await user.remove_roles(role, reason = "Gecko Rank Role")
                        except:
                            pass

                # if bot can send message in the channel
                botuser = message.guild.get_member(bot.user.id)
                cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'level'")
                t = cur.fetchall()
                if len(t) > 0:
                    if t[0][0] == 0:
                        if message.channel.permissions_for(botuser).send_messages:
                            await message.channel.send(f"GG <@{user.id}>, you have upgraded to level {updlvl}!")
                    else:
                        channel = bot.get_channel(int(t[0][0]))
                        if channel != None:
                            try:
                                if channel.permissions_for(botuser).send_messages:
                                    await channel.send(f"GG <@{user.id}>, you have upgraded to level {updlvl}!")
                            except:
                                pass

bot.add_cog(ManageChat(bot))