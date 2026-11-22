# GTA6-Viral-Clips-Automation

Zero-paid-service project to discover and rank public YouTube videos relevant to GTA 6, with a Shorts-first filter. It reads public metadata only.

## Current scope
- GTA 6 / GTA VI relevance filter; GTA 5-only results are excluded.
- Candidate duration limited to 180 seconds.
- **Important:** YouTube Data API does not expose a reliable vertical-video / Shorts-format flag here. Therefore these are short-form candidates, not guaranteed vertical Shorts.
- Official / Trailer, Funny Moments, Gameplay Ideas, and general GTA 6 Shorts categories.
- Ranking emphasizes views per day and engagement rates, while retaining total views.
- CSV and JSON reports uploaded as a 7-day GitHub Actions artifact.
- Seen video IDs persisted to reduce repeated candidates.
- Python standard library only; no third-party Python packages.

## Not included
- No downloading/re-uploading YouTube, Twitch, Kick, or other creators' videos.
- No automatic clipping from third-party URLs.
- No YouTube upload or publishing. Publishing remains disabled pending separate design, testing, rights review, and explicit approval.
- No paid service, Render deployment, subscription, or billing activation.

Use only source footage that you own or have explicit permission/licensing to edit and publish. Public availability or public metadata does not grant reuse rights. Cropping, captions, or music alone do not guarantee copyright clearance or monetization eligibility.

## Setup
1. In Google Cloud Console, enable **YouTube Data API v3** for the project.
2. Create an API key restricted to YouTube Data API v3.
3. In this repository, open **Settings → Secrets and variables → Actions**.
4. Add a repository secret named `YOUTUBE_API_KEY`.
5. Open **Actions → GTA 6 YouTube Discovery → Run workflow**.
6. Download the candidate artifact from the completed run.

Scheduled times: 04:17 and 16:17 UTC (09:47 and 21:47 IST). GitHub may delay scheduled runs.
Search phrases are editable in `config/search_terms.txt`.

## Ranking
The score is based on:
- 55% log of views per day
- 20% log of total views
- 25% log of combined like and comment rates

This is a sortable discovery heuristic, not a prediction of future virality or a measure of clip quality. Hidden/disabled public metrics are treated as zero. Very new videos use a minimum age floor of 0.25 days to limit unstable velocity spikes.

## Cost and limits
The workflow uses standard GitHub-hosted runners in a public repository. YouTube Data API quota applies; each `search.list` request consumes quota units. Check Google Cloud Console for the project's current quota and usage. No paid service or billing activation is part of this project.

## Security
Never commit API keys, OAuth tokens, cookies, or passwords. Store keys in GitHub Actions secrets. This repository is public: do not commit private footage or personal data.
