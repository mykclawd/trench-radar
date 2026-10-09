---
name: trench-radar
description: Daily crypto culture + trench-news digest (upstream Bankr skill, reference copy).
---

> Reference copy of the upstream Bankr `trench-radar` skill (Bankr skill catalog), as forked by myk.
> It is the base methodology only. `PROMPT.md` is what we actually run and overrides this file where they conflict.
> Tool names below (`search_tool`, `execute_cli`, `edit_file`, `market_intelligence`) are Bankr agent tools; map them to your own web search, shell and file tools.

# Trench Radar

The whole picture of crypto culture — not a coin scanner. The question this skill answers is "what happened in crypto the last day or two?": the drama, the viral moments, the narrative shifts, the launches, the beefs, the memes, the policy shocks CT is reacting to. Coins are PART of that culture — a runaway memecoin on a new chain is a culture story — but they are one section of the digest, never the whole digest.

The core insight from real runs: social/narrative data tells you what the story IS; onchain velocity data is a supporting signal that catches coin-shaped stories before recap articles exist. Culture layer leads, onchain layer feeds it.

## Files This Skill Maintains

Two files in the Bankr file system (create on first run if missing, then ALWAYS `edit_file` — never `create_file` on an existing file, that spawns duplicates):

1. `trench-seeds.md` — the editable watchlist (seed accounts, project/media seeds, keywords, chains). Installer customizes this; it parameterizes every run.
2. `trench-log.md` — dedup memory. Stories already covered (culture stories AND coins), with date + a one-line state stamp. Runs report DELTAS ("ansem beef: covered yesterday, today he responded — update, not rerun"), never reruns.

### First-Run Bootstrap

If `trench-seeds.md` doesn't exist, create it with these defaults and tell the user it's theirs to edit:

```
# Trench Seeds — edit freely, every section parameterizes the digest

## Seed Accounts (KOLs / trench natives — the culture graph)
- 0xdeployer
- blknoiz06
- jessepollak
- rbthreek
- 0xmikedee
- 100xdarren
- frankdegods
- ezbruv

## Project / Media Seeds (official + news accounts — launches, features, headline coverage)
- raydium
- uniswap
- cointelegraph

## Candidate Accounts (auto-promoted by one-hop branching, review + promote to Seed or delete)
(empty)

## Culture Topics to Watch
- founder / KOL drama and beefs
- viral trader stories (PnL screenshots, $X → $Y)
- new chain or product launches
- airdrop meta and farming drama
- exploit / rug fallout and community response
- policy + regulation moments CT reacts to
- memes and running jokes gaining steam
- ecosystem migrations and rotations

## Chains to Watch
- base
- solana
- robinhood chain
- monad

## Muted (never report)
(empty)
```

If `trench-log.md` doesn't exist, create it with a `## Covered Stories` section (entries: date, story, type [culture/coin/launch/drama], one-liner, state stamp) and a `## Watchlist Deltas` section.

## The Three-Layer Workflow

Run in order. Layer 1 is now the CULTURE scan; onchain velocity is Layer 2 and feeds the coins section only.

### Layer 1 — Culture Scan (the main event)

Read `trench-seeds.md` first. Two seed classes, two jobs:
- **Seed Accounts** (KOLs): what are they posting, arguing about, laughing at, quote-tweeting? This is the culture graph and the source of one-hop candidate discovery.
- **Project / Media Seeds** (official project + news accounts): launches, features, listings, headline coverage. News layer only — do NOT branch off their reply graphs (noise).

**FRESHNESS GATE (hard rule):** every story must have a verifiable beat in the LAST 24 HOURS (48h absolute max for a slow-burn story with a new development). Search engines resurface old drama constantly — before including any story, verify its actual date from the source post/article timestamp. If the originating event is older than 48h and there is no NEW beat inside the last 24h, DROP IT — or, if it was previously covered, it can only appear in "deltas since last run" with the new beat. Known failure mode: a months-old KOL post (e.g. a January "reach/spam" beef) surfacing in search results and getting reported as a fresh headline. Free-mode queries should include date qualifiers ("today", the exact date, "last 24 hours") and result publication dates must be checked, not assumed.

Two modes; ALWAYS degrade gracefully:

**Free mode (default, no API keys):**
- Run 3-5 `search_tool` queries built from the Culture Topics + seed handles + watched chains, ALWAYS with date qualifiers (e.g. "crypto twitter drama <today's date>", "<seed handle> post last 24 hours", "<chain> launch reaction <today's date>"). Vary queries per run; the goal is the STORY landscape, not price data.
- For each candidate story, confirm the underlying event's timestamp before it enters the digest (see Freshness Gate). A recap article published today about an old event does NOT make the event fresh.
- Run `get_social_sentiment_for_ticker` on 1-2 anchor tickers (BTC/ETH/SOL or whatever the stories orbit) with context like: "Recap crypto twitter CULTURE the last 24h — drama, beefs, viral moments, narrative shifts, memes, who's fighting with whom, what stories dominated. Not price analysis. Pay attention to these accounts: <seed list>."
- One `search_tool` pass on the project/media seeds for launch/feature/headline news, same date qualifiers.

**Power mode (only if `X_BEARER_TOKEN` env var is set — check with `get_env_vars`):**
- `execute_cli` with packages `["twitter-api-v2@1.17.2"]`, `includeEnvVars: true`, invoke scripts with `bun` (node is NOT available in the sandbox).
- Pull recent tweets (last 24h; 48h only for delta checks) from every seed account AND project/media seed (userByUsername → userTimeline), rank by engagement velocity (likes+RTs per hour). Discard anything older regardless of engagement.
- The top-engagement posts ARE the culture stories. Cluster them: who's talking about the same thing = a story.
- One-hop branching from high-engagement KOL posts ONLY: extract accounts they're QTing/replying to and topics/tickers they reference. Append promising accounts to `## Candidate Accounts` in trench-seeds.md.
- NOTE: X search/timeline access requires a paid API tier. If calls 403/429, fall back to free mode silently and note "power mode unavailable" once at the end. Never make the skill feel broken because keys are missing.

**Signal classes to hunt for (both modes) — culture-first:**
- Drama and beefs: who's fighting, what's the accusation, how's CT split
- Viral moments: posts, memes, PnL stories, "X followed Y" moments that turbo narratives
- Narrative shifts: what CT believed yesterday vs today ("memecoins are dead" → "RH chain summer")
- Launches and product moments: new chains, features, apps, listings — and the REACTION to them
- Fallout stories: exploits, rugs, failed migrations, and the community response
- Policy/macro moments only as CT reacts to them (the reaction is the story)
- Coin-shaped culture: a runner is a story when it has lore, a moment, or a rotation behind it — not just a % gain

### Layer 2 — Onchain Velocity (supporting signal, feeds the coins section)

1. `market_intelligence` — trending, top gainers, new pools.
2. DEX data via `execute_cli` with curl (public, no auth):
   - DexScreener: `curl -s "https://api.dexscreener.com/token-profiles/latest/v1"` and `curl -s "https://api.dexscreener.com/latest/dex/search?q=<chain-or-ticker>"`
   - GeckoTerminal new pools per watched chain: `curl -s "https://api.geckoterminal.com/api/v2/networks/<network>/new_pools" -H "accept: application/json"`
3. Promotion rule: <7 days old with volume/mcap >0.5, OR appearing in both trending and a watched chain's new pools → run a quick sentiment/search pass to see if there's a STORY behind it (lore, a moment, a rotation). Cap at 3 coin stories per digest.
4. A coin with big numbers but no narrative gets one line in "coins worth noting" at most. A coin WITH a narrative graduates into the culture sections.
5. Noise filter — SILENT: sub-$5K fdv pools, single-buyer pools, and narrative-free new-pool churn are dropped WITHOUT COMMENT. Never write lines like "new-pool churn was pure noise this run" or list the tickers you skipped — the digest only contains what made the cut. Filtering is invisible to the reader.
6. Cross-reference everything against `trench-log.md` — already-covered items only reappear with a material delta.

### Layer 3 — Digest + Memory

Compose with this exact template (consistency makes it a product). Culture leads, coins follow:

```
TRENCH RADAR — <date>

headline stories:
• <the 2-3 things that defined CT this window — drama, launch, viral moment, shift>

culture + drama:
• <who's beefing / what went viral / what meme is running — with the why>

narrative shifts:
• <what CT believed before vs now, and what flipped it>

builders + launches:
• <new chains, products, features, listings — and the reaction>

coins worth noting:
• <TICKER> — <chain> — <stat> — <the story behind it, or one line if it's just numbers>

who's talking (seeds):
• <seed account>: <what they said/did, engagement>

deltas since last run:
• <previously covered story: then vs now>

one-liner: <the single takeaway>
```

Sections with nothing real get dropped, not padded. Then update `trench-log.md` via `edit_file`: append covered stories with type + state stamp AND the story's origin date (so future runs can spot staleness instantly), update deltas. If candidates were added to trench-seeds.md, mention it so the user reviews them.

## Automation Recipe (paste verbatim into a Bankr automation)

Cron runs in UTC. Suggested: `0 13,22 * * *` (2x daily). Select **Telegram** as the output destination — the digest is delivered natively, no bot token needed.

Paste this as the automation command, verbatim, no prefix:

> Run the trench-radar skill for a scheduled culture digest. Steps: (1) Load the trench-radar skill with use_skill. (2) Read trench-seeds.md and trench-log.md. (3) Run Layer 1 culture scan: searches across the Culture Topics + seed accounts (power mode via X API if X_BEARER_TOKEN is set, otherwise free mode), enforcing the 24h freshness gate — verify event timestamps, drop stale stories. (4) Run Layer 2 onchain velocity: market_intelligence + DexScreener/GeckoTerminal curls; promote at most 3 coin stories that have a narrative behind them. (5) Compose the digest with the skill's culture-first template, reporting deltas for already-covered stories instead of reruns. (6) Update trench-log.md with edit_file. (7) Return the digest as the final message so it's delivered to Telegram.

## Setup for Installers

1. Nothing required. Works out of the box in free mode with zero API keys.
2. Edit `trench-seeds.md` after the first run — YOUR seed accounts, project/media seeds, culture topics, chains. Defaults are a starter set.
3. Optional power mode: add `X_BEARER_TOKEN` via the Bankr terminal sidebar → Env Vars (X API bearer token with read access; timeline/search access requires a paid X API tier).
4. Optional: create the automation above for scheduled Telegram delivery.

## Rules

- FRESHNESS GATE: a story enters the digest only with a verified beat in the last 24h (48h max with a new development). Verify source timestamps — recap articles and search results resurface old events; publication date ≠ event date. Stale stories are dropped silently or moved to deltas if previously covered.
- CULTURE FIRST: if a digest reads like a token screener, the run failed. Coins appear when they carry a story; max 3 coin stories + a short "worth noting" list.
- SILENT FILTERING: never narrate what was skipped. No "skipped X/Y/Z", no "pure noise this run", no meta-commentary about filtering. Sub-$5K fdv / single-buyer / narrative-free churn simply never appears in the digest.
- NEVER skip the trench-log.md cross-reference — repeated stories kill digest trust.
- NEVER let missing X keys degrade the experience loudly; free mode is the product, power mode is a bonus.
- ALWAYS `edit_file` for trench-seeds.md and trench-log.md updates; `create_file` only on true first run.
- Drop empty sections; never pad. Signal, not volume.
- This skill is read-only: it NEVER trades, transfers, or submits transactions based on what it finds. If the user wants to act on a finding, that's a separate explicit request.