#!/usr/bin/env python3
"""Discover and rank public GTA 6 YouTube Shorts candidates. No downloading or publishing."""
import csv, json, math, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
STATE = ROOT / "data" / "seen_video_ids.json"
API = "https://www.googleapis.com/youtube/v3"
GTA6_RE = re.compile(r"\b(?:gta\s*6|gta\s*vi|grand theft auto\s*vi)\b", re.I)
GTA5_RE = re.compile(r"\b(?:gta\s*5|gta\s*v|grand theft auto\s*v)\b", re.I)
DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")

def api_get(path, params):
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing YOUTUBE_API_KEY GitHub Actions secret.")
    params = {**params, "key": key}
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def duration_seconds(value):
    match = DURATION_RE.fullmatch(value or "")
    if not match:
        return 10**9
    hours, minutes, seconds = (int(x or 0) for x in match.groups())
    return hours * 3600 + minutes * 60 + seconds

def category_for(title, channel):
    t = title.lower()
    c = channel.lower()
    if "rockstar" in c or "official trailer" in t or "launch trailer" in t:
        return "Official / Trailer"
    if any(x in t for x in ("funny", "fail", "meme", "hilarious", "glitch", "chaos")):
        return "Funny Moments"
    if any(x in t for x in ("gameplay", "mission", "vehicle", "car", "police", "map", "feature", "secret")):
        return "Gameplay Ideas"
    return "GTA 6 Shorts"

def main():
    terms_file = ROOT / "config/search_terms.txt"
    terms = [s.strip() for s in terms_file.read_text(encoding="utf-8").splitlines()
             if s.strip() and not s.lstrip().startswith("#")]
    ids = set()
    for term in terms[:10]:
        result = api_get("search", {"part":"snippet","type":"video","q":term,
            "maxResults":50,"order":"date","videoDuration":"short","safeSearch":"moderate"})
        ids.update(x["id"]["videoId"] for x in result.get("items", [])
                   if x.get("id", {}).get("videoId"))

    rows = []
    now = datetime.now(timezone.utc)
    ordered_ids = sorted(ids)
    for i in range(0, len(ordered_ids), 50):
        result = api_get("videos", {"part":"snippet,statistics,contentDetails",
                                    "id":",".join(ordered_ids[i:i+50])})
        for item in result.get("items", []):
            st, sn = item.get("statistics", {}), item.get("snippet", {})
            title, channel = sn.get("title", ""), sn.get("channelTitle", "")
            description = sn.get("description", "")
            text = title + " " + description
            # Strict GTA VI relevance; exclude GTA V-only results and non-Shorts durations.
            if not GTA6_RE.search(text):
                continue
            if GTA5_RE.search(text) and not re.search(r"\b(?:gta\s*6|gta\s*vi)\b", text, re.I):
                continue
            duration = item.get("contentDetails", {}).get("duration", "")
            seconds = duration_seconds(duration)
            if seconds <= 0 or seconds > 180:
                continue

            try:
                published = datetime.fromisoformat(sn.get("publishedAt", "").replace("Z", "+00:00"))
                age_days = max((now - published).total_seconds() / 86400, 0.25)
            except (ValueError, TypeError):
                published, age_days = now, 1.0
            views, likes, comments = (int(st.get(k, 0)) for k in
                                      ("viewCount","likeCount","commentCount"))
            like_rate = 100 * likes / views if views else 0
            comment_rate = 100 * comments / views if views else 0
            views_per_day = views / age_days
            # Emphasizes recent daily velocity and engagement, while retaining some total reach.
            score = (0.55 * math.log1p(views_per_day)
                     + 0.20 * math.log1p(views)
                     + 0.25 * math.log1p(like_rate + comment_rate))
            rows.append({"video_id":item["id"],"title":title,"channel":channel,
                "published_at":sn.get("publishedAt",""),
                "url":f"https://www.youtube.com/watch?v={item['id']}",
                "duration":duration,"duration_seconds":seconds,
                "views":views,"likes":likes,"comments":comments,
                "age_days":round(age_days,2),"views_per_day":round(views_per_day,1),
                "like_rate_pct":round(like_rate,3),
                "comment_rate_pct":round(comment_rate,3),
                "ranking_score":round(score,4),
                "category":category_for(title, channel),
                "shorts_status":"Short-form candidate (<=180s); vertical Shorts format not verifiable via this API"})
    rows.sort(key=lambda r:r["ranking_score"], reverse=True)

    OUT.mkdir(exist_ok=True)
    STATE.parent.mkdir(exist_ok=True)
    seen_ids = json.loads(STATE.read_text()) if STATE.exists() else []
    seen = set(seen_ids)
    fresh = [r for r in rows if r["video_id"] not in seen]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for name, data in ((f"candidates_{stamp}.json",rows),
                       (f"new_candidates_{stamp}.json",fresh)):
        (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    if rows:
        with (OUT/f"candidates_{stamp}.csv").open("w",newline="",encoding="utf-8-sig") as f:
            w = csv.DictWriter(f,fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    new_ids = [r["video_id"] for r in rows if r["video_id"] not in seen]
    seen_ids = (seen_ids + new_ids)[-10000:]
    STATE.write_text(json.dumps(seen_ids,indent=2),encoding="utf-8")
    print(f"Discovered {len(rows)} relevant GTA 6 short-form candidates; {len(fresh)} new candidates.")
    print("Note: <=180 seconds is a duration filter, not proof of vertical YouTube Shorts format.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise
