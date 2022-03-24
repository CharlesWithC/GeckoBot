# Global Trucking Discord Bot
# Version: v1.0.2

import os, asyncio, io
import discord
from discord.ext import commands,tasks
from time import time, gmtime, strftime
from datetime import datetime
from random import randint
from base64 import b64encode, b64decode

import sqlite3

from PIL import Image
from PIL import ImageFont, ImageDraw, ImageOps

BOTID = 954034331230285838
TOKEN = "OTU0MDM0MzMxMjMwMjg1ODM4.YjNPtQ.x-HkmEXRQWKGV2i2FiQldtYi4wk"
TFM = "https://radio.truckers.fm"
ADMIN_ROLE_ID = [955724878043029505, 955724930748665896, 955724967318802473]
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

FINANCE_CHANNEL = [-1]
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
    cur.execute(f"CREATE TABLE selfrole (guildid INT, channelid INT, msgid INT, channel INT, title TEXT, description TEXT)")
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
        await channel.send(f"`{text}`")
    except:
        pass

async def finance_log(func, text):
    text = f"[{strftime('%Y-%m-%d %H:%M:%S', gmtime())}] [Finance] {text}"
    print(text)
    try:
        channel = bot.get_channel(FINANCE_LOG_CHANNEL[1])
        await channel.send(f"`{text}`")
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
                        embed = discord.Embed(title=f"Staff Notice", description=f"A self-role post (message id: `{msgid}`) with role-binds {rolebindtxt} sent in <#{channelid}> ({channelid}) at server {guild} ({guildid}) has expired because the bot either cannot view the channel, or cannot find the message. The bot will no longer assign roles on reactions.", url=f"https://discord.com/channels/{guildid}/{channelid}/{msgid}", color=0x2222DD)
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
                    emoji = b64encode(reaction.emoji.encode()).decode()
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
                                    await log("SelfRole", f"Cannot assign {role} ({roleid}) for user {user.id}, user reaction removed (server {guild} ({guildid}))")
                                    await message.remove_reaction(reaction.emoji, user)
                                    continue
                                cur.execute(f"SELECT * FROM userrole WHERE userid = {user.id} AND roleid = {roleid}")
                                p = cur.fetchall()
                                if len(p) == 0:
                                    await log("SelfRole", f"Added {role} ({roleid}) role to user {user.id} at server {guild} ({guildid})")
                                    cur.execute(f"INSERT INTO userrole VALUES ({guildid}, {user.id}, {roleid})")
                            inrole.append(user.id)
                    conn.commit()
                    cur.execute(f"SELECT userid FROM userrole WHERE roleid = {roleid}")
                    preusers = cur.fetchall()
                    for data in preusers:
                        preuser = data[0]
                        if not preuser in inrole:
                            await log("SelfRole", f"Removed {role} ({roleid}) role from user {preuser} at server {guild} ({guildid})")
                            cur.execute(f"DELETE FROM userrole WHERE userid = {preuser} AND roleid = {roleid} AND guildid = {guildid}")
                            try:
                                role = discord.utils.get(guild.roles, id=roleid)
                                user = discord.utils.get(guild.members, id=preuser)
                                await user.remove_roles(role)
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

@bot.command(name="selfrole")
async def SelfRole(ctx):
    # This is a complex function
    # Bot will parse command as below:
    # !selfrole {#channel} title: {title} description: {description} rolebind: {@role1} {emoji1} {@role2} {emoji2} ...
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
            sample = "!selfrole {#channel} title: {title} description: {description} rolebind: {@role1} {emoji1} {@role2} {emoji2} ..."
            await ctx.reply(f"{ctx.message.author.name}, this is an invalid command!\nThis command works like:\n`{sample}`\nYou only need to change content in {{}}.\nYou can add line breaks or use \\n for line breaking.")
            return

        channelid = int(msg[msg.find("<#") + 2 : msg.find(">")])
        title = msg[msg.find("title:") + len("title:") : msg.find("description:")]
        if title.startswith(" "):
            title = title[1:]
        description = msg[msg.find("description:") + len("description:") : msg.find("rolebind:")]
        if description.startswith(" "):
            description = description[1:]
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
            message = await channel.send(embed=embed)
            for data in rolebind:
                await message.add_reaction(data[1])
            await ctx.reply(f"{ctx.message.author.name}, self-role message posted at <#{channelid}>!")

            title = b64encode(title.encode()).decode()
            description = b64encode(description.encode()).decode()
            msgid = message.id
            cur.execute(f"INSERT INTO selfrole VALUES ({guildid}, {channelid}, {msgid}, {channelid}, '{title}', '{description}')")
            for data in rolebind:
                cur.execute(f"INSERT INTO rolebind VALUES ({guildid}, {channelid}, {msgid}, {data[0]}, '{b64encode(data[1].encode()).decode()}')")
            conn.commit()

            await log("Staff", f"{ctx.message.author.name} created a self-role post at <#{channelid}> (server {ctx.guild} ({ctx.guild.id})), with role-binding: {rolebindtxt}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            await ctx.reply(f"{ctx.message.author.name}, it seems the bot cannot send message at <#{channelid}>. Make sure the channel exist and the bot has access to it!")

            await log("Staff", f"!selfrole command execution by {ctx.message.author.name} failed due to {str(e)}")

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
        
        embed = discord.Embed(description=f"{ctx.message.author.name}, you have {balance} :coin:, ranking #{rank}.", color=0x2222DD)
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
            embed = discord.Embed(description=f"{ctx.message.author.name}, you have already checked in today, come back tomorrow!", color=0xDD2222)
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
                embed = discord.Embed(description=f"{ctx.message.author.name}, you earned {reward} :coin:!", color=0x22DD22)
                await ctx.send(embed=embed)
                await finance_log(f"{ctx.message.author.name} earned {reward} coins for checking in, current balance {balance}.")
            else:
                embed = discord.Embed(description=f"{ctx.message.author.name}, **{checkin_continuity + 1} days in a row!** You earned {reward} :coin:!", color=0x22DD22)
                await ctx.send(embed=embed)
                await finance_log(f"{ctx.message.author.name} earned {reward} coins for checking in {checkin_continuity + 1} days in a row, current balance {balance}.")

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
                embed = discord.Embed(description=f"{ctx.message.author.name}, you haven't finished the last delivery! Come back after {TimeDelta(work_claim_time)}.", color=0xDD2222)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f"{ctx.message.author.name}, you are still resting! Come back after {TimeDelta(work_claim_time)}.", color=0xDD2222)
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

                embed = discord.Embed(description=f"{ctx.message.author.name}, you finished your delivery and earned {work_reward} :coin:. However you are too tired and need to have a rest. Come back after 30 minutes!", color=0x22DD22)
                await ctx.send(embed=embed)
                await finance_log(f"{ctx.message.author.name} earned {work_reward} coins from working, current balance {balance}.")

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
                    embed = discord.Embed(description=f"{ctx.message.author.name}, you earned {last_reward} from your last job. And you started working again, this job will finish in {length} minutes and you will earn {work_reward} :coin:.", color=0x22DD22)
                    await ctx.send(embed=embed)
                    await finance_log(f"{ctx.message.author.name} earned {last_reward} coins from working, current balance {balance}.")

                else:
                    embed = discord.Embed(description=f"{ctx.message.author.name}, you started working, the job will finish in {length} minutes and you will earn {work_reward} :coin:.", color=0x22DD22)
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
            embed = discord.Embed(description=f"{ctx.message.author.name}, you are not working! Use !work to start working.", color=0xDD2222)
            await ctx.send(embed=embed)

        elif work_claim_time > time():
            embed = discord.Embed(description=f"{ctx.message.author.name}, you haven't finished the delivery! Come back after {TimeDelta(work_claim_time)}.", color=0xDD2222)
            await ctx.send(embed=embed)

        else:
            balance += work_reward

            cur.execute(f"UPDATE finance SET work_reward = 0 WHERE userid = {userid}")
            cur.execute(f"UPDATE finance SET balance = {balance} WHERE userid = {userid}")
            conn.commit()

            embed = discord.Embed(description=f"{ctx.message.author.name}, you earned {last_reward} from your last job!", color=0x22DD22)
            await ctx.send(embed=embed)
            await finance_log(f"{ctx.message.author.name} earned {last_reward} coins from working, current balance {balance}.")

@bot.command(name="richest")
async def FinanceRichest(ctx):
    if ctx.message.author.id == BOTID:
        return
    if not ctx.message.channel.id in FINANCE_CHANNEL and not FINANCE_CHANNEL == [-1]:
        return
    async with ctx.typing():
        cur.execute(f"SELECT userid, balance FROM finance ORDER BY balance DESC")
        t = cur.fetchall()

        msg = "**Top 10 richest Global Trucking members**\n\n"
        rank = 0
        for tt in t:
            rank += 1
            if rank > 10:
                break
            
            msg += f"**{RANK_EMOJI[rank]} {bot.get_user(tt[0]).name}**\n:coin: {tt[1]}\n\n"
        
        embed = discord.Embed(description=msg, color=0x2222DD)
        await ctx.send(embed=embed)

bot.loop.create_task(LoopedTask())
bot.run(TOKEN)