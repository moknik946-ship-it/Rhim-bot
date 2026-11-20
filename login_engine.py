# -*- coding: utf-8 -*-
"""
تسجيل الدخول (الطريقة الجديدة): OAuth guest ← MajorLogin ببصمة جهاز ← GetLoginData
الدالة الأساسية: await do_login(uid, password, region) ← dict بنفس شكل النسخ السابقة، أو None
LAST_ERROR[uid] يحمل مرحلة الفشل الأخيرة (oauth / majorlogin / decrypt / getlogindata / ...)
"""
import asyncio
import json
import logging
import os
import random
import struct
import time
from datetime import datetime

import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

try:
    from Pb2 import PorTs_pb2
except Exception:                         # اختياري: للاسم والكلان فقط
    PorTs_pb2 = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
log = logging.getLogger("login")

LOGIN_KEY = b"Yg&tc%DEuh6%Zc^8"
LOGIN_IV = b"6oyZDr22E3ychjM%"
AES_KEY, AES_IV = LOGIN_KEY, LOGIN_IV
LOGIN_SERVERS = ["https://loginbp.ppmainecoonghj.com/"]

# حالة النسخة (تتحدث من سيرفر الإصدارات وتنحفظ 10 دقايق)
login_url = LOGIN_SERVERS[0]
ob = "OB55"
verr = None
host = "loginbp.ppmainecoonghj.com"
_ver_ts = 0.0
LAST_ERROR = {}


def update_version(force=False):
    global login_url, ob, verr, host, _ver_ts
    if not force and time.time() - _ver_ts < 600 and verr:
        return login_url, ob, verr
    try:
        from google_play_scraper import app as gp
        d = gp("com.dts.freefireth", lang="en", country="ME")
        version = d["version"]
    except Exception:
        version = "1.132.1"
    try:
        x = requests.get(
            "https://version.ggwhitehawk.com/live/ver.php"
            f"?version={version}&lang=en&device=android&channel=android"
            f"&appsttore=googleplay&region=en&whitelist_version=1.3.0"
            f"&whitelist_sp_version=1.0.0&device_name=google%20G011A"
            f"&device_CPU=ARMv7%20VFPv3%20NEON%20VMH"
            f"&device_GPU=Adreno%20(TM)%20640&device_mem=1993",
            timeout=10,
        ).json()
        login_url = x["server_url"]
        ob = x["latest_release_version"]
        verr = x["remote_version"]
        host = login_url.split("https://", 1)[1].split("/", 1)[0]
    except Exception:
        login_url = LOGIN_SERVERS[0]
        ob = "OB55"
        verr = version
        host = "loginbp.ppmainecoonghj.com"
    _ver_ts = time.time()
    return login_url, ob, verr


# ───────────── دوال الطريقة الجديدة (منقولة كما هي) ─────────────
def EnV_VaRiAnT(n):
	d=[]
	while True:
		b=n&0x7F;n>>=7
		if n:b|=0x80
		d.append(b)
		if not n:break
	return bytes(d)

def ProToBuF(Fields):
	p=bytearray()
	for f,v in Fields.items():
		if isinstance(v,bool):
			p.extend(EnV_VaRiAnT((f<<3)|0));p.extend(EnV_VaRiAnT(1 if v else 0))
		elif isinstance(v,int):
			p.extend(EnV_VaRiAnT((f<<3)|0));p.extend(EnV_VaRiAnT(v))
		elif isinstance(v,str):
			d=v.encode();p.extend(EnV_VaRiAnT((f<<3)|2));p.extend(EnV_VaRiAnT(len(d)));p.extend(d)
		elif isinstance(v,(bytes,bytearray)):
			d=bytes(v);p.extend(EnV_VaRiAnT((f<<3)|2));p.extend(EnV_VaRiAnT(len(d)));p.extend(d)
	return bytes(p)

def Read_VaRiAnT(data,pos):
	result=0;shift=0
	while pos<len(data):
		b=data[pos];pos+=1
		result|=(b&0x7F)<<shift
		if not (b&0x80):break
		shift+=7
	return result,pos

def Parse_ProToBuF(data):
	fields={};pos=0;n=len(data)
	while pos<n:
		try:key,pos=Read_VaRiAnT(data,pos)
		except:break
		fn=key>>3;wt=key&0x07
		try:
			if wt==0:val,pos=Read_VaRiAnT(data,pos)
			elif wt==2:
				ln,pos=Read_VaRiAnT(data,pos);val=data[pos:pos+ln];pos+=ln
			elif wt==5:val=data[pos:pos+4];pos+=4
			elif wt==1:val=data[pos:pos+8];pos+=8
			else:break
		except:break
		fields.setdefault(fn,[]).append(val)
	return fields

def Ua():
	versions=['4.0.18P6','4.0.19P7','4.0.20P1','4.1.0P3','4.1.5P2','4.2.1P8','4.2.3P1','5.0.1B2','5.0.2P4','5.1.0P1','5.2.0B1','5.2.5P3','5.3.0B1','5.3.2P2','5.4.0P1','5.4.3B2','5.5.0P1','5.5.2P3']
	return random.choice(versions)

def build_login_payload(access_token, open_id):
    """حمولة MajorLogin (بصمة الجهاز): منقولة من دالة get_jwt اللي أرسلها صاحب المشروع"""
    P = {}
    P[3] = time.strftime("%Y-%m-%d %H:%M:%S"); P[4] = "free fire"; P[5] = 1
    ver = os.environ.get("LOGIN_VERSION", "").strip()
    P[7] = (verr or "1.132.9") if ver.lower() == "auto" else (ver or "1.132.9")
    P[8] = "Android OS 14 / API-34 (UP1A.231005.007/V816.0.15.0.UNQMIXM)"
    P[9] = "Handheld"; P[10] = "Grameenphone"; P[11] = "CarrierDataNetwork"
    P[12] = 1666; P[13] = 750; P[14] = "352"; P[15] = "ARM64 FP ASIMD AES | 2400 | 8"
    P[16] = 5563; P[17] = "Mali-G57 MC2"
    P[18] = "OpenGL ES 3.2 v1.r32p1-01eac0.0a0b917d9265b4c01be9925306306139"
    P[19] = "Google|9cc73f7a-91f6-40f6-87ec-5b67e597eb8c"; P[20] = "59.152.5.188"
    P[21] = "en"; P[22] = open_id; P[23] = "8"; P[24] = "Handheld"
    P[25] = "Xiaomi 2312DRAABI"; P[26] = "BD"; P[29] = access_token; P[30] = 1
    P[41] = "Grameenphone"; P[42] = "Cellular"
    P[57] = "7428b253defc164018c604a1ebbfebdf"
    P[60] = 109685; P[61] = 58294; P[62] = 797; P[63] = 18000; P[64] = 58818; P[65] = 109685
    P[66] = 58818; P[67] = 109685; P[73] = 2
    P[74] = "/data/app/~~cqQgpdMykLQEM3odipXatw==/com.dts.freefireth-G6e5yOt1dtuXG5Ambhj18g==/lib/arm64"
    P[76] = 1
    P[77] = "b8e0cd5e295eee42f5860d3c86e483dd|/data/app/~~cqQgpdMykLQEM3odipXatw==/com.dts.freefireth-G6e5yOt1dtuXG5Ambhj18g==/base.apk"
    P[78] = 3; P[79] = 2; P[81] = "64"; P[83] = "2019121229"; P[85] = 3; P[86] = "OpenGLES2"
    P[87] = 4095; P[88] = 8
    P[89] = b"FwQVTgUPX1UaUllDDwcWCRBpWAUOUgsvA1snWlBaO1kFYg=="
    P[90] = "Dhaka"; P[91] = "C"; P[92] = 8043; P[93] = "android"
    P[94] = "KqsHT4XbSZhqerDNUhjbS3DxG/4+I62zQU2tZFJN91kBUICAlZ5yujshLKvjlk/KiShfKfis8EeB1PMhFHIodWPncZC4fCHYF3TcTwNj95aWY/S3"
    P[95] = 111207; P[96] = '{"cur_rate":[60,90,120],"support_etc2":false}'
    P[97] = 1; P[98] = 1; P[99] = "4"; P[100] = "4"; P[102] = "GQ]        e"; P[103] = 1
    P[104] = 45174; P[105] = 1
    P[106] = "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|https://core-bs.ggpolarbear.com/live/ABHotUpdates/|a4332cb1c1a84e51dd77441e4856ed5a"
    P[107] = "1.9393e7b8e53e8aeb"
    return AES.new(LOGIN_KEY, AES.MODE_CBC, LOGIN_IV).encrypt(pad(ProToBuF(P), 16))


xAlInAs_build_login_payload = build_login_payload      # اسم قديم للتوافق


def Strip_MajorLogin_Prefix(body):
	if len(body)<=64:return body
	try:
		if 8 in Parse_ProToBuF(body):return body
	except:pass
	try:
		if 8 in Parse_ProToBuF(body[64:]):return body[64:]
	except:pass
	return body[64:]

def GeT_AccEss(uid,password):
	url="https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
	headers={"User-Agent":Ua(),"Content-Type":"application/json; charset=utf-8"}
	R=requests.post(url,headers=headers,json={"client_id":100067,"client_secret":"2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3","client_type":2,"device_id":"","password":password,"response_type":"token","uid":int(uid)},verify=False,timeout=15)
	if R.status_code not in (200,201):return None
	try:J=R.json()
	except:return None
	if J.get("code")!=0:return None
	data=J.get("data",{})
	return {"access_token":data.get("access_token"),"open_id":data.get("open_id")}

def xAlInAs_decrypt_major_login(resp):
	class A: pass
	a = A()
	body = Strip_MajorLogin_Prefix(resp)
	ld = Parse_ProToBuF(body)
	if not ld: return None
	au = ld.get("8") or ld.get(8)
	if type(au) is list: au = au[0]
	if isinstance(au, bytes):
		try: tok = au.decode("utf-8")
		except: tok = ""
	else: tok = str(au or "")
	if not tok.startswith("eyJ"): return None
	
	ub = ld.get("10") or ld.get(10)
	if type(ub) is list: ub = ub[0]
	url = ub.decode("utf-8") if isinstance(ub, bytes) else str(ub or "")
	if not url: return None
	
	ts_raw = ld.get("21") or ld.get(21)
	if type(ts_raw) is list: ts_raw = ts_raw[0]
	ts = int(ts_raw) if ts_raw else int(time.time())
	
	kb = xAlInAs_get_raw_field(body, 22)
	ib = xAlInAs_get_raw_field(body, 23)
	if not kb or not ib: kb, ib = LOGIN_KEY, LOGIN_IV
	
	acc_uid = ld.get("1") or ld.get(1)
	if type(acc_uid) is list: acc_uid = acc_uid[0]
	if isinstance(acc_uid, bytes):
		try: acc_uid = int(acc_uid.hex(), 16)
		except: acc_uid = 0
	
	a.token = tok
	a.account_uid = acc_uid or 0
	a.key = kb
	a.iv = ib
	a.timestamp = ts
	a.url = url
	return a

def xAlInAs_decrypt_login_data(data):
	class P: pass
	p = P()
	pd = Parse_ProToBuF(data)
	if not pd: return None
	
	def get_val(k):
		v = pd.get(k)
		if not v: return None
		if isinstance(v, list): v = v[0]
		return v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)

	op = get_val("14") or get_val(14)
	cp_ = get_val("32") or get_val(32)
	if not op or not cp_: return None
	p.Online_IP_Port = op
	p.AccountIP_Port = cp_
	return p

def xAlInAs_read_varint(d, p):
    v = 0
    s = 0
    while True:
        if p >= len(d):
            raise ValueError("truncated")
        b = d[p]
        p += 1
        v |= (b & 0x7F) << s
        if not b & 0x80:
            return v, p
        s += 7
        if s > 70:
            raise ValueError("too long")

def xAlInAs_get_raw_field(d, tf):
    try:
        p = 0
        while p < len(d):
            tag, p = xAlInAs_read_varint(d, p)
            f = tag >> 3
            w = tag & 7
            if w == 0:
                v, p = xAlInAs_read_varint(d, p)
            elif w == 1:
                if p + 8 > len(d):
                    return None
                v = d[p:p + 8]
                p += 8
            elif w == 2:
                ln, p = xAlInAs_read_varint(d, p)
                if p + ln > len(d):
                    return None
                v = d[p:p + ln]
                p += ln
            elif w == 5:
                if p + 4 > len(d):
                    return None
                v = d[p:p + 4]
                p += 4
            else:
                return None
            if f == tf:
                return v
        return None
    except:
        return None


# ───────────── التجميع ─────────────
def _fail(uid, stage):
    LAST_ERROR[str(uid)] = stage
    log.warning("login failed for ...%s at %s", str(uid)[-4:], stage)
    return None


def _login_sync(uid, password, region):
    uid = str(uid)
    LAST_ERROR.pop(uid, None)
    update_version()
    try:
        td = GeT_AccEss(uid, password)
    except Exception as e:
        return _fail(uid, f"oauth error: {type(e).__name__}")
    if not td or not td.get("access_token") or not td.get("open_id"):
        return _fail(uid, "oauth (بيانات الحساب غلط أو محظور)")
    try:
        pyl = build_login_payload(td["access_token"], td["open_id"])
        headers_ml = {
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept-Encoding": "identity",
            "X-GA-SV": str(int(time.time())),
            "Authorization": "Bearer",
            "X-GA": "v1 1",
            "ReleaseVersion": ob,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
            "Host": host,
        }
        r_ml = requests.post(f"{login_url.rstrip('/')}/MajorLogin", headers=headers_ml, data=pyl,
                             verify=False, timeout=15)
    except Exception as e:
        return _fail(uid, f"majorlogin error: {type(e).__name__}")
    if r_ml.status_code not in (200, 201) or not r_ml.content:
        return _fail(uid, f"majorlogin http {r_ml.status_code}")
    ad = xAlInAs_decrypt_major_login(r_ml.content)
    if not ad:
        return _fail(uid, "majorlogin رفض الحساب")
    client_url = ad.url.rstrip("/")
    if not client_url.startswith(("http://", "https://")):
        client_url = "https://" + client_url
    try:
        headers_gld = {
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": str(int(time.time())),
            "Authorization": f"Bearer {ad.token}",
            "X-GA": "v1 1",
            "ReleaseVersion": ob,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
        }
        r_gld = requests.post(f"{client_url}/GetLoginData", headers=headers_gld, data=pyl,
                              verify=False, timeout=15)
    except Exception as e:
        return _fail(uid, f"getlogindata error: {type(e).__name__}")
    if r_gld.status_code != 200 or not r_gld.content:
        return _fail(uid, f"getlogindata http {r_gld.status_code}")
    ports = xAlInAs_decrypt_login_data(r_gld.content)
    if not ports or not ports.Online_IP_Port or not ports.AccountIP_Port:
        return _fail(uid, "getlogindata بدون عناوين السيرفر")
    try:
        oip, oport = ports.Online_IP_Port.split(":")
        cip, cport = ports.AccountIP_Port.split(":")
    except ValueError:
        return _fail(uid, "عناوين السيرفر بصيغة غلط")
    name, clan_id, clan_data = "Unknown", 0, ""
    if PorTs_pb2 is not None:
        try:
            p = PorTs_pb2.GetLoginData()
            p.ParseFromString(r_gld.content)
            name = p.AccountName or name
            clan_id = p.Clan_ID or 0
            clan_data = p.Clan_Compiled_Data or ""
        except Exception:
            pass
    return {
        "bot_uid": str(ad.account_uid),
        "token": ad.token,
        "region": region,
        "key": ad.key,
        "iv": ad.iv,
        "timestamp": int(ad.timestamp) or int(time.time()),
        "online_ip": oip, "online_port": oport,
        "chat_ip": cip, "chat_port": cport,
        "account_name": name, "clan_id": clan_id, "clan_data": clan_data,
        "server_url": client_url,
        "login_data_raw": r_gld.content,
    }


async def do_login(uid, password, region_pref="ME"):
    """تسجيل دخول. يرجع dict أو None (والسبب في LAST_ERROR[uid])"""
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _login_sync, uid, password, region_pref or "ME")
    except Exception as e:
        return _fail(uid, f"unexpected {type(e).__name__}: {e}")
