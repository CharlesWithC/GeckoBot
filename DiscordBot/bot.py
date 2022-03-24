# Global Trucking Discord Bot
# Version: v1.3.3

import os, asyncio, io
import discord
from discord.ext import commands,tasks
from time import time, gmtime, strftime
from datetime import datetime
from random import randint
from base64 import b64encode, b64decode
import validators

import sqlite3

from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps

BOTID = 954034331230285838
TOKEN = "OTU0MDM0MzMxMjMwMjg1ODM4.YjNPtQ.x-HkmEXRQWKGV2i2FiQldtYi4wk"
TFM = "https://radio.truckers.fm"
ADMIN_ROLE_ID = [824545574241304596, 948928675955494952, 868440317936939008, 840545310085611522]
ADMIN_USER_ID = [873178118213472286]

LOGO = "./logo.png"
BANNER_BG = "#520000"
BANNER_Y = 700 # pixel
BANNER_FONT = "./WOODCUT.TTF"

GUILD_ID = 823779955305480212
LOG_CHANNEL = (955721720440975381, 955979951226646629)
FINANCE_LOG_CHANNEL = (955721720440975381, 956362780909375538)
STAFF_CHANNEL = (823779955305480212, 857931794379833354)
RADIO_CHANNEL = [(955721720440975381, 955721720990425161), (823779955305480212, 954689640076558407)]

FINANCE_CHANNEL = [956567340106018838]
FINANCE_CHECKIN_BASE_REWARD = 200
RANK_EMOJI = ["", ":first_place:", ":second_place:", ":third_place:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":ten:"]

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents)

DATABASE_EXIST = os.path.exists("database.db")
conn = sqlite3.connect("database.db", check_same_thread = False)
cur = conn.cursor()
if not DATABASE_EXIST:
    cur.execute(f"CREATE TABLE finance (userid INT, last_checkin INT, checkin_continuity INT, \
        work_claim_time INT, work_reward INT, balance INT)")
    cur.execute(f"CREATE TABLE selfrole (guildid INT, channelid INT, msgid INT, channel INT, title TEXT, description TEXT, imgurl TEXT)")
    cur.execute(f"CREATE TABLE rolebind (guildid INT, channelid INT, msgid INT, role INT, emoji VARCHAR(64))")
    cur.execute(f"CREATE TABLE userrole (guildid INT, userid INT, roleid INT)")

def TimeDelta(timestamp): # returns human-readable delta
    delta = abs(time() - timestamp)
    if delta <= 1:
        return f"{round(delta, 3)} second"
    elif delta < 60:
        return f"{round(delta, 3)} seconds"
    else:
        if delta / 60 == 1:
            return f"1 minute"
        else:
            return f"{int(delta/60)} minutes"    

async def log(func, text):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [{func}] {text}"
    print(text)
    try:
        channel = bot.get_channel(LOG_CHANNEL[1])
        await channel.send(f"```{text}```")
    except:
        pass

async def finance_log(text):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [Finance] {text}"
    print(text)
    try:
        channel = bot.get_channel(FINANCE_LOG_CHANNEL[1])
        await channel.send(f"```{text}```")
    except:
        pass

async def LoopedTask():
    await bot.wait_until_ready()
    selfrole_fail = [] # (channelid, msgid)
    while not bot.is_closed():
        # Update Activity Status
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="TruckersFM"))

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
                    cur.execute(f"DELETE FROM selfrole WHERE channelid = {channelid} AND msgid = {msgid}")
                    cur.execute(f"DELETE FROM rolebind WHERE channelid = {channelid} AND msgid = {msgid}")
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
                                    cur.execute(f"INSERT INTO userrole VALUES ({guildid}, {user.id}, {roleid})")
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

                        
        await asyncio.sleep(10)

##### STAFF

@bot.command(name="banner")
async def GenerateBanner(ctx, name):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        img = Image.open(LOGO)
        font = ImageFont.truetype(BANNER_FONT, 50)
        draw = ImageDraw.Draw(img)
        w, h = draw.textsize(name, font=font)
        h *= 0.21
        draw.text(((img.size[0]-w)/2, BANNER_Y+h/2), text=name, fill='white', font=font)
        with io.BytesIO() as image_binary:
            img.save(image_binary, 'PNG')
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename='banner.png'))
            await log("Staff", f"{ctx.message.author.name} created a banner for {name}")

@bot.command(name="announce")
async def Announce(ctx):
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
        msg = ctx.message.content + " "
        if msg.find("<#") == -1 or msg.find("description:") == -1 or msg.find("title:") == -1:
            sample = "!announce {#channel} title: {title} description: {description} <imgurl: {imgurl}>"
            await ctx.reply(f"{ctx.message.author.name}, this is an invalid command!\nThis command works like:\n`{sample}`\nYou only need to change content in {{}}.\nYou can add line breaks or use \\n for line breaking.")
            return

        channelid = int(msg[msg.find("<#") + 2 : msg.find(">")])
        title = msg[msg.find("title:") + len("title:") : msg.find("description:")]
        description = msg[msg.find("description:") + len("description:") : msg.find("imgurl:")]
        imgurl = ""
        if msg.find("imgurl:") != -1:
            imgurl = msg[msg.find("imgurl:") + len("imgurl:"): ]
        embed = discord.Embed(title=title, description=description)
        embed.set_thumbnail(url=imgurl)

        try:
            channel = bot.get_channel(channelid)
            await channel.send(embed = embed)
            await log("Staff", f"[guild {ctx.guild} ({ctx.guild.id})] {ctx.message.author.name} made an announcement at {channel} ({channelid})")

        except Exception as e:
            await ctx.message.reply(f"{ctx.message.author.name}, it seems I cannot send message at <#{channelid}>. Make sure the channel exist and I have access to it!")
            await log("Staff", f"[guild {ctx.guild} ({ctx.guild.id})] !announce command executed by {ctx.message.author.name} failed due to {str(e)}")

@bot.command(name="selfrole")
async def SelfRole(ctx):
    # This is a complex function
    # Bot will parse command as below:
    # !selfrole {#channel} 
    # title: {title} 
    # description: {description} 
    # imgurl: {imgurl} (don't put imgurl parameter if you don't need thumbnail)
    # rolebind: {@role1} {emoji1} {@role2} {emoji2} ...
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
            cur.execute(f"INSERT INTO selfrole VALUES ({guildid}, {channelid}, {msgid}, {channelid}, '{title}', '{description}', '{imgurl}')")
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
        msgtxt = ctx.message.content.split(" ")
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

###### FUN HOUSE - FINANCE

@bot.command(name="balance")
async def FinanceBalance(ctx):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        userid = ctx.message.author.id
        cur.execute(f"SELECT balance FROM finance WHERE userid = {userid}")
        t = cur.fetchall()
        if len(t) == 0: # user not found, create user
            cur.execute(f"INSERT INTO finance VALUES ({userid}, 0, 0, 0, 0, 0)")
            t = [[0]]
        balance = t[0][0]

        cur.execute(f"SELECT userid FROM finance ORDER BY balance DESC")
        t = cur.fetchall()
        rank = 0
        for tt in t:
            rank += 1
            if userid == tt[0]:
                break
        
        embed = discord.Embed(description=f"{ctx.message.author.name}, you have **{balance}** :coin:, ranking **#{rank}**.", color=0x0000DD)
        await ctx.send(embed=embed)
        
@bot.command(name="checkin")
async def FinanceCheckIn(ctx):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        userid = ctx.message.author.id
        cur.execute(f"SELECT last_checkin, checkin_continuity, balance FROM finance WHERE userid = {userid}")
        t = cur.fetchall()
        if len(t) == 0: # user not found, create user
            cur.execute(f"INSERT INTO finance VALUES ({userid}, 0, 0, 0, 0, 0)")
            t = [[0, 0, 0]]
        
        last_checkin = t[0][0]
        checkin_continuity = t[0][1]
        balance = t[0][2]

        bonus = 0
        now = datetime.now()
        today = datetime(now.year, now.month, now.day, 0)
        last = datetime.fromtimestamp(last_checkin)
        last = datetime(last.year, last.month, last.day, 0)
        if today == last:
            embed = discord.Embed(description=f"{ctx.message.author.name}, you have already checked in today, come back tomorrow!", color=0xDD0000)
            await ctx.send(embed=embed)
        else:
            if (today - last).days == 1:
                checkin_continuity += 1
                bonus = checkin_continuity * 2 + 1
            else:
                checkin_continuity = 0
            reward = bonus + FINANCE_CHECKIN_BASE_REWARD
            balance = balance + reward
            cur.execute(f"UPDATE finance SET last_checkin = {time()} WHERE userid = {userid}")
            cur.execute(f"UPDATE finance SET checkin_continuity = {checkin_continuity} WHERE userid = {userid}")
            cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid}")
            conn.commit()
            if bonus == 0:
                embed = discord.Embed(description=f"{ctx.message.author.name}, you earned **{reward}** :coin:!", color=0x00DD00)
                await ctx.send(embed=embed)
                await finance_log(f"{ctx.message.author.name} ({ctx.message.author.id}) earned {reward} coins for checking in, current balance {balance}.")
            else:
                embed = discord.Embed(description=f"{ctx.message.author.name}, **{checkin_continuity + 1} days in a row!** You earned {reward} :coin:!", color=0x00DD00)
                await ctx.send(embed=embed)
                await finance_log(f"{ctx.message.author.name} ({ctx.message.author.id}) earned {reward} coins for checking in {checkin_continuity + 1} days in a row, current balance {balance}.")

@bot.command(name="work")
async def FinanceWork(ctx):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        userid = ctx.message.author.id
        cur.execute(f"SELECT work_claim_time, work_reward, balance FROM finance WHERE userid = {userid}")
        t = cur.fetchall()
        if len(t) == 0: # user not found, create user
            cur.execute(f"INSERT INTO finance VALUES ({userid}, 0, 0, 0, 0, 0)")
            t = [[0, 0, 0]]
        
        work_claim_time = t[0][0]
        work_reward = t[0][1]
        balance = t[0][2]

        if work_claim_time > time():
            if work_reward > 0:
                embed = discord.Embed(description=f"{ctx.message.author.name}, you haven't finished the last delivery! Come back after **{TimeDelta(work_claim_time)}**.", color=0xDD0000)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{ctx.message.author.name}, you are still resting! Come back after **{TimeDelta(work_claim_time)}**.", color=0xDD0000)
                await ctx.send(embed=embed)

        else:
            balance += work_reward
            if randint(1,24) == 24 and work_reward != 0 and time() - work_claim_time <= 600: # rest, only if re-work
                work_claim_time = int(time() + 30 * 60)
                work_reward = 0

                cur.execute(f"UPDATE finance SET work_claim_time = {work_claim_time} WHERE userid = {userid}")
                cur.execute(f"UPDATE finance SET work_reward = {work_reward} WHERE userid = {userid}")
                cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid}")
                conn.commit()

                embed = discord.Embed(description=f"{ctx.message.author.name}, you finished your delivery and earned **{work_reward}** :coin:. However you are too tired and need to have a rest. Come back after 30 minutes!", color=0x00DD00)
                await ctx.send(embed=embed)
                await finance_log(f"{ctx.message.author.name} ({ctx.message.author.id}) earned {work_reward} coins from working, current balance {balance}.")

            else: # new work
                last_reward = work_reward

                length = randint(30, 120)
                work_claim_time = int(time() + length * 60)
                work_reward = 200 + randint(-100, 100)

                cur.execute(f"UPDATE finance SET work_claim_time = {work_claim_time} WHERE userid = {userid}")
                cur.execute(f"UPDATE finance SET work_reward = {work_reward} WHERE userid = {userid}")
                cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid}")
                conn.commit()

                if last_reward != 0:
                    embed = discord.Embed(description=f"{ctx.message.author.name}, you earned **{last_reward}** :coin: from your last job. And you started working again, this job will finish in **{length} minutes** and you will earn **{work_reward}** :coin:.", color=0x00DD00)
                    await ctx.send(embed=embed)
                    await finance_log(f"{ctx.message.author.name} ({ctx.message.author.id}) earned {last_reward} coins from working, current balance {balance}.")

                else:
                    embed = discord.Embed(description=f"{ctx.message.author.name}, you started working, the job will finish in **{length} minutes** and you will earn **{work_reward}** :coin:.", color=0x00DD00)
                    await ctx.send(embed=embed)

@bot.command(name="claim")
async def FinanceClaim(ctx):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        userid = ctx.message.author.id
        cur.execute(f"SELECT work_claim_time, work_reward, balance FROM finance WHERE userid = {userid}")
        t = cur.fetchall()
        if len(t) == 0: # user not found, create user
            cur.execute(f"INSERT INTO finance VALUES ({userid}, 0, 0, 0, 0, 0)")
            t = [[0, 0, 0]]
        
        work_claim_time = t[0][0]
        work_reward = t[0][1]
        balance = t[0][2]

        if work_reward == 0:
            embed = discord.Embed(description=f"{ctx.message.author.name}, you are not working! Use !work to start working.", color=0xDD0000)
            await ctx.send(embed=embed)

        elif work_claim_time > time():
            embed = discord.Embed(description=f"{ctx.message.author.name}, you haven't finished the delivery! Come back after **{TimeDelta(work_claim_time)}**.", color=0xDD0000)
            await ctx.send(embed=embed)

        else:
            balance += work_reward

            cur.execute(f"UPDATE finance SET work_reward = 0 WHERE userid = {userid}")
            cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid}")
            conn.commit()

            embed = discord.Embed(description=f"{ctx.message.author.name}, you earned **{last_reward}** :coin: from your last job!", color=0x00DD00)
            await ctx.send(embed=embed)
            await finance_log(f"{ctx.message.author.name} ({ctx.message.author.id}) earned {last_reward} coins from working, current balance {balance}.")

@bot.command(name="richest")
async def FinanceRichest(ctx):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        cur.execute(f"SELECT userid, balance FROM finance ORDER BY balance DESC")
        t = cur.fetchall()

        rank = 0
        for tt in t:
            rank += 1
            if rank > 10:
                break
            
            msg += f"**{RANK_EMOJI[rank]} {bot.get_user(tt[0]).name}**\n:coin: {tt[1]}\n\n"
        
        embed = discord.Embed(title="**Top 10 richest members**", description=msg, color=0x0000DD)
        await ctx.send(embed=embed)

bot.loop.create_task(LoopedTask())
bot.run(TOKEN)