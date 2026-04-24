# ftl-weekend-digest

Thursday-morning GitHub Actions job that asks Claude to search the web for interesting weekend events in the greater Fort Lauderdale area (car shows, comedy, theater, grand openings, festivals — no music/drinking-centric parties) and pushes a compact, link-rich digest to an [ntfy.sh](https://ntfy.sh) topic.

## How it works

1. `.github/workflows/ftl-weekend.yml` runs on a cron (Thursday 12:00 UTC ≈ 8 AM ET).
2. `scripts/fetch_events.py` calls the Anthropic API with the server-side `web_search` tool, gets back a curated digest, and POSTs it to `ntfy.sh/<topic>`.
3. Your phone (subscribed to the topic in the ntfy app) gets the notification.

## Setup

One-time:

```bash
# 1. Anthropic API key (required)
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..."

# 2. Optional: override the ntfy topic (defaults to daniel-weekly-notifications-1993)
gh variable set NTFY_TOPIC --body "your-topic-name"
```

## Manual run

```bash
gh workflow run "FTL Weekend Digest"
gh run watch
```

## Tuning

- Event types / exclusions: edit the prompt in `scripts/fetch_events.py::build_prompt`.
- Schedule: edit the `cron` in `.github/workflows/ftl-weekend.yml`.
- Message size cap: `MAX_BODY_CHARS` in the script (ntfy.sh free tier ≈ 4 KiB).
