# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Retrieve player map data each 10 seconds.

import requests, json
from fuzzywuzzy import process
from db import newconn
from functions import *
import time
from settings import *
from datetime import datetime

nameid = {}
traffic = {}
location = {}
country = {}

config_txt = ""
if sys.argv[0].endswith("main.py"):
    config_txt = open("./bot.conf","r").read()
elif sys.argv[0].endswith("test.py"):
    config_txt = open("./test.conf","r").read()
config = json.loads(config_txt)
STEAMKEY = config["steam"]

def GetSteamUser(steamid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT steamdata FROM steam WHERE steamid = {steamid} AND lastupd > {int(time.time())-10800}")
    t = cur.fetchall()
    if len(t) > 0:
        d = json.loads(b64d(t[0][0]))
        return d
    r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAMKEY}&steamids={steamid}")
    d = json.loads(r.text)["response"]["players"][0]
    cur.execute(f"DELETE FROM steam WHERE steamid = {steamid}")
    cur.execute(f"INSERT INTO steam VALUES ({steamid}, '{d['personaname']}', '{b64e(json.dumps(d))}', {int(time.time())})")
    conn.commit()
    return d

def SearchName(name):
    res = process.extract(name, nameid.keys(), limit = 5)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret

def Name2ID(name):
    if name in nameid.keys():
        return nameid[name]
    return None

def GetMapLoc(mpid):
    r = requests.get(f"https://api.truckyapp.com/v3/map/online?playerID={mpid}")
    if r.status_code != 200:
        return None
    d = json.loads(r.text)["response"]
    if not d["online"]:
        return None
    return {"name": d["name"], "mpid": d["mp_id"], "playerid": d["p_id"], "x": d["x"], "y": d["y"], "heading": d["heading"], \
        "server": d["serverDetails"]["name"], "distance": round(d["location"]["distance"],2), "time": d["time"],\
            "city": d["location"]["poi"]["realName"], "country": d["location"]["poi"]["country"]}

def GetVTCPosition(vtcid, mid):
    r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}/members")
    if r.status_code == 200:
        d = json.loads(r.text)
        if not d["error"]:
            d = d["response"]["members"]
            for dd in d:
                if dd["id"] == mid:
                    return ": "+dd["role"]
            return ""
        elif d["descriptor"] == "PRIVATE_MEMBERS":
            return ""

def GetHRData(mpid):
    r = requests.get(f"https://api.truckersmp.com/v2/player/{mpid}")
    if r.status_code != 200:
        return None
    d = json.loads(r.text)
    if d["error"]:
        return None
    d = d["response"]
    name = d["name"]
    vtcid = d["vtc"]["id"]
    vtcname = d["vtc"]["name"]
    invtc = d["vtc"]["inVTC"]
    steamid = d["steamID"]
    banned = d["banned"]
    bannedUntil = d["bannedUntil"]
    bansCount = d["bansCount"]
    displayBans = d["displayBans"]

    bans = []
    ets2hour = 0
    atshour = 0
    if displayBans:
        r = requests.get(f"https://api.truckersmp.com/v2/bans/{mpid}")
        if r.status_code == 200:
            d = json.loads(r.text)
            if not d["error"]:
                d = d["response"]
                bans = d
    
    try:
        r = requests.get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAMKEY}&steamid={steamid}&format=json")
        if r.status_code == 200:
            d = json.loads(r.text)
            for game in d["response"]["games"]:
                if game["appid"] == ETS2ID:
                    ets2hour = round(game["playtime_forever"]/60, 2)
                if game["appid"] == ATSID:
                    atshour = round(game["playtime_forever"]/60, 2)
    except:
        ets2hour = -1
        atshour = -1

    return {"mpid": mpid, "steamid": steamid, "name": name, "vtcid": vtcid, "vtcname": vtcname, "invtc": invtc, \
        "banned": banned, "bannedUntil": bannedUntil, "bansCount": bansCount, \
        "displayBans": displayBans, "bans": bans, "ets2hour": ets2hour, "atshour": atshour}

def GetTMPData(mpid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT tmpdata FROM truckersmp WHERE mpid = {mpid} AND lastupd > {int(time.time()) - 10800}")
    t = cur.fetchall()
    if len(t) > 0:
        return json.loads(b64d(t[0][0])) # cache for three hours
    global nameid
    r = requests.get(f"https://api.truckersmp.com/v2/player/{mpid}")
    if r.status_code == 200:
        d = json.loads(r.text)
        if not d["error"]:
            d = d["response"]
            name = d["name"]
            steamid = d["steamID"]
            patreon = d["patreon"]["isPatron"]
            avatar = d["avatar"]
            joinDate = d["joinDate"]
            group = d["groupName"]
            vtcid = d["vtc"]["id"]
            vtc = d["vtc"]["name"]
            vtctag = d["vtc"]["tag"]
            lastupd = int(time.time())
            res = {"mpid": mpid, "steamid": steamid, "name":name, "patreon": patreon, "avatar": avatar, "joinDate": joinDate, "group": group, \
                "vtcid": vtcid, "vtc": vtc, "vtctag": vtctag, "vtcpos": GetVTCPosition(d["vtc"]["id"], d["vtc"]["memberID"]),\
                    "lastupd": lastupd}
            nameid[f'{name} ({mpid})'] = mpid
            cur.execute(f"SELECT name, tmpdata FROM truckersmp WHERE mpid = {mpid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO truckersmp VALUES ({mpid}, '{b64e(d['name'])}', '{b64e(json.dumps(res))}', {int(time.time())})")
                conn.commit()
            else:
                if t[0][0] != b64e(d['name']):
                    cur.execute(f"UPDATE truckersmp SET name = '{b64e(d['name'])}', lastupd = '{int(time.time())}' WHERE mpid = {mpid}")
                if t[0][1] != b64e(json.dumps(res)):
                    cur.execute(f"UPDATE truckersmp SET tmpdata = '{b64e(json.dumps(res))}', lastupd = '{int(time.time())}' WHERE mpid = {mpid}")
                conn.commit()
            
            return res
    return None

def UpdateTMPMap():
    global nameid
    while 1:
        conn = newconn()
        cur = conn.cursor()
        r = requests.get("https://tracker.ets2map.com/v3/fullmap")
        if r.status_code != 200:
            time.sleep(10)
            continue
        d = json.loads(r.text)["Data"]
        for dd in d:
            cur.execute(f"SELECT name FROM truckersmp WHERE mpid = {dd['MpId']}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO truckersmp VALUES ({dd['MpId']}, '{b64e(dd['Name'])}', '', 0)")
            else:
                name = t[0][0]
                if name != b64e(dd['Name']):
                    cur.execute(f"UPDATE truckersmp SET name = '{b64e(dd['Name'])}' WHERE mpid = {dd['MpId']}")
        conn.commit()

        cur.execute(f"SELECT mpid, name FROM truckersmp")
        t = cur.fetchall()
        nameid = {}
        for tt in t:
            nameid[f'{b64d(tt[1])} ({tt[0]})'] = tt[0]

        time.sleep(30)

def SearchServer(server):
    res = process.extract(server, traffic.keys(), limit = 10)
    ret = []
    for t in res:
        if t[0] == "allplayer":
            continue
        ret.append(t[0])
    return ret

def SearchLocation(server, loc):
    res = process.extract(loc, location[server], limit = 10)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret

def SearchCountry(server, loc):
    print(country[server])
    res = process.extract(loc, country[server], limit = 10)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret

def GetTopTraffic(server):
    return (traffic[server]["top"], traffic[server]["lastupd"])

def GetLocationTraffic(server, location):
    return (traffic[server]["traffic"][location], traffic[server]["lastupd"])

def UpdateTMPTraffic():
    global traffic
    global location
    global country
    while 1:
        r = requests.get("https://traffic.krashnz.com/api/v2/public/servers.json")
        if r.status_code != 200:
            time.sleep(10)
            continue
        d = json.loads(r.text)
        if d["error"]:
            time.sleep(10)
            continue
        if d["response"]["offline"]:
            traffic["offline"] = True
            time.sleep(90)
            continue
        servers = d["response"]["servers"]
        allplayer = 0
        for server in servers:
            name = f'{server["game"].upper()} {server["name"]}' ### NOTE
            r = requests.get(server["urls"]["traffic"])
            if r.status_code != 200:
                continue
            d = json.loads(r.text)
            if d["error"]:
                continue
            if d["response"]["offline"]:
                traffic[name] = {"offline": True}
                continue
            straffic = {}
            ctraffic = {}
            totplayer = 0
            if not name in location.keys():
                location[name] = []
            if not name in country.keys():
                country[name] = []
            for place in d["response"]["traffic"]:
                loc = place["name"] + ", " + place["country"]
                if not loc in location[name]:
                    location[name].append(loc)
                if not place["country"] in country[name]:
                    country[name].append(place["country"])
                totplayer += place["players"]
                straffic[loc] = {"location": loc, "severity": place["severity"], "players": place["players"]}
                if not place["country"] in ctraffic.keys():
                    ctraffic[place["country"]] = []
                ctraffic[place["country"]].append({"location": place["name"], "severity": place["severity"], "players": place["players"]})
            allplayer += totplayer
            r = requests.get(server["urls"]["top"])
            if r.status_code != 200:
                continue
            d = json.loads(r.text)
            if d["error"]:
                continue
            if d["response"]["offline"]:
                continue
            stop = d["response"]["top"]
            
            traffic[name] = {"players": totplayer, "traffic": straffic, "ctraffic": ctraffic, "top": stop, "lastupd": int(time.time())}
        traffic["allplayer"] = allplayer
        time.sleep(180)

def GetEvents(vtcid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT data FROM eventcache WHERE vtcid = {vtcid} AND lastupd > {int(time.time()) - 10800}")
    t = cur.fetchall()
    if len(t) > 0:
        return json.loads(b64d(t[0][0]))
    
    r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}/events/attending")
    if r.status_code != 200:
        return None
    d = json.loads(r.text)
    if d["error"]:
        return None
    d = d["response"]
    t = []
    for dd in d:
        eid = dd["id"]
        name = dd["name"]
        server = dd["server"]["name"]
        vtc = dd["vtc"]["name"]
        creator = dd["user"]["username"]
        url = dd["url"]

        game = dd["game"]
        emap = dd["map"]
        departure = dd["departure"]
        arrive = dd["arrive"]
        startat = dd["start_at"]
        dt=datetime.strptime(startat, '%Y-%m-%d %H:%M:%S')
        ts=int(dt.timestamp())
        dlc = dd["dlcs"]

        confirmed = dd["attendances"]["confirmed"]
        unsure = dd["attendances"]["unsure"]
        t.append({"id": eid, "name": name, "server": server, "url": url, "vtc": vtc, "creator": creator, "game": game, "map": emap, "departure": departure, "arrive": arrive, "startat": ts, "dlc": dlc, "confirmed": confirmed, "unsure": unsure})
    
    cur.execute(f"DELETE FROM eventcache WHERE vtcid = {vtcid}")
    cur.execute(f"INSERT INTO eventcache VALUES ({vtcid}, '{b64e(json.dumps(t))}', {int(time.time())})")
    conn.commit()
    return t