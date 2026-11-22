# GTA6-Viral-Clips-Automation

Zero-paid-service starter project to discover public GTA 6-related YouTube videos, rank
candidates by visible engagement statistics, and maintain a duplicate-detection list
using GitHub Actions.

## Current scope
- Scheduled discovery twice daily and manual workflow dispatch.
- Official YouTube Data API for public video metadata.
- Transparent weighted log score: Views 25%, Likes 35%, Comments 40%.
- JSON and CSV candidate reports uploaded as a 7-day workflow artifact.
- Seen video IDs persisted to reduce repeated candidates.
- Python standard library only; no third-party Python packages.

## Not included
- No downloading/re-uploading YouTube, Twitch, Kick, or other creators' videos.
- No automatic clipping from third-party URLs.
- No YouTube upload or publishing. Publishing remains disabled pending separate design,
  testing, and explicit approval.
- No paid service, Render deployment, subscription, or billing activation.

Use only source footage that you own or have explicit permission/licensing to edit and publish.
Cropping, captions, or music alone do not guarantee copyright clearance or monetization eligibility.

## Setup
1. In Google Cloud Console, create/select a project and enable **YouTube Data API v3**.
2. Create an API key restricted to YouTube Data API v3.
3. In this repository, open **Settings → Secrets and variables → Actions**.
4. Add a repository secret named `YOUTUBE_API_KEY`.
5. Open **Actions → GTA 6 YouTube Discovery → Run workflow**.
6. Download the `gta6-candidates-...` artifact from the completed run.

Scheduled times: 04:17 and 16:17 UTC (09:47 and 21:47 IST). GitHub may delay scheduled runs.
Search phrases are editable in `config/search_terms.txt`.

## Ranking formula
```
score = 0.25 × ln(1 + views)
      + 0.35 × ln(1 + likes)
      + 0.40 × ln(1 + comments)
```
Like and comment rates are also reported. Hidden/disabled public metrics are treated as zero.
This is a candidate shortlist, not a measure of clip quality or permission to reuse footage.

## Cost and limits
The workflow uses standard GitHub-hosted runners in a public repository, which GitHub
currently documents as free. YouTube Data API quota applies. Google currently documents
100 search.list calls/day and 10,000 units/day for other methods by default; check the
Google Cloud Console for the actual project quota.

## Security
Never commit API keys, OAuth tokens, cookies, or passwords. Store keys in GitHub Actions
secrets. This repository is public: do not commit private footage or personal data.

## Next stages
1. Validate discovery output and ranking.
2. Add a local FFmpeg utility for rights-cleared source footage.
3. Only after separate approval, evaluate YouTube OAuth upload and scheduled publishing.
