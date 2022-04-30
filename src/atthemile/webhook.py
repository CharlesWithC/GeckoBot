# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# At The Mile Logistics VTC exclusive

from flask import Flask, request
from bot import tbot
import threading
import asyncio
atmflask = Flask(__name__)

ATMGUILD = 929761730089877626
APPLICANT = 942478809175830588

@atmflask.route("/atm/applicant")
def ATMapplicant():
    guild = tbot.get_guild(ATMGUILD)
    role = guild.get_role(APPLICANT)
    userid = request.args.get("userid")
    channel = tbot.get_channel(941562364174688256)
    try:
        userid = int(userid)
    except:
        tbot.loop.create_task(channel.send(f"Invalid user ID: {userid}. Applicant role not given."))
        return {"success": False, "message": "Invalid user ID!"}
    user = guild.get_member(userid)
    if user is None:
        tbot.loop.create_task(channel.send(f"User not found: {userid}. Applicant role not given."))
        return {"success": False, "msg": "User not found!"}
    tbot.loop.create_task(user.add_roles(role, reason = "Applicant from website"))
    return {"success": True}

threading.Thread(target = atmflask.run, args = ("127.0.0.1", 4001)).start()