# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Fun House - Connect Four

import os, asyncio
import discord
from discord.commands import CommandPermission, SlashCommandGroup
from discord.ui import Button, View
from discord.ext import commands
from time import time, gmtime, strftime
from datetime import datetime
from random import randint

from bot import bot
from settings import *
from functions import *
from db import newconn

WHITE = ":white_circle:"
RED = ":red_circle:"
BLUE = ":blue_circle:"
NUM = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
TNUM = "".join(NUM)

class ConnectFourJoinButton(Button):
    def __init__(self, label, custom_id, disabled = False):
        super().__init__(
            label=label,
            style=BTNSTYLE["green"],
            custom_id=custom_id,
            disabled=disabled
        )  

    async def callback(self, interaction: discord.Interaction):    
        custom_id = self.custom_id
        if not custom_id.startswith("GeckoConnectFourGame"):
            return
        d = custom_id.split("-")
        red = int(d[1])
        if red == interaction.user.id and red != BOTOWNER: # allow dev to test
            await interaction.response.send_message(f"You cannot play with yourself.", ephemeral = True)
            return
        if int(d[2]) != 0 and interaction.user.id != int(d[2]):
            await interaction.response.send_message(f"The match starter selected <@{d[2]}> to be their opponent and you cannot join.", ephemeral = True)
            return
        blue = interaction.user.id
        bet = int(d[3])
        channelid = interaction.channel_id
        channel = interaction.channel
        guildid = interaction.guild_id

        conn = newconn()
        cur = conn.cursor()

        # check if game already started
        cur.execute(f"SELECT * FROM connectfour WHERE customid = '{custom_id}'")
        p = cur.fetchall()
        if len(p) > 0:
            await interaction.response.send_message(f"The game has already started.", ephemeral = True)
            return

        # check bet
        if bet > 0:
            cur.execute(f"SELECT balance FROM finance WHERE userid = {blue} AND guildid = {guildid}")
            t = cur.fetchall()
            if len(t) == 0 or t[0][0] < bet:
                await ctx.respond(f"You don't have enough coins to bet.", ephemeral = True)
                return
        
        # update database
        cur.execute(f"SELECT COUNT(*) FROM connectfour")
        t = cur.fetchall()
        gameid = 1
        if len(t) > 0:
            gameid = t[0][0] + 1
        state = '0'*42
        cur.execute(f"INSERT INTO connectfour VALUES ({gameid}, {red}, {blue}, {guildid}, {channelid}, 0, {bet}, '1|{state}', '{custom_id}', {int(time())})")
        conn.commit()

        # update message status
        view = View(timeout = 1)
        uniq = f"{randint(1,100000)}{int(time()*100000)}"
        customid = f"GeckoConnectFourGame-{uniq}"
        button = ConnectFourJoinButton(f"Preparing Match", customid, disabled = True)
        view.add_item(button)
        await interaction.response.edit_message(content = "Wait a moment, the game is being prepared...", view = view)
        cur.execute(f"DELETE FROM buttonview WHERE customid = '{customid}'")
        conn.commit()

        # start game
        msg = f"**Connect Four #{gameid}**\n{RED} <@{red}> vs {BLUE} <@{blue}>\n{RED} <@{red}> turn\n\n" + TNUM + "\n"
        msg += (WHITE * 7 + "\n") * 6
        msg = await channel.send(msg)
        for emoji in NUM:
            await msg.add_reaction(emoji)

        await interaction.message.delete()

        cur.execute(f"UPDATE connectfour SET msgid = {msg.id} WHERE gameid = {gameid}")
        conn.commit()

class ConnectFour(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    four = SlashCommandGroup("four", "Connect Four Game")

    @four.command(name="start", description="Connect Four - Start a game")
    async def start(self, ctx, opponent: discord.Option(discord.User, "Select an opponent and only he / she could join.", required = False),
        bet: discord.Option(int, "How many coins to bet, default 0", required = False, min_value=0, max_value=10000)):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guildid = ctx.guild.id

        conn = newconn()
        cur = conn.cursor()
        
        guildid = 0
        if not ctx.guild is None:
            guildid = ctx.guild.id

            cur.execute(f"SELECT channelid FROM channelbind WHERE guildid = {guildid} AND category = 'four'")
            t = cur.fetchall()
            if len(t) == 0:
                await ctx.respond(f"{ctx.author.name}, staff haven't set up a connect four game channel yet! Tell them to use `/setchannel four {{#channel}}` to set it up!", ephemeral = True)
                return
            if t[0][0] != ctx.channel.id and t[0][0] != 0:
                await ctx.respond(f"This is not the channel for connect four games!", ephemeral = True)
                return
        
        if opponent is None:
            opponent = 0
        else:
            opponent = opponent.id
        
        if bet is None:
            bet = 0
        else:
            cur.execute(f"SELECT balance FROM finance WHERE userid = {ctx.author.id} AND guildid = {ctx.guild.id}")
            t = cur.fetchall()
            if len(t) == 0 or t[0][0] < bet:
                await ctx.respond(f"You don't have enough coins to bet.", ephemeral = True)
                return
        
        additional = "\n"
        if bet > 0:
            additional = f"The match starter bet {bet} :coin:, and their opponent have to pay {bet} :coin: to join.\n"
        
        view = View()
        uniq = f"{randint(1,100000)}{int(time()*100000)}"
        customid = f"GeckoConnectFourGame-{ctx.author.id}-{opponent}-{bet}-{uniq}"
        button = ConnectFourJoinButton(f"Join Match", customid)
        view.add_item(button)
        if opponent != 0:
            await ctx.respond(content = f"<@{opponent}>, you are invited to join **Connect Four** match started by <@{ctx.author.id}>.\n{additional}Press 'Join Match' to start the game.", view = view)
        else:
            await ctx.respond(content = f"<@{ctx.author.id}> started a **Connect Four** match.\n{additional}Press 'Join Match' to start the game.", view = view)
        cur.execute(f"INSERT INTO buttonview VALUES ({int(time())}, '{customid}')")
        conn.commit()

    @four.command(name="result", description="Connect Four - Get the result (including the final state) of a given game.")
    async def result(self, ctx, gameid: discord.Option(int, "Game ID", required = True)):
        await ctx.defer()    
        if ctx.guild is None:
            await ctx.respond("You can only run this command in guilds!")
            return
        guildid = ctx.guild.id

        conn = newconn()
        cur = conn.cursor()

        try:
            gameid = int(gameid)
        except:
            await ctx.respond(f"{gameid} is not a valid game ID.", ephemeral = True)
            return

        cur.execute(f"SELECT COUNT(*) FROM connectfour")
        t = cur.fetchall()
        if len(t) == 0 or t[0][0] < gameid:
            await ctx.respond(f"{gameid} is not a valid game ID.", ephemeral = True)
            return
        
        cur.execute(f"SELECT * FROM connectfour WHERE ABS(gameid) = {gameid} AND guildid = {guildid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"The game didn't happen in this guild and you cannot access it.", ephemeral = True)
            return

        cur.execute(f"SELECT red, blue, state FROM connectfour WHERE gameid = -{gameid} AND guildid = {guildid}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"The game hasn't ended yet.", ephemeral = True)
            return
        
        red = t[0][0]
        blue = t[0][1]
        result = f"{RED} <@{red}> vs {BLUE} <@{blue}>\n"
        state = t[0][2]
        won = state.split("|")[0]
        if won == "-1":
            result += f"{RED} <@{red}> won\n"
        elif won == "-2":
            result += f"{BLUE} <@{blue}> won\n"
        elif won == "-3":
            result += f"**Draw**\n"
        elif won == "0":
            result += f"**Game cancelled due to inactivity**\n"
        result += "\nFinal state:\n"
        state = state.split("|")[1]
        pstate = ""
        for i in range(6):
            pstate = state[i*7:(i+1)*7] + "\n" + pstate
        pstate = pstate.replace("0", WHITE)
        pstate = pstate.replace("1", RED)
        pstate = pstate.replace("2", BLUE)
        pstate = TNUM + "\n" + pstate
        result += pstate
        embed = discord.Embed(title = f"Connect Four - Game #{gameid}", description=result, color = GECKOCLR)

        await ctx.respond(embed = embed)
    
    @four.command(name="leaderboard", description="Connect Four - Get the leaderboard.")
    async def leaderboard(self, ctx, sortby: discord.Option(str, "Sort by: ", required = False, choices = ["earnings", "wins", "losses"])):
        await ctx.defer()    
        conn = newconn()
        cur = conn.cursor()

        if sortby == "earnings":
            sortby = "earning"
        elif sortby == "wins":
            sortby = "won"
        elif sortby == "losses":
            sortby = "lost"
        if not sortby in ["earning", "won", "lost"]:
            sortby = "won" # decided by copilot
        cur.execute(f"SELECT userid, {sortby} FROM connectfour_leaderboard ORDER BY {sortby} DESC LIMIT 10")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"Nobody has played the game.", ephemeral = True)
            return
        
        result = ""
        for i in range(len(t)):
            if sortby == "earning":
                result += f"{RANK_EMOJI[i+1]} **{bot.get_user(t[i][0]).name}**\n:coin: {t[i][1]}\n"
            elif sortby == "won":
                result += f"{RANK_EMOJI[i+1]} **{bot.get_user(t[i][0]).name}**\n:medal: {t[i][1]}\n"
            elif sortby == "lost":
                result += f"{RANK_EMOJI[i+1]} **{bot.get_user(t[i][0]).name}**\n:x: {t[i][1]}\n"
            
        embed = discord.Embed(title = "Connect Four - Leaderboard", description=result, color = GECKOCLR)
        embed.set_footer(text = "The leaderboard includes all players, throughout all guilds.", icon_url = GECKOICON)
        await ctx.respond(embed = embed)
    
    @four.command(name="statistics", description="Connect Four - Get your statistics.")
    async def statistics(self, ctx):
        await ctx.defer()    
        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"SELECT won, lost, draw, earning FROM connectfour_leaderboard WHERE userid = {ctx.author.id}")
        t = cur.fetchall()
        if len(t) == 0:
            await ctx.respond(f"You haven't played the game.", ephemeral = True)
            return
        
        result = f"**{ctx.author.name}**\n"
        embed = discord.Embed(title = f"{ctx.author}", description="```Connect Four - Statistics```", color = GECKOCLR)
        if not ctx.author.avatar is None:
            embed.set_thumbnail(url = ctx.author.avatar.url)
        embed.add_field(name = "Games", value = f"```{t[0][0]+t[0][1]+t[0][2]}```", inline = True)
        embed.add_field(name = chr(173), value = chr(173))
        embed.add_field(name = "Earnings", value = f"```{t[0][3]}```", inline = True)

        embed.add_field(name = "Wins", value = f"```{t[0][0]}```", inline = True)
        embed.add_field(name = "Draws", value = f"```{t[0][2]}```", inline = True)
        embed.add_field(name = "Losses", value = f"```{t[0][1]}```", inline = True)

        embed.set_footer(text = "The statistics include all games played, throughout all guilds.", icon_url = GECKOICON)
        await ctx.respond(embed = embed)

async def ClearExpiredGame():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT gameid, chnid, msgid FROM connectfour WHERE lastop < {int(time())-300} AND gameid > 0")
        t = cur.fetchall()
        for tt in t:
            gameid = tt[0]
            chnid = tt[1]
            msgid = tt[2]
            cur.execute(f"SELECT state FROM connectfour WHERE ABS(gameid) = {gameid}")
            t = cur.fetchall()
            state = t[0][0]
            p = stats.split("|")
            if len(p) == 0:
                state = "0|" + state
            else:
                state = "0|" + p[1]
            cur.execute(f"UPDATE connectfour SET state = '{state}', gameid = -ABS(gameid) WHERE ABS(gameid) = {gameid}")
            conn.commit()
            channel = bot.get_channel(chnid)
            if channel is None:
                continue
            try:
                message = await channel.fetch_message(msgid)
                await message.edit(f":x: The game has been cancelled due to inactivity.")
                await message.clear_reactions()
            except:
                pass
        
        cur.execute(f"DELETE FROM buttonview WHERE buttonid < {time()-3600} AND customid LIKE 'GeckoConnectFourGame%'")
        conn.commit()
        await asyncio.sleep(30)

def UpdateLeaderboard(won, lost, bet, draw = False):
    conn = newconn()
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM connectfour_leaderboard WHERE userid = {won}")
    t = cur.fetchall()
    if len(t) == 0:
        if draw:
            cur.execute(f"INSERT INTO connectfour_leaderboard VALUES ({won}, 0, 0, 1, {bet})")
        else:
            cur.execute(f"INSERT INTO connectfour_leaderboard VALUES ({won}, 1, 0, 0, {bet})")
    else:
        if draw:
            cur.execute(f"UPDATE connectfour_leaderboard SET draw = draw + 1 WHERE userid = {won}")
        else:
            cur.execute(f"UPDATE connectfour_leaderboard SET won = won + 1, earning = earning + {bet} WHERE userid = {won}")

    cur.execute(f"SELECT * FROM connectfour_leaderboard WHERE userid = {lost}")
    t = cur.fetchall()
    if len(t) == 0:
        if draw:
            cur.execute(f"INSERT INTO connectfour_leaderboard VALUES ({lost}, 0, 0, 1, -{bet})")
        else:
            cur.execute(f"INSERT INTO connectfour_leaderboard VALUES ({lost}, 0, 1, 0, -{bet})")
    else:
        if draw:
            cur.execute(f"UPDATE connectfour_leaderboard SET draw = draw + 1 WHERE userid = {lost}")
        else:
            cur.execute(f"UPDATE connectfour_leaderboard SET lost = lost + 1, earning = earning - {bet} WHERE userid = {lost}")

    conn.commit()

async def ConnectFourUpdate():
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    channel = None
    gameid = 0
    while not bot.is_closed():    
        conn = newconn()
        cur = conn.cursor()    
        cur.execute(f"SELECT gameid, red, blue, guildid, chnid, msgid, state, bet FROM connectfour WHERE gameid > 0 AND msgid != ''")
        d = cur.fetchall()
        for dd in d:
            try:
                gameid = dd[0]
                red = dd[1]
                blue = dd[2]
                guildid = dd[3]
                chnid = dd[4]
                msgid = dd[5]
                state = dd[6]
                bet = dd[7]
                vs = f"**Connect Four #{gameid}**\n{RED} <@{red}> vs {BLUE} <@{blue}>\n"
                
                channel = bot.get_channel(chnid)

                current = state.split("|")[0]
                state = state.split("|")[1]

                message = await channel.fetch_message(msgid)

                col = 0
                row = 0

                t1 = time()
                if current == "1": # red
                    # get red reaction
                    t = 0
                    col = 0
                    cnt = 0
                    e = None
                    u = None
                    for reaction in message.reactions:
                        if reaction.count == 1:
                            continue
                        for user in await reaction.users().flatten():
                            if user.id == red:
                                if reaction.emoji in NUM:
                                    col = NUM.index(reaction.emoji)
                                    await message.remove_reaction(reaction.emoji, user)
                                    e = reaction.emoji
                                    u = user
                                cnt += 1
                                
                    if cnt > 1 or cnt == 0:
                        continue

                    # get row
                    row = -1
                    for i in range(6):
                        if state[i*7+col] == "0":
                            row = i
                            break
                    if row == -1:
                        continue

                    # update state
                    state = state[:row*7+col] + "1" + state[row*7+col+1:]
                
                elif current == "2": # blue
                    # get blue reaction
                    t = 0
                    col = 0
                    cnt = 0
                    e = None
                    u = None
                    for reaction in message.reactions:
                        if reaction.count == 1:
                            continue
                        for user in await reaction.users().flatten():
                            if user.id == blue:
                                if reaction.emoji in NUM:
                                    col = NUM.index(reaction.emoji)
                                    await message.remove_reaction(reaction.emoji, user)
                                    e = reaction.emoji
                                    u = user
                                cnt += 1

                    if cnt == 0 or cnt > 1:
                        continue

                    # get row
                    row = -1
                    for i in range(6):
                        if state[i*7+col] == "0":
                            row = i
                            break
                    if row == -1:
                        continue

                    # update state
                    state = state[:row*7+col] + "2" + state[row*7+col+1:]

                # state readable (current row)
                pstate = ""
                for i in range(6):
                    pstate = state[i*7:(i+1)*7] + "\n" + pstate
                pstate = pstate.replace("0", WHITE)
                pstate = pstate.replace("1", RED)
                pstate = pstate.replace("2", BLUE)
                pstate = TNUM + "\n" + pstate
                
                # convert to matrix for easier check
                matrix = []
                for i in range(6):
                    matrix.append(state[i*7:i*7+7])
                
                cur.execute(f"UPDATE connectfour SET lastop = {int(time())} WHERE gameid = {gameid}")
                conn.commit()

                # check if four in a row or column or diagonal
                redwon = False
                bluewon = False
                for i in range(6):
                    for j in range(7-3):
                        if matrix[i][j] == matrix[i][j+1] == matrix[i][j+2] == matrix[i][j+3] == "1":
                            redwon = True
                        if matrix[i][j] == matrix[i][j+1] == matrix[i][j+2] == matrix[i][j+3] == "2":
                            bluewon = True
                if redwon + bluewon == 0:
                    # check column
                    for i in range(6-3):
                        for j in range(7):
                            if matrix[i][j] == matrix[i+1][j] == matrix[i+2][j] == matrix[i+3][j] == "1":
                                redwon = True
                            if matrix[i][j] == matrix[i+1][j] == matrix[i+2][j] == matrix[i+3][j] == "2":
                                bluewon = True
                if redwon + bluewon == 0:
                    # check diagonal
                    # left to right
                    for i in range(6-3):
                        for j in range(7-3):
                            if matrix[i][j] == matrix[i+1][j+1] == matrix[i+2][j+2] == matrix[i+3][j+3] == "1":
                                redwon = True
                            if matrix[i][j] == matrix[i+1][j+1] == matrix[i+2][j+2] == matrix[i+3][j+3] == "2":
                                bluewon = True
                    # right to left
                    for i in range(6-3):
                        for j in range(3, 7):
                            if matrix[i][j] == matrix[i+1][j-1] == matrix[i+2][j-2] == matrix[i+3][j-3] == "1":
                                redwon = True
                            if matrix[i][j] == matrix[i+1][j-1] == matrix[i+2][j-2] == matrix[i+3][j-3] == "2":
                                bluewon = True

                gameend = False
                if redwon:
                    additional = "!"
                    if bet > 0:
                        # deduct blue bet coins, add red bet coins
                        cur.execute(f"UPDATE finance SET balance = balance - {bet} WHERE userid = {blue}")
                        cur.execute(f"UPDATE finance SET balance = balance + {bet} WHERE userid = {red}")
                        additional = f" and earned {bet} :coin: from bet!"
                    UpdateLeaderboard(red, blue, bet)
                    await message.edit(f"{vs}{RED} <@{red}> won the game" + additional + "\n\n" + pstate)
                    gameend = True
                elif bluewon:
                    additional = "!"
                    if bet > 0:
                        # deduct red bet coins, add blue bet coins
                        cur.execute(f"UPDATE finance SET balance = balance - {bet} WHERE userid = {red}")
                        cur.execute(f"UPDATE finance SET balance = balance + {bet} WHERE userid = {blue}")
                        additional = f" and earned {bet} :coin: from bet!"
                    UpdateLeaderboard(blue, red, bet)
                    await message.edit(f"{vs}{BLUE} <@{blue}> won the game" + additional + "\n\n" + pstate)
                    gameend = True
                elif state.count("0") == 0:
                    if bet > 0:
                        additional = f"\nNobody has won or lost a coin."
                    UpdateLeaderboard(red, blue, 0, draw = True)
                    await message.edit(f"{vs}{BLUE} **Draw**" + additional + "\n\n" + pstate)
                    gameend = True
                
                if gameend:
                    # clear reaction
                    await message.clear_reactions()

                    # update database
                    if redwon:
                        cur.execute(f"UPDATE connectfour SET state = '-1|{state}', gameid = -gameid WHERE gameid = {gameid}")
                    elif bluewon:
                        cur.execute(f"UPDATE connectfour SET state = '-2|{state}', gameid = -gameid WHERE gameid = {gameid}")
                    elif state.count("0") == 0:
                        cur.execute(f"UPDATE connectfour SET state = '-3|{state}', gameid = -gameid WHERE gameid = {gameid}")
                else:
                    if current == "1":
                        cur.execute(f"UPDATE connectfour SET state = '2|{state}' WHERE gameid = {gameid}")
                        await message.edit(f"{vs}{BLUE} <@{blue}>'s turn\n\n{pstate}")
                    elif current == "2":
                        cur.execute(f"UPDATE connectfour SET state = '1|{state}' WHERE gameid = {gameid}")
                        await message.edit(f"{vs}{RED} <@{red}>'s turn\n\n{pstate}")
                conn.commit()

            except Exception as e:
                import traceback
                traceback.print_exc()
                # try:
                #     # cur.execute(f"UPDATE connectfour SET gameid = -gameid WHERE gameid = {gameid}")
                #     # conn.commit()
                #     await channel.send("Game error occurred. This game is no longer available.")
                # except:
                #     pass
                try:
                    await log("ERROR", f"Connect Four error {str(e)}")
                except:
                    pass

        await asyncio.sleep(1)

bot.add_cog(ConnectFour(bot))
bot.loop.create_task(ClearExpiredGame())
bot.loop.create_task(ConnectFourUpdate())