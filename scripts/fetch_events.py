"""Thursday-morning Fort Lauderdale weekend event digest.

Calls Claude with the server-side web_search tool to gather the weekend's
events, formats a compact plain-text message, and POSTs it to ntfy.sh.

Env:
  ANTHROPIC_API_KEY  required
  NTFY_TOPIC         required (e.g. "daniel-weekly-notifications-1993")
"""

from __future__ import annotations

import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = 8192
MAX_WEB_SEARCHES = 15
NTFY_URL_BASE = "https://ntfy.sh"
# ntfy.sh free tier allows up to ~4 KiB message bodies. Stay under that.
MAX_BODY_CHARS = 3800


def weekend_window(now: datetime) -> tuple[str, str, str]:
    """Return (friday_iso, sunday_iso, human_range) for the upcoming weekend."""
    # Monday=0 ... Sunday=6. If run Thursday, Friday is +1 day.
    days_to_friday = (4 - now.weekday()) % 7
    if days_to_friday == 0 and now.hour >= 18:
        days_to_friday = 7
    friday = (now + timedelta(days=days_to_friday)).date()
    sunday = friday + timedelta(days=2)
    human = f"{friday.strftime('%a %b %-d')} – {sunday.strftime('%a %b %-d')}"
    # %-d not supported on Windows; the script runs on ubuntu-latest so fine.
    return friday.isoformat(), sunday.isoformat(), human


def build_prompt(fri: str, sun: str, human: str, max_chars: int) -> str:
    return f"""Find interesting events happening this upcoming weekend ({human}, i.e. {fri} through {sun}) in the greater Fort Lauderdale area.

Cities to cover: Fort Lauderdale, Hollywood, Pompano Beach, Dania Beach, Plantation, Sunrise, Davie, Wilton Manors, Oakland Park, Las Olas, downtown FTL, the beach area.

INCLUDE:
- Car shows / cars & coffee meetups
- Comedy shows
- Theater / stage performances / plays / musicals
- Festivals, fairs, street markets
- Grand openings of restaurants, shops, or venues (like the recent Smorgasbord FTL opening)
- Art walks, gallery openings, museum exhibits
- Food events (food truck rallies, tasting events, pop-ups)
- Cultural events, fireworks, parades, unique one-off happenings

EXCLUDE:
- Concerts, DJ nights, music festivals
- Bar events, club nights, happy hours, wine/beer/cocktail tasting parties
- Anything primarily centered on drinking or live music

Use the web_search tool aggressively. Try multiple queries such as:
- "Fort Lauderdale weekend events {fri}"
- "things to do Fort Lauderdale this weekend"
- "Fort Lauderdale car show {fri[:7]}"
- "Fort Lauderdale comedy shows this weekend"
- "Broward theater this weekend"
- "Fort Lauderdale grand opening {fri[:7]}"
- "South Florida festivals this weekend"
Check sources like Visit Lauderdale, Eventbrite, Broward.org, Sun Sentinel events, Secret Florida, Do305, Time Out Miami/Fort Lauderdale. Follow up on promising calendar pages with additional searches or direct lookups to capture each event's address, time, and official link.

For EACH event you include, capture:
  • NAME — short event name
  • WHEN — day and start time (e.g. "Fri 7:30pm" or "Sat 10am–2pm")
  • WHERE — venue name + street address + city (e.g. "Revolution Live, 100 SW 3rd Ave, Fort Lauderdale")
  • WHAT — one-sentence description of what it is / why it's interesting
  • LINK — a direct URL to the event page, ticket page, or official listing (full https URL, no shorteners)

If you cannot verify a time OR address OR link for an event, DROP it. Do not make up details.

OUTPUT FORMAT — plain text only, no markdown, under {max_chars} chars total. Structure:

Weekend in Greater FTL — {human}

== CAR SHOWS ==
• {{NAME}}
  {{WHEN}} · {{WHERE}}
  {{WHAT}}
  {{LINK}}

• {{next event}}
  ...

== COMEDY ==
• ...

== THEATER ==
• ...

== GRAND OPENINGS / NEW ==
• ...

== FESTIVALS & MARKETS ==
• ...

== OTHER ==
• ...

Rules:
- Only include sections that actually have events.
- Each event block is 4 lines: name, when+where, what, link. Blank line between events.
- Keep descriptions to one short sentence (<= 100 chars).
- Skip generic recurring stuff (normal weekly farmers markets) unless this weekend's edition has something special.
- If the full digest would exceed {max_chars} chars, trim weaker/lower-interest events first — never trim the key fields of the events you keep.
- Do NOT wrap in code fences. Do NOT add commentary before or after. Return ONLY the digest body.
"""


def call_claude(prompt: str) -> str:
    client = Anthropic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": MAX_WEB_SEARCHES,
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )
    # Concatenate all text blocks in the final message.
    parts: list[str] = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    text = "\n".join(p.strip() for p in parts if p.strip())
    if not text:
        raise RuntimeError(f"Claude returned no text. stop_reason={resp.stop_reason}")
    return text.strip()


def post_ntfy(topic: str, title: str, body: str) -> None:
    url = f"{NTFY_URL_BASE}/{topic}"
    data = body.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Title": title,
            "Tags": "calendar",
            "Priority": "default",
            "Content-Type": "text/plain; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        if r.status >= 300:
            raise RuntimeError(f"ntfy returned HTTP {r.status}")


def main() -> int:
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        print("ERROR: NTFY_TOPIC env var is required", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY env var is required", file=sys.stderr)
        return 2

    now = datetime.now(ZoneInfo("America/New_York"))
    fri, sun, human = weekend_window(now)
    print(f"Target weekend: {human} ({fri} to {sun})")

    prompt = build_prompt(fri, sun, human, MAX_BODY_CHARS)
    print("Calling Claude with web_search...")
    digest = call_claude(prompt)
    print(f"Got digest ({len(digest)} chars)")
    if len(digest) > MAX_BODY_CHARS:
        print(f"Digest over {MAX_BODY_CHARS} chars; truncating.")
        digest = digest[: MAX_BODY_CHARS - 20].rstrip() + "\n… (truncated)"
    print("-" * 40)
    print(digest)
    print("-" * 40)

    title = f"FTL Weekend — {human}"
    post_ntfy(topic, title, digest)
    print(f"Pushed to ntfy.sh/{topic}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
