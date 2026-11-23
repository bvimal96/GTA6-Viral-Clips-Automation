# GTA6-Viral-Clips-Automation

Free, YouTube-only discovery workflow for a GTA 6 Shorts-focused channel. It reads public YouTube metadata and does not download or republish other creators' videos.

## Current operating scope
- GTA 6 / GTA VI only; explicit GTA 5 title crossovers are excluded.
- Candidate duration is 180 seconds or less. This is a duration filter only; the YouTube Data API does not prove that a video is a vertical Short.
- Candidate triage: HIGH_POTENTIAL, MANUAL_REVIEW, EXCLUDE. These are title-based review queues, not verified content labels.
- Strict content scope: actual GTA 6 in-game footage/gameplay only. Titles indicating reaction, review, podcast, facecam, selfie, vlog, discussion, or commentary are excluded.
- All other candidates are marked VISUAL_GAMEPLAY_CHECK_REQUIRED because public metadata cannot prove what appears in the video. Manually inspect the clip and reject talking-head/selfie/commentary videos.
- Ranking uses views/day, total views, and public like/comment rates. It is a discovery heuristic, not a quality or future-virality guarantee.
- Dashboard includes creator shortlist, new-this-run filtering, and an explicit usage-rights status.
- Every discovered third-party candidate starts as PERMISSION_REQUIRED. No public video is treated as cleared for reuse.
- CSV, JSON, and HTML dashboard are uploaded as a GitHub Actions artifact for 7 days.
- Seen video IDs are persisted to reduce repeat discoveries.
- Python standard library only.

## Run the discovery workflow
1. In this repository, open **Actions → GTA 6 YouTube Discovery**.
2. Select **Run workflow** for an immediate refresh, or let the scheduled runs execute.
3. Open the completed run and download the `gta6-candidates-N` artifact ZIP.
4. Extract the ZIP and open `index.html` in a browser. CSV/JSON are included for sorting and further review.
5. Use the HIGH_POTENTIAL filter as the first manual-review queue. Check the actual video, not just its title or score. Keep only in-game GTA 6 footage; reject facecam, selfie, talking-head, reaction, review, podcast, vlog, and commentary content.

Scheduled runs: 04:17 and 16:17 UTC (09:47 and 21:47 IST). GitHub may delay scheduled runs. Editing the search terms or scanner files on `main` also triggers a run.

## Candidate ranking
- 55% log of views per day
- 20% log of total views
- 25% log of combined like and comment rates
- Minimum age floor: 1 day to avoid unstable velocity spikes on newly published videos.

Missing or hidden public metrics are treated as zero. A high score means strong public engagement signals only; it does not prove GTA 6 footage, originality, vertical Shorts format, or rights.

## Usage rights — mandatory gate
- Discovery is not permission.
- Every third-party result is marked `PERMISSION_REQUIRED` until the owner grants explicit permission or a valid license is verified.
- Record each source in `rights/rights_register_template.csv` using `USER_OWNED` or `THIRD_PARTY`. For third-party clips, keep `download_eligible=FALSE` until written permission or a valid license is verified. Make a private working copy; do not put personal contact details or private permission documents in this public repository.
- For third-party footage, `AUTHORIZED` should be used only after confirming the rights holder, permitted platforms, editing rights, monetization rights, territory, and validity period in writing. For owned footage, confirm that the uploader/channel owner actually owns the recording and has the underlying game-content rights needed for the intended use.
- If permission is refused or rights are unclear, do not download, edit, or publish that creator's footage.
- Copyright clearance and YouTube reused-content monetization eligibility are separate checks.

## Production and publishing
- Only use footage you own or are explicitly licensed/authorized to edit and publish.
- Put your own source files and third-party files with verified permission on your own computer in `source_media/approved/` (this folder is git-ignored); never upload private footage or permission evidence to this public repo.
- No third-party YouTube downloader, scraping, or automatic clipping from public URLs is included.
- No automatic YouTube upload or publishing is included. Publishing requires separate explicit approval.
- The current automation is the discovery and review system; final video editing/export is a separate production step using rights-cleared footage.

## Cost and security
- GitHub Actions public-repository workflow and YouTube Data API v3 only; no Render, paid API, paid subscription, or billing activation.
- YouTube Data API quota applies. Keep the API key in GitHub Actions secret `YOUTUBE_API_KEY`; never commit it.
- Do not add private footage, API keys, OAuth tokens, cookies, passwords, or personal data to this public repository.

## Search terms
Edit `config/search_terms.txt` to tune discovery. Avoid adding GTA 5 terms because the channel scope is GTA 6 only.
