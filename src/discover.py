#!/usr/bin/env python3
"""Discover and rank public GTA 6 YouTube short-form candidates. No downloading or publishing."""
import csv, html, json, math, os, re, sys, urllib.parse, urllib.request
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

def candidate_review(title, category):
    """Conservative title-only triage; does not verify footage, vertical format, or reuse rights."""
    if category in ("Rockstar Official", "Trailer / Repost"):
        return "EXCLUDE", "OFFICIAL_OR_TRAILER", False, "Official channel or trailer wording"

    # Exclude GTA 5 crossover titles to preserve the GTA 6-only channel scope.
    if GTA5_RE.search(title):
        return "EXCLUDE", "GTA5_CROSSOVER_OR_TITLE", False, "GTA 5 is explicitly mentioned in the title"

    cleaned = re.sub(r"#\w+|[^\w\s]", " ", title)
    words = cleaned.split()
    title_has_gta6 = bool(GTA6_RE.search(title) or re.search(r"#gta\s*6|#gtavi", title, re.I))
    topic_terms = (
        "gameplay", "mission", "vehicle", "car", "police", "map", "feature",
        "secret", "easter egg", "hidden", "funny", "fail", "meme", "glitch",
        "comparison", "versus", "vs", "lucia", "jason", "vice city",
        "real life", "details", "things", "facts", "update", "mod"
    )
    title_lower = title.lower()
    has_specific_topic = any(term in title_lower for term in topic_terms)

    if title_has_gta6 and len(words) >= 3 and has_specific_topic:
        return "HIGH_POTENTIAL", "GTA6_TITLE_AND_TOPIC", True, "GTA 6 named in title with a specific topic clue"
    if len(words) < 3 or not title_has_gta6:
        return "MANUAL_REVIEW", "WEAK_TITLE_CONTEXT", False, "Title alone does not establish clear GTA 6 topic"
    return "MANUAL_REVIEW", "TOPIC_NOT_CLEAR", False, "GTA 6 title present but specific clip topic is unclear"

def category_for(title, channel):
    t = title.lower()
    if channel.strip().lower() == "rockstar games":
        return "Rockstar Official"
    if any(x in t for x in ("trailer", "launch trailer")):
        return "Trailer / Repost"
    if any(x in t for x in ("funny", "fail", "meme", "hilarious", "glitch", "chaos")):
        return "Funny Moments"
    if any(x in t for x in ("gameplay", "mission", "vehicle", "car", "police", "map", "feature", "secret")):
        return "Gameplay Ideas"
    return "GTA 6 Shorts"

def write_dashboard(rows, stamp):
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    page = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GTA 6 Shorts Discovery</title>
<style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#10141d;color:#edf2fa}
body{margin:0;padding:24px;max-width:1500px;margin-inline:auto}h1{margin:0 0 6px}.muted{color:#9eabc0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}
.card,section{background:#1a2230;border:1px solid #2c394d;border-radius:12px;padding:14px}
.metric{font-size:28px;font-weight:700}.controls{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
input,select{background:#111925;color:#edf2fa;border:1px solid #40516a;border-radius:8px;padding:10px;min-width:160px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:10px;border-bottom:1px solid #303b4d;vertical-align:top}
th{position:sticky;top:0;background:#202b3b;cursor:pointer}a{color:#8fc7ff;text-decoration:none}a:hover{text-decoration:underline}
.pill{display:inline-block;border-radius:20px;padding:3px 8px;background:#29384d;font-size:12px}.high{color:#8ce0ad}.exclude{color:#ff9999}
.wrap{overflow:auto;max-height:70vh}.small{font-size:12px}.note{line-height:1.5}
</style></head><body>
<h1>GTA 6 Shorts Discovery</h1><div class="muted">Generated: __STAMP__ · Public metadata only · Candidate list, not verified viral Shorts</div>
<div class="cards" id="metrics"></div>
<div class="note muted">Important: YouTube Data API duration filtering (≤180 seconds) does not prove vertical Shorts format, actual GTA 6 footage, or permission to reuse. Review content and rights separately. No video is downloaded.</div>
<div class="controls">
<input id="q" placeholder="Search title or creator…">
<select id="group"><option value="">All candidate groups</option><option>HIGH_POTENTIAL</option><option>MANUAL_REVIEW</option><option>EXCLUDE</option></select>
<select id="category"><option value="">All categories</option></select>
<select id="sort"><option value="ranking_score">Sort: Ranking score</option><option value="views_per_day">Views per day</option><option value="views">Total views</option><option value="published_at">Newest first</option></select>
<label class="pill"><input type="checkbox" id="fresh" style="min-width:0"> New in this run</label>
</div>
<div class="muted small" id="count"></div>
<section class="wrap"><table><thead><tr><th>Video</th><th>Creator</th><th>Group</th><th>Category</th><th>Views</th><th>Views/day</th><th>Like %</th><th>Age (days)</th><th>Duration</th><th>Shorts title hint</th><th>Reason</th></tr></thead><tbody id="body"></tbody></table></section>
<script>
const rows = __DATA__;
const seen = new Set(rows.filter(x=>x.is_new).map(x=>x.video_id));
const fmt = n => Number(n||0).toLocaleString();
const categories=[...new Set(rows.map(x=>x.category))].sort();
for(const c of categories){const o=document.createElement('option');o.value=c;o.textContent=c;document.querySelector('#category').append(o)}
const counts=Object.fromEntries(['HIGH_POTENTIAL','MANUAL_REVIEW','EXCLUDE'].map(g=>[g,rows.filter(x=>x.candidate_group===g).length]));
document.querySelector('#metrics').innerHTML =
  [['Candidates',rows.length],['High potential',counts.HIGH_POTENTIAL],['Manual review',counts.MANUAL_REVIEW],['Excluded',counts.EXCLUDE],['New this run',rows.filter(x=>x.is_new).length],['Creators',new Set(rows.map(x=>x.channel)).size]]
  .map(([k,v])=>'<div class="card"><div class="muted">'+k+'</div><div class="metric">'+fmt(v)+'</div></div>').join('');
function render(){
 let a=rows.filter(x=>(!document.querySelector('#q').value || (x.title+' '+x.channel).toLowerCase().includes(document.querySelector('#q').value.toLowerCase()))
 &&(!document.querySelector('#group').value||x.candidate_group===document.querySelector('#group').value)
 &&(!document.querySelector('#category').value||x.category===document.querySelector('#category').value)
 &&(!document.querySelector('#fresh').checked||x.is_new));
 const key=document.querySelector('#sort').value;
 a.sort((x,y)=>key==='published_at'?y.published_at.localeCompare(x.published_at):(Number(y[key]||0)-Number(x[key]||0)));
 document.querySelector('#count').textContent='Showing '+a.length+' of '+rows.length+' candidates';
 document.querySelector('#body').innerHTML=a.map(x=>'<tr><td><a target="_blank" rel="noopener" href="'+x.url+'">'+esc(x.title)+'</a><div class="muted small">'+x.video_id+'</div></td><td>'+esc(x.channel)+'</td><td class="'+(x.candidate_group==='HIGH_POTENTIAL'?'high':x.candidate_group==='EXCLUDE'?'exclude':'')+'">'+x.candidate_group+'</td><td>'+esc(x.category)+'</td><td>'+fmt(x.views)+'</td><td>'+fmt(x.views_per_day)+'</td><td>'+Number(x.like_rate_pct||0).toFixed(2)+'%</td><td>'+x.age_days+'</td><td>'+x.duration_seconds+'s</td><td>'+(x.shorts_hint_in_title?'Yes':'No')+'</td><td>'+esc(x.review_reason)+'</td></tr>').join('');
}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
document.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',render));render();
</script></body></html>"""
    page = page.replace("__STAMP__", html.escape(stamp)).replace("__DATA__", payload)
    (OUT / "index.html").write_text(page, encoding="utf-8")

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
            if not GTA6_RE.search(text):
                continue
            # Strict channel scope: exclude explicit GTA 5 crossovers in the title.
            if GTA5_RE.search(title):
                continue
            duration = item.get("contentDetails", {}).get("duration", "")
            seconds = duration_seconds(duration)
            if seconds <= 0 or seconds > 180:
                continue

            try:
                published = datetime.fromisoformat(sn.get("publishedAt", "").replace("Z", "+00:00"))
                age_days = max((now - published).total_seconds() / 86400, 1.0)
            except (ValueError, TypeError):
                published, age_days = now, 1.0
            views, likes, comments = (int(st.get(k, 0)) for k in
                                      ("viewCount","likeCount","commentCount"))
            like_rate = 100 * likes / views if views else 0
            comment_rate = 100 * comments / views if views else 0
            views_per_day = views / age_days
            score = (0.55 * math.log1p(views_per_day)
                     + 0.20 * math.log1p(views)
                     + 0.25 * math.log1p(like_rate + comment_rate))
            category = category_for(title, channel)
            group, review_flag, shortlist, review_reason = candidate_review(title, category)
            rows.append({"video_id":item["id"],"title":title,"channel":channel,
                "published_at":sn.get("publishedAt",""),
                "url":f"https://www.youtube.com/watch?v={item['id']}",
                "duration":duration,"duration_seconds":seconds,
                "views":views,"likes":likes,"comments":comments,
                "age_days":round(age_days,2),"views_per_day":round(views_per_day,1),
                "like_rate_pct":round(like_rate,3),
                "comment_rate_pct":round(comment_rate,3),
                "ranking_score":round(score,4),
                "category":category,
                "shorts_status":"Short-form candidate (<=180s); vertical Shorts format not verifiable via this API",
                "shorts_hint_in_title":bool(re.search(r"#shorts|\bshorts\b", title, re.I)),
                "candidate_group":group,
                "review_flag":review_flag,
                "review_reason":review_reason,
                "creator_shortlist":shortlist})
    rows.sort(key=lambda r:r["ranking_score"], reverse=True)

    OUT.mkdir(exist_ok=True)
    STATE.parent.mkdir(exist_ok=True)
    seen_ids = json.loads(STATE.read_text()) if STATE.exists() else []
    seen = set(seen_ids)
    fresh_ids = {r["video_id"] for r in rows if r["video_id"] not in seen}
    for r in rows:
        r["is_new"] = r["video_id"] in fresh_ids
    fresh = [r for r in rows if r["is_new"]]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for name, data in ((f"candidates_{stamp}.json",rows),
                       (f"new_candidates_{stamp}.json",fresh)):
        (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    if rows:
        with (OUT/f"candidates_{stamp}.csv").open("w",newline="",encoding="utf-8-sig") as f:
            w = csv.DictWriter(f,fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    write_dashboard(rows, stamp)
    new_ids = [r["video_id"] for r in rows if r["video_id"] not in seen]
    seen_ids = (seen_ids + new_ids)[-10000:]
    STATE.write_text(json.dumps(seen_ids,indent=2),encoding="utf-8")
    counts = {g:sum(r["candidate_group"]==g for r in rows) for g in ("HIGH_POTENTIAL","MANUAL_REVIEW","EXCLUDE")}
    print(f"Discovered {len(rows)} relevant GTA 6 short-form candidates; {len(fresh)} new candidates.")
    print("Groups: " + ", ".join(f"{k}={v}" for k,v in counts.items()))
    print("Dashboard: output/index.html")
    print("Note: <=180 seconds is a duration filter, not proof of vertical YouTube Shorts format.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise
