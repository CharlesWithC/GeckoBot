# Copyright (C) 2022 Charles All rights reserved.
# Author: @Charles-1414
# License: Apache-2.0

# Retrieve player map data each 10 seconds.

import requests, json
from rapidfuzz import process, fuzz
from db import newconn
from functions import *
import time
from settings import *
from datetime import datetime

ponline = {}
nameid = {}
vtcnameid = {}
playerid = {}
serverid = {}
idserver = {}
traffic = {}
location = {}
country = {}
idname = {}

config_txt = ""
if sys.argv[0].endswith("main.py"):
    config_txt = open("./bot.conf","r").read()
elif sys.argv[0].endswith("test.py"):
    config_txt = open("./test.conf","r").read()
config = json.loads(config_txt)
STEAMKEY = config["steam"]

def GetSteamUser(mpid, steamid):
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
    cur.execute(f"INSERT INTO steam VALUES ({mpid}, {steamid}, '{d['personaname']}', '{b64e(json.dumps(d))}', {int(time.time())})")
    conn.commit()
    return d

def VTCID2Name(vtcid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM vtcbind WHERE vtcid = {vtcid}")
    t = cur.fetchall()
    if len(t) > 0:
        return b64d(t[0][0])
    else:
        r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}")
        if r.status_code != 200:
            return f"VTC #{vtcid}"
        d = json.loads(r.text)
        if d["error"]:
            return f"VTC #{vtcid}"
        d = d["response"]
        name = d["name"]
        cur.execute(f"INSERT INTO vtcbind VALUES (0, {vtcid}, '{b64e(name)}')")
        conn.commit()
        return name

def SearchVTCName(name):
    res = process.extract(name, vtcnameid.keys(), limit = 5, score_cutoff = 60)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret

def SearchName(name):
    res = process.extract(name, nameid.keys(), limit = 5, score_cutoff = 80)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret

def Name2ID(name):
    if name in nameid.keys():
        return nameid[name]
    return None

def VTCName2ID(name):
    if name in vtcnameid.keys():
        return vtcnameid[name]
    return None

def ID2Player(mpid):
    if mpid in ponline.keys():
        return ponline[mpid]
    return None

def Discord2Mp(discordid):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT mpid FROM tmpbind WHERE discordid = {discordid}")
    t = cur.fetchall()
    if len(t) > 0:
        return t[0][0]
    return None

def PlayerID2Mp(server, pid):
    sid = serverid[server]
    if not (sid, pid) in playerid.keys():
        return None
    return playerid[(sid, pid)]

def Steam2Mp(steamid):
    conn = newconn()
    cur = conn.cursor()
    steamid = int(steamid)
    cur.execute(f"SELECT mpid FROM steam WHERE steamid = {steamid}")
    t = cur.fetchall()
    if len(t) > 0:
        return t[0][0]
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

def GetVTCData(vtcid, clearcache = False):
    conn = newconn()
    cur = conn.cursor()
    if not clearcache:
        cur.execute(f"SELECT tmpdata FROM vtc WHERE vtcid = {vtcid} AND lastupd > {int(time.time()) - 10800}")
        t = cur.fetchall()
        if len(t) > 0:
            return json.loads(b64d(t[0][0])) # cache for three hours
            
    r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}")
    if r.status_code == 200:
        d = json.loads(r.text)
        if not d["error"]:
            d = d["response"]
            name = d["name"]
            slogan = d["slogan"]
            ownerid = d["owner_id"]
            ownername = d["owner_username"]
            logo = d["logo"]
            games = ""
            if d["games"]["ats"]:
                games += "American Truck Simulator, "
            if d["games"]["ets"]:
                games += "Euro Truck Simulator, "
            games = games[:-2]
            membercnt = d["members_count"]
            recruitment = d["recruitment"]
            language = d["language"]
            verified = d["verified"]
            created = d["created"]

            res = {"vtcid": vtcid, "name": name, "slogan": slogan, "ownerid": ownerid, "ownername": ownername, \
                "logo": logo, "games": games, "membercnt": membercnt, "recruitment": recruitment, "language": language, \
                "verified": verified, "created": created}

            cur.execute(f"SELECT name, tmpdata FROM vtc WHERE vtcid = {vtcid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO vtc VALUES ({vtcid}, '{b64e(name)}', '{b64e(json.dumps(res))}', '',  {int(time.time())})")
                conn.commit()
            else:
                if t[0][0] != b64e(d['name']):
                    cur.execute(f"UPDATE vtc SET name = '{b64e(d['name'])}', lastupd = '{int(time.time())}' WHERE vtcid = {vtcid}")
                if t[0][1] != b64e(json.dumps(res)):
                    cur.execute(f"UPDATE vtc SET tmpdata = '{b64e(json.dumps(res))}', lastupd = '{int(time.time())}' WHERE vtcid = {vtcid}")
                conn.commit()
            
            return res
    return None

def GetVTCMembers(vtcid, clearcache = False):
    conn = newconn()
    cur = conn.cursor()
    if not clearcache:
        cur.execute(f"SELECT members FROM vtc WHERE vtcid = {vtcid} AND lastupd > {int(time.time()) - 10800}")
        t = cur.fetchall()
        if len(t) > 0 and t[0][0] != '':
            tt = t[0][0].split("|")
            return (json.loads(b64d(tt[0])), json.loads(b64d(tt[1]))) # cache for three hours

    roles = []
    r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}/roles")
    if r.status_code == 200:
        d = json.loads(r.text)
        if not d["error"]:
            d = d["response"]
            for role in d["roles"]:
                name = role["name"]
                roleid = role["id"]
                order = role["order"]
                r = {"name": name, "roleid": roleid, "order": order}
                roles.append(r)            

    r = requests.get(f"https://api.truckersmp.com/v2/vtc/{vtcid}/members")
    if r.status_code == 200:
        d = json.loads(r.text)
        if not d["error"]:
            d = d["response"]["members"]
            members = []
            for dd in d:
                members.append({"mpid": dd["user_id"], "username": dd["username"], "roleid": dd["role_id"], "joinDate": dd["joinDate"]})
                if dd['user_id'] in idname.keys() and idname[dd['user_id']] != b64e(dd['username']):
                    cur.execute(f"SELECT name FROM truckersmp WHERE mpid = {dd['user_id']}")
                    p = cur.fetchall()
                    nameid[f"{dd['username']} ({dd['user_id']})"] = dd['user_id']
                    if len(p) == 0:
                        cur.execute(f"INSERT INTO truckersmp VALUES ({dd['user_id']}, '{b64e(dd['username'])}', '', 0)")
                    else:
                        if p[0][0] != b64e(dd["username"]):
                            cur.execute(f"UPDATE truckersmp SET name = '{b64e(dd['username'])}' WHERE mpid = {dd['user_id']}")
                            del nameid[f"{b64d(p[0][0])} ({dd['user_id']})"]

            cur.execute(f"SELECT members FROM vtc WHERE vtcid = {vtcid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO vtc VALUES ({vtcid}, '', '', '{b64e(json.dumps(roles)) + '|' + b64e(json.dumps(members))}',  0)")
                conn.commit()
            else:
                if t[0][0] != b64e(json.dumps(members)):
                    cur.execute(f"UPDATE vtc SET members = '{b64e(json.dumps(roles)) + '|' + b64e(json.dumps(members))}' WHERE vtcid = {vtcid}")
                conn.commit()
            
            return (roles, members)
    return None

def GetTMPData(mpid, clearcache = False):
    conn = newconn()
    cur = conn.cursor()
    if not clearcache:
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
            discordid = d["discordSnowflake"]
            patreon = d["patreon"]["isPatron"]
            avatar = d["avatar"]
            joinDate = d["joinDate"]
            group = d["groupName"]
            vtcid = d["vtc"]["id"]
            vtc = d["vtc"]["name"]
            vtctag = d["vtc"]["tag"]
            lastupd = int(time.time())
            if discordid != None:
                cur.execute(f"SELECT mpid FROM tmpbind WHERE discordid = {discordid}")
                t = cur.fetchall()
                if len(t) > 0:
                    tmpid = t[0][0]
                    if tmpid != mpid:
                        cur.execute(f"UPDATE tmpbind SET mpid = {mpid} WHERE discordid = {discordid}")
                        conn.commit()
                else:
                    cur.execute(f"INSERT INTO tmpbind VALUES ({discordid}, {mpid})")
                    conn.commit()
            res = {"mpid": mpid, "steamid": steamid, "discordid": discordid, "name":name, "patreon": patreon, "avatar": avatar, "joinDate": joinDate, "group": group, \
                "vtcid": vtcid, "vtc": vtc, "vtctag": vtctag, "vtcpos": GetVTCPosition(d["vtc"]["id"], d["vtc"]["memberID"]),\
                    "lastupd": lastupd}
            cur.execute(f"SELECT * FROM vtc WHERE vtcid = {vtcid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO vtc VALUES ({vtcid}, '{b64e(vtc)}', '', '', 0)")
                conn.commit()
                vtcnameid[f"{vtc} ({vtcid})"] = vtcid
            nameid[f'{name} ({mpid})'] = mpid
            cur.execute(f"SELECT name, tmpdata FROM truckersmp WHERE mpid = {mpid}")
            t = cur.fetchall()
            if len(t) == 0:
                cur.execute(f"INSERT INTO truckersmp VALUES ({mpid}, '{b64e(d['name'])}', '{b64e(json.dumps(res))}', {int(time.time())})")
                conn.commit()
            else:
                if t[0][0] != b64e(d['name']):
                    del nameid[f'{b64d(t[0][0])} ({mpid})']
                    cur.execute(f"UPDATE truckersmp SET name = '{b64e(d['name'])}', lastupd = '{int(time.time())}' WHERE mpid = {mpid}")
                if t[0][1] != b64e(json.dumps(res)):
                    cur.execute(f"UPDATE truckersmp SET tmpdata = '{b64e(json.dumps(res))}', lastupd = '{int(time.time())}' WHERE mpid = {mpid}")
                conn.commit()
            
            return res
    return None

def UpdateTMPMap():
    global nameid
    global idname
    global playerid 
    global ponline
    global vtcnameid
    while 1:
        conn = newconn()
        cur = conn.cursor()
        r = requests.get("https://tracker.ets2map.com/v3/fullmap")
        if r.status_code != 200:
            time.sleep(10)
            continue
        d = json.loads(r.text)["Data"]
        playerid = {}
        ponline = {}
        for dd in d:
            playerid[(dd['ServerId'], dd['PlayerId'])] = dd['MpId']
            ponline[dd['MpId']] = (dd['ServerId'], dd['PlayerId'])
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
            idname[tt[0]] = tt[1]
        
        cur.execute(f"SELECT vtcid, name FROM vtc")
        t = cur.fetchall()
        vtcnameid = {}
        for tt in t:
            vtcnameid[f'{b64d(tt[1])} ({tt[0]})'] = tt[0]

        time.sleep(30)

def SearchServer(server):
    res = process.extract(server, traffic.keys(), limit = 10, score_cutoff = 40)
    ret = []
    for t in res:
        if t[0] == "allplayer":
            continue
        ret.append(t[0])
    return ret

def ID2Server(sid):
    if sid in idserver.keys():
        return idserver[sid]
    return None

def SearchLocation(server, loc):
    res = process.extract(loc, location[server], limit = 10, score_cutoff = 40)
    ret = []
    for t in res:
        ret.append(t[0])
    return ret

def SearchCountry(server, loc):
    res = process.extract(loc, country[server], limit = 10, score_cutoff = 40)
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
    global serverid
    global idserver
    while 1:
        r = requests.get("https://api.truckersmp.com/v2/servers")
        if r.status_code == 200:
            d = json.loads(r.text)["response"]
            for dd in d:
                serverid[dd["game"] + " " + dd["name"]] = dd["mapid"]
                idserver[dd["mapid"]] = dd["game"] + " " + dd["name"]
                
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