# ftl-weekend-digest

Wednesday-morning GitHub Actions job that asks Claude Code to search the web for interesting weekend events and pushes **two** compact, link-rich digests to an [ntfy.sh](https://ntfy.sh) topic:

1. **Greater Fort Lauderdale** — 10–20 local events (car shows, comedy, theater, grand openings, festivals — no music/drinking-centric parties).
2. **Bigger events within a ~5-hour drive** — marquee/larger-scale events anywhere within roughly 5 hours' drive of Fort Lauderdale, in any direction (West Palm Beach, the Keys, Naples/Fort Myers, Tampa/St. Pete, Orlando, Daytona, etc.).

Uses the official [`anthropics/claude-code-action`](https://github.com/anthropics/claude-code-action) so it can authenticate with a **Claude Max / Pro subscription OAuth token** — no pay-per-token Anthropic API key required.

## How it works

1. `.github/workflows/ftl-weekend.yml` runs on cron (Wednesday 13:00 UTC ≈ 9 AM ET / 8 AM EST).
2. Two Claude Code Action steps run the curation prompts (local + regional), use WebSearch/WebFetch, and write `events.json` and `events-regional.json`.
3. Dead URLs are dropped, two HTML pages are rendered and deployed to GitHub Pages (`index.html` for local, `regional.html` for the 5-hour-drive list).
4. Two follow-up steps POST a notification each to `ntfy.sh/<topic>` so your phone gets both digests.

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

- Event types / exclusions / counts: edit the two `prompt:` blocks in `.github/workflows/ftl-weekend.yml` (one for local, one for the 5-hour-drive regional list).
- Drive radius: edit the geography/"bigger" guidance in the regional prompt.
- Schedule: edit the `cron:` in the same file (currently Wednesday).
- Destination: change `NTFY_TOPIC` in the "Push ntfy notifications" step (both notifications use the same topic).

## Keeping the schedule alive

GitHub automatically **disables scheduled (cron) workflows in a public repo after 60 days with no new commits** on the default branch — and only commits count (scheduled runs, issues, and tags do not). Since the digest never commits anything on its own, its schedule would silently stop after ~60 idle days.

`.github/workflows/keepalive.yml` prevents this: twice a week it checks how long it's been since the last commit and, once the repo has been quiet ~45 days, writes a dated marker to `.github/keepalive.txt` and pushes it. That commit resets GitHub's 60-day clock and keeps every scheduled workflow in this repo enabled. On an active repo it does nothing, so it adds no commit noise. Tune the window via `THRESHOLD_DAYS` in that file (keep it comfortably under 60).
