# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Cryptography

import os, asyncio
import discord
from discord.ext import commands
import base64
from time import time
import requests

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

from bot import bot
from settings import *
from functions import *
from db import newconn

HEX = ["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F"]

def genpwd(userid):
    userid = str(userid)
    ruserid = userid[::-1]
    t = ""
    for i in range(len(userid)):
        t += userid[i] + ruserid[i]
    s = ""
    for i in range(len(t)):
        if i + 1 < len(t):
            p = int(t[i])*10 + int(t[i+1])
            if int(t[i]) == 1 and int(t[i+1]) <= 5:
                s += HEX[10+int(t[i+1])]
                i += 1
            elif p >= 32 and p <= 99:
                s += chr(p)
                i += 1
        else:
            s += HEX[int(t[i])]  
    s = s.encode()
    for _ in range(3):
        s = base64.b64encode(s)
    key = SHA256.new(s).digest()
    return key

def encrypt(userid, source, encode=True):
    if type(source) == str:
        source = source.encode()
    key = genpwd(userid)
    key = SHA256.new(key).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = AES.block_size - len(source) % AES.block_size  # calculate needed padding
    source += bytes([padding]) * padding  # Python 2.x: source += chr(padding) * padding
    data = IV + encryptor.encrypt(source)  # store the IV at the beginning and encrypt
    return base64.b64encode(data).decode("latin-1") if encode else data

def decrypt(userid, source, decode=True):
    key = genpwd(userid)
    if decode:
        source = base64.b64decode(source.encode("latin-1"))
    key = SHA256.new(key).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = source[:AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])  # decrypt
    padding = data[-1]  # pick the padding value from the end; Python 2.x: ord(data[-1])
    if data[-padding:] != bytes([padding]) * padding:  # Python 2.x: chr(padding) * padding
        raise ValueError("Invalid padding...")
    return data[:-padding].decode()  # remove the padding

@bot.slash_command(name="encrypt", description="Encrypt a message")
async def EncryptMessage(ctx, receiver: discord.Option(str, "Receiver of the message, only he / she could decrypt the message", required = True),
        content: discord.Option(str, "Content of message", required = True)):
        
    if not receiver.startswith("<@!") or not receiver.endswith(">"):
        await ctx.respond("Invalid receiver! You must tag the user.", ephemeral = True)
        return
    
    receiver = receiver[3:-1]
    try:
        receiver = int(receiver)
    except:
        await ctx.respond("Invalid receiver! You must tag the user.", ephemeral = True)
        return
    
    if len(content) > 500:
        await ctx.respond("Content can be at most 500 characters long.", ephemeral = True)
        return

    s = encrypt(receiver, str(receiver) + content)
    if len(s) > 1800:
        await ctx.respond("Content too long.", ephemeral = True)
        return

    await ctx.respond(f"Encrypted message to <@!{receiver}>:\n||{s}||", ephemeral = True)

@bot.slash_command(name="decrypt", description="Decrypt a message")
async def DecryptMessage(ctx, content: discord.Option(str, "Encrypted message sent to you", required = True)):
    try:
        s = decrypt(ctx.user.id, content)
    except:
        await ctx.respond("Not a message to you.", ephemeral = True)
        return
    if not s.startswith(str(ctx.user.id)):
        await ctx.respond("Not a message to you.", ephemeral = True)
        return
    s = s[len(str(ctx.user.id)):]
    await ctx.respond(f"Decrypted message:\n||{s}||", ephemeral = True)