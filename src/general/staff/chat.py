# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff - Chat Action Management

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from base64 import b64encode, b64decode
from datetime import datetime

from bot import bot
from settings import *
from functions import *
from db import newconn

class ManageChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    manage = SlashCommandGroup("chat", "Manage chat action")
    
    @manage.command(name = "add", description = "Staff - Add Gecko's action when detected keyword in message.")
    async def add(self, ctx, keywords: discord.Option(str, "Keywords, split with ','. Phrases with space separating words are accepted."),
        action: discord.Option(str, "Gecko's action, if set to react, the reaction emoji will be needed", choices = ["timeout", "kick", "ban", "react"]),
        emoji: discord.Option(str, "Reaction emoji, needed only when action is 'react'", required = False)):

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

        if action == "timeout":
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
                await ctx.respond("Reaction emoji is needed as action is 'react'", ephemeral = True)
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
        for d in current:
            if not d in existing:
                if action == "react":
                    newone += d + "|" + emoji + ","
                else:
                    newone += d + ","
        newone = newone.split(",")
        while newone.count("") > 0:
            newone.remove("")
        newone = ",".join(newone).lower()
        
        cur.execute(f"UPDATE chataction SET keywords = '{b64e(newone)}' WHERE guildid = {guildid} AND action = '{action}'")
        conn.commit()

        await ctx.respond(f"Chat action {action} for {keywords} added.")
        await log("Chat", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} added chat action {action} for {keywords}")

    @manage.command(name = "list", description = "Staff - List keywords Gecko will act on.")
    async def show(self, ctx,
        action: discord.Option(str, "Gecko's action, if set to react, the reaction emoji will be needed", choices = ["timeout", "kick", "ban", "react"])):

        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guild = ctx.guild
        guildid = guild.id
        if not isStaff(ctx.guild, ctx.author):
            await ctx.respond("Only staff are allowed to run the command!", ephemeral = True)
            return
        
        if not action in ["timeout", "kick", "ban", "react"]:
            await ctx.respond(f"Invalid action {action}.", ephemeral = True)
            return

        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT keywords FROM chataction WHERE guildid = {guildid} AND action = '{action}'")
        t  = cur.fetchall()
        if len(t) == 0 or t[0][0] == "":
            await ctx.respond(f"No keyword found.", ephemeral = True)
            return

        msg = ""
        if action in ["timeout", "kick", "ban"]:
            msg = "When keywords below are found in messages: \n```"
            msg += b64d(t[0][0]).replace(",",", ")
            msg += f"```Gecko will **{action}** the author."
        else:
            d = {}
            t = b64d(t[0][0]).split(",")
            for tt in t:
                kw = tt.split("|")[0]
                emoji = tt.split("|")[1]
                if not emoji in d.keys():
                    d[emoji] = [kw]
                else:
                    d[emoji].append(kw)
            msg = "Gecko will react those emojis when those keywords are found in messages:\n\n"
            for t in d.keys():
                msg += f"{t}: `{', '.join(d[t])}`\n"
        await ctx.respond(msg)

    @manage.command(name = "remove", description = "Staff - Remove Gecko's action when detected keyword in message.")
    async def remove(self, ctx, keywords: discord.Option(str, "Keywords, split with ','"),
        action: discord.Option(str, "Gecko's action, if set to react, the reaction emoji will be needed", choices = ["timeout", "kick", "ban", "react"])):

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
        toremove = keywords.lower().split(",")
        newone = ""
        for d in existing:
            if not d.split("|")[0] in toremove:
                newone += d + ","
        newone = newone.split(",")
        while newone.count("") > 0:
            newone.remove("")
        newone = ",".join(newone)

        cur.execute(f"UPDATE chataction SET keywords = '{b64e(newone)}' WHERE guildid = {guildid} AND action = '{action}'")
        conn.commit()

        await ctx.respond(f"Chat action {action} for {keywords} removed.")
        await log("Chat", f"[Guild {ctx.guild} ({ctx.guild.id})] {ctx.author} removed chat action {action} for {keywords}")

conn = newconn()
@bot.event
async def on_message(message):
    global gonn
    try:
        cur = conn.cursor()
    except:
        conn = newconn()
        cur = conn.cursor()
    user = message.author
    msg = message.content
    msg = " "+msg.lower()+" "
    if user.id == BOTID or message.guild is None:
        return
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
                    if action == "timeout":
                        await user.timeout(datetime(9999,1,1), reason = "Gecko Chat Action")
                    elif action == "kick":
                        await user.kick(reason = "Gecko Chat Action")
                    elif action == "ban":
                        await user.ban(reason = "Gecko Chat Action")
                    elif action == "react":
                        await message.add_reaction(keyword.split("|")[1])
                except Exception as e:
                    await log("ChatAction", f"[Guild {message.guild} ({message.guild.id})] Unknown error occurred on {action} {user}: {str(e)}", message.guild.id)

bot.add_cog(ManageChat(bot))