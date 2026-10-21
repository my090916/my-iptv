# -*- coding: utf-8 -*-
"""
潮汕 + 央视 直播源 生成器（TVBox / PotPlayer 通用）
=====================================================
【央视 18 台】静态公网源，长期有效，无需每日更新
    主线路：219.147.245.238:25480（2026-10-21 实测 hls/1~17 全部可用，已逐台抽帧核对台标）
    备用线路：74.91.26.218:82（已抽帧核对：cctv9hd=CCTV9、cctv12hd=CCTV12、cctv5p=CCTV5+、cctv1hd=实际CCTV8）
    CCTV16 来自 gmxw.7766.org:808/hls/169（已抽帧核对为奥林匹克频道体育赛事）

【潮汕台】
    汕头 4 个频道：橄榄台官方源，采用「按天」动态签名 → 每天必须重新运行本脚本！
    潮州公共：113.64.146.48:1688（静态，但首连较慢）

用法：直接运行本脚本，即在 output 目录重新生成全部源文件。
"""
import hashlib
import time
import datetime
import os
import json

OUT = os.path.dirname(os.path.abspath(__file__))

SALT = "bf9b2cab35a9c38857b82aabf99874aa96b9ffbb"
HOST = "https://sttv-hls.strtv.cn"
UA = ("Mozilla/5.0 (Linux; Android 12; MI 9 Build/SKQ1.200826.002) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0 Mobile Safari/537.36")

# ---------- 央视：已验证的静态线路 ----------
# (频道名, 主线路, 备用线路 or None)
CCTV = [
    ("CCTV1 综合",      "http://219.147.245.238:25480/newlive/live/hls/1/live.m3u8",  None),
    ("CCTV2 财经",      "http://219.147.245.238:25480/newlive/live/hls/2/live.m3u8",  None),
    ("CCTV3 综艺",      "http://219.147.245.238:25480/newlive/live/hls/3/live.m3u8",  None),
    ("CCTV4 中文国际",  "http://219.147.245.238:25480/newlive/live/hls/4/live.m3u8",  None),
    ("CCTV5 体育",      "http://219.147.245.238:25480/newlive/live/hls/5/live.m3u8",  None),
    ("CCTV5+ 体育赛事", "http://219.147.245.238:25480/newlive/live/hls/6/live.m3u8",  "http://74.91.26.218:82/live/cctv5p.m3u8"),
    ("CCTV6 电影",      "http://219.147.245.238:25480/newlive/live/hls/7/live.m3u8",  None),
    ("CCTV7 国防军事",  "http://219.147.245.238:25480/newlive/live/hls/8/live.m3u8",  None),
    ("CCTV8 电视剧",    "http://219.147.245.238:25480/newlive/live/hls/9/live.m3u8",  None),
    ("CCTV9 纪录",      "http://219.147.245.238:25480/newlive/live/hls/10/live.m3u8", "http://74.91.26.218:82/live/cctv9hd.m3u8"),
    ("CCTV10 科教",     "http://219.147.245.238:25480/newlive/live/hls/11/live.m3u8", None),
    ("CCTV11 戏曲",     "http://219.147.245.238:25480/newlive/live/hls/12/live.m3u8", None),
    ("CCTV12 社会与法", "http://219.147.245.238:25480/newlive/live/hls/13/live.m3u8", "http://74.91.26.218:82/live/cctv12hd.m3u8"),
    ("CCTV13 新闻",     "http://219.147.245.238:25480/newlive/live/hls/14/live.m3u8", None),
    ("CCTV14 少儿",     "http://219.147.245.238:25480/newlive/live/hls/15/live.m3u8", None),
    ("CCTV15 音乐",     "http://219.147.245.238:25480/newlive/live/hls/16/live.m3u8", None),
    ("CCTV16 奥林匹克", "http://gmxw.7766.org:808/hls/169/index.m3u8",                None),
    ("CCTV17 农业农村", "http://219.147.245.238:25480/newlive/live/hls/17/live.m3u8", None),
]

# ---------- 潮汕 ----------
ST_CHANNELS = [
    ("汕头新闻综合", "lKGXIQa", 500, "汕头电视台"),
    ("汕头经济生活", "7xjJK9d", 500, "汕头电视台"),
    ("汕头102.5音乐广播", "s7k681h", 64, "汕头广播"),
    ("汕头107.2综合广播", "Li7mg21", 64, "汕头广播"),
]
CZ_CHANNELS = [("潮州公共", "http://113.64.146.48:1688/hls/4/index.m3u8", "潮州电视台")]


def b36(n):
    if n == 0:
        return "0"
    d = "0123456789abcdefghijklmnopqrstuvwxyz"
    o = ""
    while n > 0:
        n, r = divmod(n, 36)
        o = d[r] + o
    return o


def pathname(cid, o, b):
    r = 0
    dd = -1
    l = 0
    for ch in cid:
        p = ord(ch)
        r += p
        if dd != -1:
            l += dd - p
        dd = p
    r += l
    s = b36(r)
    c = b36(o)
    u = sum(ord(x) for x in c)
    c = c[5:] + c[:5]
    f = abs(u - r)
    c = s[::-1] + c
    g, w = c[:4], c[4:]
    m = []
    for i in range(len(cid)):
        if i % 2 == b:
            m.append(c[i % len(c)])
        else:
            h = cid[i - 1] if i > 0 else None
            if h:
                v = g.find(h)
                m.append(h if v == -1 else w[v])
            else:
                m.append(g[i])
    return (b36(f)[::-1] + "".join(m))[:len(cid)]


def day_params():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)
    o = int(datetime.datetime(now.year, now.month, now.day, tzinfo=tz).timestamp() * 1000)
    return o, ((now.weekday() + 1) % 7) % 2


def day_params_for(dt):
    """指定日期（带时区 datetime）对应的 (0点毫秒, 星期奇偶)"""
    tz = datetime.timezone(datetime.timedelta(hours=8))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    dt = dt.astimezone(tz)
    o = int(datetime.datetime(dt.year, dt.month, dt.day, tzinfo=tz).timestamp() * 1000)
    return o, ((dt.weekday() + 1) % 7) % 2


def st_url(cid, r, o, b):
    lk = pathname(cid, o, b)
    t = int(time.time()) + 93600
    ts = format(t, "x")
    sign = hashlib.md5(f"{SALT}/{cid}/{r}/{lk}.m3u8{ts}".encode()).hexdigest()
    return f"{HOST}/{cid}/{r}/{lk}.m3u8?sign={sign}&t={ts}"


def build_lines(forecast=1):
    """返回 [(分组, 频道名, [线路...])]

    注意：汕头服务器只认「当天」路径（0点毫秒 + 星期奇偶），
    且 sign 的 t 必须是当下的时间戳；实测预生成未来日期一律返回 400，
    因此不要依赖 forecast > 1 做离线预置，forecast 仅保留作调试用。
    """
    groups = [("央视频道", [])]
    for name, main, bak in CCTV:
        urls = [main] + ([bak] if bak else [])
        groups[0][1].append((name, urls))

    tz = datetime.timezone(datetime.timedelta(hours=8))
    today = datetime.datetime.now(tz)
    st = []
    for name, cid, r, _ in ST_CHANNELS:
        urls = []
        for i in range(max(1, forecast)):
            o, b = day_params_for(today + datetime.timedelta(days=i))
            urls.append(st_url(cid, r, o, b))
        st.append((name, urls))
    groups.append(("汕头电视台", st))

    cz = [(n, [u]) for n, u, _ in CZ_CHANNELS]
    groups.append(("潮州电视台", cz))
    return groups


def gen_txt(groups):
    """TVBox txt 格式：频道名,url#url   （一套为主，备用用 # 并列）"""
    out = ["# 潮汕 + 央视 直播源  |  生成时间 %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "# 央视线路为长期静态源；汕头台为官方按天签名，每天需重新运行「更新潮汕央视直播源」",
           ""]
    for gname, items in groups:
        out.append(f"{gname},#genre#")
        for name, urls in items:
            out.append(f"{name},{'#'.join(urls)}")
        out.append("")
    return "\n".join(out)


def gen_m3u(groups):
    L = ['#EXTM3U x-tvg-url="https://epg.112114.xyz/pp.xml"']
    for gname, items in groups:
        for name, urls in items:
            for u in urls:
                L.append(f'#EXTINF:-1 group-title="{gname}",{name}')
                L.append(u)
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    g = build_lines()
    open(os.path.join(here, "tv.txt"), "w", encoding="utf-8").write(gen_txt(g))
    open(os.path.join(here, "tv.m3u"), "w", encoding="utf-8").write(gen_m3u(g))
    print("生成完成", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
