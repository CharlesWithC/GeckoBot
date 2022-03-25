# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Staff Functions of Gecko Bot

import os, asyncio
import discord
from base64 import b64encode, b64decode
import validators

from bot import bot
from settings import *
from functions import *
from db import newconn

@bot.command(name="selfrole")
async def SelfRole(ctx):
    # This is a complex function
    # Bot will parse command as below:
    # !selfrole {#channel} 
    # title: {title} 
    # description: {description} 
    # imgurl: {imgurl} (don't put imgurl parameter if you don't need thumbnail)
    # rolebind: {@role1} {emoji1} {@role2} {emoji2} ...
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
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !selfrole command")
        return

    async with ctx.typing():
        msg = ctx.message.content
        if msg.find("<#") == -1 or msg.find("description:") == -1 or msg.find("rolebind:") == -1:
            sample = "!selfrole {#channel} title: {title} description: {description} <imgurl: {imgurl}> rolebind: {@role1} {emoji1} {@role2} {emoji2} ..."
            await ctx.reply(f"{ctx.message.author.name}, this is an invalid command!\nThis command works like:\n`{sample}`\nYou only need to change content in {{}}.\nYou can add line breaks or use \\n for line breaking.")
            return

        channelid = int(msg[msg.find("<#") + 2 : msg.find(">")])
        title = msg[msg.find("title:") + len("title:") : msg.find("description:")]
        imgurl = ""
        if msg.find("imgurl:") != -1:
            imgurl = msg[msg.find("imgurl:") + len("imgurl:") : msg.find("rolebind:")].replace(" ","")
            if validators.url(imgurl) != True:
                await ctx.reply(f"{ctx.message.author.name}, {imgurl} is an invalid url.")
                return
        tmp = msg.find("imgurl:")
        if tmp == -1:
            tmp = msg.find("rolebind:")
        description = msg[msg.find("description:") + len("description:") : tmp]
        rolebindtxt = msg[msg.find("rolebind:") + len("rolebind:"):].split()
        i = 0
        rolebind = []
        r = -1
        e = ""
        for data in rolebindtxt:
            if i%2 == 0: # role
                if not data.startswith("<@&") or not data.endswith(">"):
                    await ctx.reply(f"{ctx.message.author.name}, invalid role {data}. Make sure the role exists each role has a emoji following.")
                    return
                r = int(data[3:-1])
            else:
                e = data.replace(" ", "")
                rolebind.append((r, e))
                cur.execute(f"SELECT emoji FROM rolebind WHERE guildid = {guildid} AND role = {r}")
                t = cur.fetchall()
                if len(t) != 0:
                    emoji = b64decode(t[0][0].encode()).decode()
                    await ctx.reply(f"{ctx.message.author.name}, role <@&{r}> already bound to {emoji} in another post.")
                    return

            i += 1
        
        message = None
        try:
            channel = bot.get_channel(channelid)
            embed = discord.Embed(title=title, description=description)
            embed.set_thumbnail(url=imgurl)
            message = await channel.send(embed=embed)
            for data in rolebind:
                await message.add_reaction(data[1])
            await ctx.reply(f"{ctx.message.author.name}, self-role message posted at <#{channelid}>!")

            title = b64encode(title.encode()).decode()
            description = b64encode(description.encode()).decode()
            imgurl = b64encode(imgurl.encode()).decode()
            msgid = message.id
            cur.execute(f"INSERT INTO selfrole VALUES ({guildid}, {channelid}, {msgid}, '{title}', '{description}', '{imgurl}')")
            for data in rolebind:
                cur.execute(f"INSERT INTO rolebind VALUES ({guildid}, {channelid}, {msgid}, {data[0]}, '{b64encode(data[1].encode()).decode()}')")
            conn.commit()

            await log("Staff", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} created a self-role post at {channel} ({channelid}), with role-binding: {rolebindtxt}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            await ctx.reply(f"{ctx.message.author.name}, it seems I cannot send message at <#{channelid}>. Make sure the channel exist and I have access to it!")

            await log("Staff", f"[guild {ctx.guild} ({ctx.guild.id})] !selfrole command executed by {ctx.message.author.name} failed due to {str(e)}")

@bot.command(name="editsr")
async def EditSelfRole(ctx):
    # !editsr {message link}
    # title: ...
    # description: ...
    # imgurl: ...
    # rolebind (only append): ...
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
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !editsr command")
        return
    
    async with ctx.typing():
        msgtxt = ctx.message.content.split()
        if len(msgtxt) < 4:
            await ctx.reply(f"{ctx.message.author.name}, invalid command!\n`!editsr {{message link}} {{item}} {{data}}`\n`item` can be `title` `description` `imgurl` `rolebind`")
            return

        msglink = msgtxt[1]
        item = msgtxt[2]
        data = " ".join(msgtxt[3:])
        if msglink.endswith("/"):
            msglink = msglink[:-1]
        msglink = msglink.split("/")
        guildid = int(msglink[-3])
        channelid = int(msglink[-2])
        msgid = int(msglink[-1])
        
        try:
            channel = bot.get_channel(channelid)
            message = await channel.fetch_message(msgid)
        except:
            await ctx.reply(f"{ctx.message.author.name}, I cannot fetch that message.")
            return

        cur.execute(f"SELECT title, description, imgurl FROM selfrole WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
        d = cur.fetchall()
        if len(d) == 0:
            await ctx.reply(f"{ctx.message.author.name}, message is not bound to any self-role post.")
            return
        d = d[0]
        title = b64decode(d[0].encode()).decode()
        description = b64decode(d[1].encode()).decode()
        imgurl = b64decode(d[2].encode()).decode()

        if item in ["title", "description", "imgurl"]:
            if item == "title":
                title = data
            elif item == "description":
                description = data
            elif item == "imgurl":
                imgurl = data
            embed = discord.Embed(title=title, description=description)
            embed.set_thumbnail(url=imgurl)
            await message.edit(embed=embed)
            await ctx.reply(f"{ctx.message.author.name}, self-role post updated!")

            data = b64encode(data.encode()).decode()
            cur.execute(f"UPDATE selfrole SET {item} = '{data}' WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
            conn.commit()

            await log("Staff", f"{ctx.message.author.name} updated self-role post {msglink} {item} to {data}.")
        
        elif item == "rolebind":
            rolebindtxt = data.split()
            i = 0
            rolebind = []
            r = -1
            e = ""
            for data in rolebindtxt:
                if i%2 == 0: # role
                    if not data.startswith("<@&") or not data.endswith(">"):
                        await ctx.reply(f"{ctx.message.author.name}, invalid role {data}. Make sure the role exists each role has a emoji following.")
                        return
                    r = int(data[3:-1])
                else:
                    e = data.replace(" ", "")
                    rolebind.append((r, e))
                i += 1
            
            updates = ""
            updateslog = ""
            for data in rolebind:
                roleid = data[0]
                emoji = data[1]
                cur.execute(f"SELECT * FROM rolebind WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid} AND role = {roleid}")
                t = cur.fetchall()
                if len(t) == 0: # not found
                    updates += f"Added <@&{roleid}> => {emoji}.\n"
                    updateslog += f"Added <@&{roleid}> ({roleid}) => {emoji}. "
                    await message.add_reaction(emoji)
                    emoji = b64encode(emoji.encode()).decode()
                    cur.execute(f"INSERT INTO rolebind VALUES ({guildid}, {channelid}, {msgid}, {roleid}, '{emoji}')")
                    conn.commit()
                else:
                    updates += f"<@&{roleid}> already bound, you cannot the emoji representing it.\n"
                
            await ctx.reply(f"{ctx.message.author.name}, self-role post updated!\n`{updates}`")
            await log("Staff", f"{ctx.message.author.name} updated self-role post {msglink} rolebind. {updateslog}")

@bot.command(name="listsr")
async def ListSelfRole(ctx):
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
        await log("Staff", f"{ctx.message.author.name} is unauthorized to execute !listsr command")
        return

    async with ctx.typing():
        msg = ""
        cur.execute(f"SELECT channelid, msgid FROM selfrole WHERE guildid = {guildid}")
        t = cur.fetchall()
        for tt in t:
            msg += f"<#{tt[0]}> https://discord.com/channels/{guildid}/{tt[0]}/{tt[1]}\n"
        
        embed = discord.Embed(title="Self-role posts in this server", description=msg)
        await ctx.send(embed=embed)

async def SelfRole():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    selfrole_fail = [] # (channelid, msgid)
    while not bot.is_closed():
        # Self role
        try:
            cur.execute(f"SELECT guildid, channelid, msgid FROM selfrole")
            t = cur.fetchall()
            selfroles = []
            for tt in t:
                selfroles.append((tt[0], tt[1], tt[2]))
            for selfrole in selfroles:
                guildid = selfrole[0]
                guild = bot.get_guild(guildid)
                channelid = selfrole[1]
                msgid = selfrole[2]
                
                cur.execute(f"SELECT role, emoji FROM rolebind")
                d = cur.fetchall()
                rolebindtxt = ""
                rolebind = []
                for dd in d:
                    rolebind.append((dd[0], dd[1]))
                    rolebindtxt = f"<@&{dd[0]}> => {b64decode(dd[1].encode()).decode()} "

                if selfrole_fail.count((channelid, msgid)) > 10:
                    while selfrole_fail.count((channelid, msgid)) > 0:
                        selfrole_fail.remove((channelid, msgid))
                    cur.execute(f"DELETE FROM selfrole WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
                    cur.execute(f"DELETE FROM rolebind WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
                    cur.execute(f"DELETE FROM userrole WHERE guildid = {guildid} AND channelid = {channelid} AND msgid = {msgid}")
                    conn.commit()
                    try:
                        await log("SelfRole", f"[{guild} ({guildid})] Self-role post {msgid} expired as bot cannot access the channel.")
                        adminchn = bot.get_channel(STAFF_CHANNEL[1])
                        embed = discord.Embed(title=f"Staff Notice", description=f"A self-role post (`{msgid}`) with role-binds {rolebindtxt} sent in <#{channelid}> (`{channelid}`) at guild {guild} (`{guildid}`) has expired because I either cannot view the channel, or cannot find the message. I will no longer assign roles on reactions.", url=f"https://discord.com/channels/{guildid}/{channelid}/{msgid}", color=0x0000DD)
                        await adminchn.send(embed=embed)
                    except Exception as e:
                        await log("SelfRole", f"[{guild} ({guildid})] Self-role post `{msgid}` expired as bot cannot access the channel. {str(e)}")
                        pass
                    continue
                
                try:
                    channel = bot.get_channel(channelid)
                    if channel is None:
                        selfrole_fail.append((channelid, msgid))
                    message = await channel.fetch_message(msgid)
                    if message is None:
                        selfrole_fail.append((channelid, msgid))
                except:
                    selfrole_fail.append((channelid, msgid))
                    continue
                while selfrole_fail.count((channelid, msgid)) > 0:
                    selfrole_fail.remove((channelid, msgid))

                cur.execute(f"SELECT role, emoji FROM rolebind WHERE channelid = {channelid} AND msgid = {msgid}")
                d = cur.fetchall()
                rolebind = {}
                for dd in d:
                    rolebind[dd[1]] = dd[0]

                reactions = message.reactions
                existing_emojis = []
                for reaction in reactions:
                    emoji = b64encode(str(reaction.emoji).encode()).decode()
                    existing_emojis.append(emoji)
                    roleid = rolebind[emoji]
                    role = discord.utils.get(guild.roles, id=roleid)
                    inrole = []
                    async for user in reaction.users():
                        if user.id != BOTID:
                            found = False
                            for userrole in user.roles:
                                if userrole.id == roleid:
                                    found = True
                                    break
                            if not found:
                                try:
                                    await user.add_roles(role)
                                except: # cannot assign role to user (maybe user has left server)
                                    await log("SelfRole", f"[{guild} ({guildid})] Cannot assign {role} ({roleid}) for {user} ({user.id}), user reaction removed.")
                                    await message.remove_reaction(reaction.emoji, user)
                                    continue
                                cur.execute(f"SELECT * FROM userrole WHERE userid = {user.id} AND roleid = {roleid} AND guildid = {guildid}")
                                p = cur.fetchall()
                                if len(p) == 0:
                                    await log("SelfRole", f"[{guild} ({guildid})] Added {role} ({roleid}) role to {user} ({user.id}).")
                                    cur.execute(f"INSERT INTO userrole VALUES ({guildid}, {channelid}, {msgid}, {user.id}, {roleid})")
                            inrole.append(user.id)
                    conn.commit()
                    cur.execute(f"SELECT userid FROM userrole WHERE roleid = {roleid}")
                    preusers = cur.fetchall()
                    for data in preusers:
                        preuser = data[0]
                        if not preuser in inrole:
                            cur.execute(f"DELETE FROM userrole WHERE userid = {preuser} AND roleid = {roleid} AND guildid = {guildid}")
                            try:
                                role = discord.utils.get(guild.roles, id=roleid)
                                user = discord.utils.get(guild.members, id=preuser)
                                await user.remove_roles(role)
                                await log("SelfRole", f"[{guild} ({guildid})] Removed {role} ({roleid}) role from user {user} ({user.id}).")
                            except:
                                pass
                    conn.commit()
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            await log("SelfRole", f"Unknown error {str(e)}")

        await asyncio.sleep(60)
        
bot.loop.create_task(SelfRole())