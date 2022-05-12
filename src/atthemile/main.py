# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# At The Mile Logistics VTC exclusive

import os, json, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ext import commands
from time import time
from datetime import datetime
from random import randint

from bot import bot
from settings import *
from functions import *
from db import newconn
import atthemile.webhook

ATMGUILD = 929761730089877626
CHNID = 969667013549121667
MSGID = 969766478679269416
UPDID = 941537154360823870

ADMINROLES = [929761730547032135, 941544365950644224, 941544363614433320, 941903394703020072]

LEVEL = {0: 941548241126834206, 2000: 941544375790489660, 10000: 941544368928596008, 15000: 969678264832503828, 25000: 941544370467901480, 40000: 969727939686039572, 50000: 941544372669907045, 75000: 969678270398341220, 80000: 969727945075732570, 100000: 941544373710094456, 150000: 969727950016643122, 200000: 969727954433245234, 250000: 969678280112353340, 300000: 969727958749155348, 350000: 969727962905735178, 400000: 969727966999379988, 450000: 969727971428536440, 500000: 941734703210311740, 600000: 969727975358607380, 700000: 969727979368370188, 800000: 969728350564282398, 900000: 969678286332518460, 1000000: 941734710470651964}

def TSeparator(num):
    num = str(num)
    if len(num) <= 3:
        return num
    return TSeparator(num[:-3]) + "," + num[-3:]
    
# class AtTheMile(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
    
#     atm = SlashCommandGroup("atm", "At The Mile")

#     def GetLevel(self, point):
#         pnts = list(LEVEL.keys())[::-1]
#         for pnt in pnts:
#             if point >= pnt:
#                 return LEVEL[pnt]

    # @atm.command(name="mile", description="Give mile point", guild_ids = [ATMGUILD])
    # @discord.commands.permissions.has_role(929761730505080871, guild_id=ATMGUILD)
    # async def mile(self, ctx, user: discord.Option(discord.User, "User"),
    #         mile: discord.Option(int, "Mile count, can be negative, but you risk role compromise")):
    #     ok = False
    #     roles = ctx.author.roles
    #     for role in roles:
    #         if role.id in ADMINROLES:
    #             ok = True
    #         if role.id == 969755343804567552:
    #             await ctx.respond("<@&969755343804567552> is not allowed!", ephemeral = True)
    #             return
    #     if ctx.author.id == BOTOWNER:
    #         ok = True
    #     if not ok:
    #         await ctx.respond("You are not allowed to use this command!", ephemeral = True)
    #         return

    #     userid = user.id
    #     conn = newconn()
    #     cur = conn.cursor()
    #     cur.execute(f"SELECT mile, totpnt FROM atm WHERE userid = {userid}")
    #     t = cur.fetchall()
    #     org = 0
    #     tot = 0
    #     if len(t) == 0:
    #         cur.execute(f"INSERT INTO atm VALUES ({userid}, {mile}, 0, {mile})")
    #     else:
    #         cur.execute(f"UPDATE atm SET mile = mile + {mile}, totpnt = totpnt + {mile} WHERE userid = {userid}")
    #         org = t[0][1]
    #         tot = t[0][1] + mile
    #     conn.commit()
        
    #     orglvl = self.GetLevel(org)
    #     totlvl = self.GetLevel(tot)

    #     if totlvl != orglvl:
    #         role = None
    #         try:
    #             role = ctx.guild.get_role(orglvl)
    #             await user.remove_roles(role, reason = "ATM Driver Rank Up")
    #         except:
    #             pass
    #         try:
    #             role = ctx.guild.get_role(totlvl)
    #             await user.add_roles(role, reason = "ATM Driver Rank Up")
    #         except:
    #             pass
    #         channel = bot.get_channel(UPDID)
    #         embed = discord.Embed(title = f"Rank Up", description = f"{user.mention} has ranked up to {role.mention}!", color = TMPCLR)
    #         await channel.send(embed = embed)
        
    #     cur.execute(f"SELECT userid, totpnt, mile, eventpnt FROM atm ORDER BY totpnt DESC")
    #     t = cur.fetchall()
    #     msg = "**Driver Rankings**\n*Miles + Event Points = **Total Points***\n"
    #     lstlvl = 0
    #     for tt in t:
    #         lvl = self.GetLevel(tt[1])
    #         if lvl != lstlvl:
    #             msg += f"\n<@&{lvl}>\n"
    #             lstlvl = lvl
    #         msg += f"<@{tt[0]}> {TSeparator(tt[2])} + {TSeparator(tt[3])} = **{TSeparator(tt[1])}**\n"
        
    #     embed = discord.Embed(title = "At The Mile Logistics", description = msg, color = TMPCLR)
    #     embed.set_thumbnail(url = "https://cdn.discordapp.com/icons/929761730089877626/a_0df4f6de129299542fc0a6ca4b72d737.gif")
    #     embed.set_footer(text = f"Powered by Gecko | CharlesWithC ", icon_url = GECKOICON)
    #     embed.timestamp = datetime.now()
    #     channel = bot.get_channel(CHNID)
    #     message = await channel.fetch_message(MSGID)
    #     await message.edit(embed = embed)

    #     await ctx.respond(f"All done! {user} has been given {mile} mile points!")

    # @atm.command(name="event", description="Give event point", guild_ids = [ATMGUILD])
    # @discord.commands.permissions.has_role(929761730505080871, guild_id=ATMGUILD)
    # async def eventpnt(self, ctx, users: discord.Option(str, "Users, separate with space"),
    #         point: discord.Option(int, "Event point, can be negative, but you risk role compromise")):
    #     ok = False
    #     roles = ctx.author.roles
    #     for role in roles:
    #         if role.id in ADMINROLES:
    #             ok = True
    #         if role.id == 969755343804567552:
    #             await ctx.respond("<@&969755343804567552> is not allowed!", ephemeral = True)
    #             return
    #     if ctx.author.id == BOTOWNER:
    #         ok = True
    #     if not ok:
    #         await ctx.respond("You are not allowed to use this command!", ephemeral = True)
    #         return

    #     conn = newconn()
    #     cur = conn.cursor()

    #     channel = bot.get_channel(UPDID)
    #     users = users.split(" ")
    #     ret = ""
    #     for user in users:
    #         userid = -1
    #         user = user.replace("@!", "@")
    #         if user.startswith("<@") and user.endswith(">"):
    #             userid = user[2:-1]
    #         else:
    #             continue  
            
    #         ret += f"{user} "

    #     embed = discord.Embed(title = f"Event Point", description = f"{TSeparator(point)} points have been given to {ret}!", color = TMPCLR)
    #     mmm = await channel.send(embed = embed)
        
    #     for user in users:
    #         userid = -1
    #         user = user.replace("@!", "@")
    #         if user.startswith("<@") and user.endswith(">"):
    #             userid = user[2:-1]
    #         else:
    #             continue  

    #         cur.execute(f"SELECT eventpnt, totpnt FROM atm WHERE userid = {userid}")
    #         t = cur.fetchall()
    #         org = 0
    #         tot = 0
    #         if len(t) == 0:
    #             cur.execute(f"INSERT INTO atm VALUES ({userid}, 0, {point}, {point})")
    #         else:
    #             cur.execute(f"UPDATE atm SET eventpnt = eventpnt + {point}, totpnt = totpnt + {point} WHERE userid = {userid}")
    #             org = t[0][1]
    #             tot = t[0][1] + point
    #         conn.commit()
            
    #         orglvl = self.GetLevel(org)
    #         totlvl = self.GetLevel(tot)

    #         if totlvl != orglvl:
    #             role = None
    #             try:
    #                 role = ctx.guild.get_role(orglvl)
    #                 await user.remove_roles(role, reason = "ATM Driver Rank Up")
    #             except:
    #                 pass
    #             try:
    #                 role = ctx.guild.get_role(totlvl)
    #                 await user.add_roles(role, reason = "ATM Driver Rank Up")
    #             except:
    #                 pass
    #             embed = discord.Embed(title = f"Rank Up", description = f"<@{userid}> has ranked up to {role.mention}!", color = TMPCLR)
    #             await channel.send(embed = embed)
        
    #     cur.execute(f"SELECT userid, totpnt, mile, eventpnt FROM atm ORDER BY totpnt DESC")
    #     t = cur.fetchall()
    #     msg = "**Driver Rankings**\n*Miles + Event Points = **Total Points***\n"
    #     lstlvl = 0
    #     for tt in t:
    #         lvl = self.GetLevel(tt[1])
    #         if lvl != lstlvl:
    #             msg += f"\n<@&{lvl}>\n"
    #             lstlvl = lvl
    #         msg += f"<@{tt[0]}> {TSeparator(tt[2])} + {TSeparator(tt[3])} = **{TSeparator(tt[1])}**\n"
            
    #     embed = discord.Embed(title = "At The Mile Logistics", description = msg, color = TMPCLR)
    #     embed.set_thumbnail(url = "https://cdn.discordapp.com/icons/929761730089877626/a_0df4f6de129299542fc0a6ca4b72d737.gif")
    #     embed.set_footer(text = f"Powered by Gecko | CharlesWithC ", icon_url = GECKOICON)
    #     embed.timestamp = datetime.now()
    #     channel = bot.get_channel(CHNID)
    #     message = await channel.fetch_message(MSGID)
    #     await message.edit(embed = embed)

    #     await ctx.respond(f"All done! [Check]({mmm.jump_url})")

# bot.add_cog(AtTheMile(bot))