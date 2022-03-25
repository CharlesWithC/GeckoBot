# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Loop Tasks of Gecko Bot

import os, asyncio
import discord
from base64 import b64encode, b64decode

from bot import bot
from settings import *
from functions import *
from db import newconn

async def Radio():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="TruckersFM"))
    while not bot.is_closed():
        # Play radio
        for sid in RADIO_CHANNEL:
            try:
                guild = bot.get_guild(sid[0])
                voice_channel = guild.voice_client
                channel = bot.get_channel(sid[1])
                if voice_channel is None or not voice_channel.is_connected():
                    try:
                        await log("Radio", f"Connecting to {channel}")
                        await channel.connect(timeout = 5)
                        voice_channel = guild.voice_client
                    except Exception as e:
                        await log("Radio", f"Failed to connect to {channel}  {str(e)}")
                        if not voice_channel is None:
                            await voice_channel.disconnect()
                            await log("Radio", f"Disconnected from {channel}")
                        continue

                    try:
                        player = discord.FFmpegPCMAudio(source = TFM)
                        await log("Radio", f"Playing TruckersFM in {channel}")
                        voice_channel.play(player)
                    except Exception as e:
                        await log("Radio", f"Failed to play TruckersFM in {channel} {str(e)}")
                        await voice_channel.disconnect()
                        await log("Radio", f"Disconnected from {channel}")
                        continue

            except Exception as e:
                await log("Radio", f"Unknown exception: {str(e)}")
                pass

        await asyncio.sleep(3)
        
async def SelfRole():
    conn = newconn()
    cur = conn.cursor()
    await bot.wait_until_ready()
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
                        adminchn = bot.get_channel(STAFF_CHANNEL[1])
                        embed = discord.Embed(title=f"Staff Notice", description=f"A self-role post (`{msgid}`) with role-binds {rolebindtxt} sent in <#{channelid}> (`{channelid}`) at guild {guild} (`{guildid}`) has expired because I either cannot view the channel, or cannot find the message. I will no longer assign roles on reactions.", url=f"https://discord.com/channels/{guildid}/{channelid}/{msgid}", color=0x0000DD)
                        await adminchn.send(embed=embed)
                    except:
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
        
bot.loop.create_task(Radio())
bot.loop.create_task(SelfRole())