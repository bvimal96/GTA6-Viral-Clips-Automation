#!/usr/bin/env python3
"""Discover and rank public YouTube video metadata. No video downloading or publishing."""
import csv, json, math, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
STATE = ROOT / "data" / "seen_video_ids.json"
API = "https://www.googleapis.com/youtube/v3"

def api_get(path, params):
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing YOUTUBE_API_KEY GitHub Actions secret.")
    params = {**params, "key": key}
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    terms_file = ROOT / "config/search_terms.txt"
    terms = [s.strip() for s in terms_file.read_text(encoding="utf-8").splitlines()
             if s.strip() and not s.lstrip().startswith("#")]
    ids = set()
    for term in terms[:10]:
        result = api_get("search", {"part":"snippet","type":"video","q":term,
            "maxResults":25,"order":"viewCount","videoDuration":"short","safeSearch":"moderate"})
        ids.update(x["id"]["videoId"] for x in result.get("items", [])
                   if x.get("id", {}).get("videoId"))

    rows = []
    ordered_ids = sorted(ids)
    for i in range(0, len(ordered_ids), 50):
        result = api_get("videos", {"part":"snippet,statistics,contentDetails",
                                    "id":",".join(ordered_ids[i:i+50])})
        for item in result.get("items", []):
            st, sn = item.get("statistics", {}), item.get("snippet", {})
            views, likes, comments = (int(st.get(k, 0)) for k in
                                      ("viewCount","likeCount","commentCount"))
            score = .25*math.log1p(views) + .35*math.log1p(likes) + .40*math.log1p(comments)
            rows.append({"video_id":item["id"],"title":sn.get("title",""),
                "channel":sn.get("channelTitle",""),"published_at":sn.get("publishedAt",""),
                "url":f"https://www.youtube.com/watch?v={item['id']}",
                "views":views,"likes":likes,"comments":comments,
                "like_rate_pct":round(100*likes/views,3) if views else 0,
                "comment_rate_pct":round(100*comments/views,3) if views else 0,
                "ranking_score":round(score,4),
                "duration":item.get("contentDetails",{}).get("duration","")})
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
    print(f"Discovered {len(rows)} public videos; {len(fresh)} new candidates.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise
