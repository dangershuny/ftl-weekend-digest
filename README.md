# ftl-weekend-digest

Thursday-morning GitHub Actions job that asks Claude Code to search the web for interesting weekend events in the greater Fort Lauderdale area (car shows, comedy, theater, grand openings, festivals — no music/drinking-centric parties) and pushes a compact, link-rich digest to an [ntfy.sh](https://ntfy.sh) topic.

Uses the official [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action) so it can authenticate with a **Claude Max / Pro subscription OAuth token** — no pay-per-token Anthropic API key required.

## How it works

1. `.github/workflows/ftl-weekend.yml` runs on cron (Thursday 12:00 UTC ≈ 8 AM ET).
2. The Claude Code Action runs the curation prompt, uses WebSearch/WebFetch, and writes the digest to `digest.txt`.
3. A follow-up step POSTs `digest.txt` to `ntfy.sh/<topic>` so your phone gets a notification.

## One-time setup

```bash
# 1. In any terminal where Claude Code is installed and logged in with your Max sub:
claude setup-token
#    → prints a long-lived OAuth token. Copy it.

# 2. Store it as a repo secret:
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo dangershuny/ftl-weekend-digest
#    → paste the token when prompted.
```

## Manual run

```bash
gh workflow run "FTL Weekend Digest" --repo dangershuny/ftl-weekend-digest
gh run watch --repo dangershuny/ftl-weekend-digest
```

## Tuning

- Event types / exclusions: edit the `prompt:` in `.github/workflows/ftl-weekend.yml`.
- Schedule: edit the `cron:` in the same file.
- Destination: change `NTFY_TOPIC` in the "Push digest to ntfy" step.

## Also in this repo

- `.github/workflows/geoffrey-asmus-reminder.yml` — one-off reminder for a Saturday 2026-04-25 2 PM EDT ntfy push. Delete after the show.
