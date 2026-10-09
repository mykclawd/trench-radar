# Trench Radar

Trench Radar is a daily crypto culture and news digest. Once a day, an LLM agent researches the last 24 to 48 hours (news, crypto Twitter drama, launches and trending onchain pools) and publishes a self-contained HTML report with a meme-style hero image.

This repo is a snapshot of the production setup as of 2026-10-09. It covers the research "brain" and the HTML output. Scheduling, hosting and our internal ops tooling are not included.

See `examples/2026-10-09/index.html` for a real report. Open it locally; the hero image is in `examples/images/`.

## What's here

| Path | What it is |
|---|---|
| `PROMPT.md` | The complete run instructions. This is the brain. Paste it as the agent's task with the placeholders filled in. |
| `templates/report.html` | The report design: inline CSS plus one example of every component. Used as the base on the first run. |
| `scripts/audit.sh` | Mechanical quality gate: stale dates, dashes, banned phrases, images, file freshness. |
| `scripts/hero_image.py` | Hero image generator for any OpenAI-compatible `/images/generations` API. Normalizes output to 16:9. |
| `scripts/og_meta.py` | Injects Open Graph and Twitter card tags so report links unfurl with the hero image. |
| `examples/2026-10-09/index.html` | A real published report. |
| `examples/digest-entry.md` | One day of the dedup and deltas memory file, in the format the agent writes. |
| `reference/bankr-trench-radar-skill.md` | The upstream Bankr skill this grew from. `PROMPT.md` overrides it. |

## How a run works

1. The agent reads yesterday's entry in the digest memory file.
2. It researches with a hard cap of 10 search/fetch calls: a news-first scan, a culture scan, a mandatory public-figure X search, and GeckoTerminal trending pools on Base, Solana, Ethereum, Robinhood Chain and BNB Chain.
3. It applies the selection rules: a 48-hour freshness rule on every story, separate bars for platform news and viral drama, and thresholds for tokens that must appear.
4. It copies yesterday's report and rewrites it section by section in small edits. It never writes the whole file in one call.
5. It generates the hero image, runs the quality gate, publishes the dated and latest copies, injects link-preview tags, and prepends today's entry to the digest file.
6. It replies with a one-line delivery message and the dated permalink.

## Requirements

- **An agent runtime with tools:** web search, URL fetch, shell, and file read/edit. We run it on [OpenClaw](https://github.com/openclaw/openclaw) as an isolated daily cron job with a 1800s timeout. Any harness with those tools works (Claude Code, Codex, a custom loop).
- **A large-context model.** Use 400k tokens of context or more. Research output is bulky and composition happens last. We currently run `gpt-6.1-sol`, with Claude Sonnet and GPT-5.x as fallbacks. Smaller models tended to fail at the composition step.
- **X search.** We use `bankr agent prompt '<question>'` from the Bankr CLI, which has live X search and needs a Bankr API key. The X API (paid tier) or another X search tool also works. Without X search the report still runs but misses X-only stories.
- **An image model** (optional) for the hero. Any OpenAI-compatible images endpoint works. Text legibility matters, because the hero prompt puts tickers and numbers in the image.
- **Python 3.9+ with Pillow** for `hero_image.py`. Bash, curl and GNU grep (`-P`) for `audit.sh` and the image checks.
- **A static file server** that serves your reports directory at `<site>/trenches/`.

No paid market-data APIs are needed. GeckoTerminal and DexScreener are public.

## Setup

1. Pick a reports directory and a public URL. For example, serve `/srv/reports` at `https://reports.example.com`, so the agent writes to `/srv/reports/trenches`.
2. Create an empty digest memory file, for example `trench-radar-digest.md`.
3. Copy `templates/report.html` to `<reports>/trenches/<yesterday>/index.html`. The first run copies "yesterday's" report as its base.
4. Fill the placeholders in `PROMPT.md` (table at the top). For `{{HERO_CMD}}`, wrap `scripts/hero_image.py` with its environment set:
   ```bash
   IMAGE_API_KEY=... IMAGE_API_BASE=https://api.openai.com/v1 IMAGE_MODELS=gpt-image-1 \
   REPORTS_DIR=/srv/reports/trenches SITE_URL=https://reports.example.com \
   python3 scripts/hero_image.py "$@"
   ```
5. Run the agent once by hand and read the output against `examples/2026-10-09/index.html`.
6. Schedule it. Ours runs at `0 8 * * *` America/New_York.

## Things we learned the hard way

These are encoded in `PROMPT.md`, each with the incident behind it. They are the reason the prompt is long:

- **Search rank is not freshness.** Search engines resurface big past incidents as the top result for a project. Without an explicit event-date check per story, a three-week-old exploit ran as the lead headline.
- **Running stories need a market catalyst.** Without a new-development rule, a public-figure saga kept running for days on social chatter alone.
- **Context blowup kills composition.** The 10-call research cap and small `maxChars` exist because runs died mid-report.
- **Same-day reruns must rebuild.** The agent once treated an existing file as done and published nothing new. The copy-then-edit process and the file-age check exist for this.
- **Models narrate their process.** Left alone, they write "we searched X and found nothing" or "included because it met the volume threshold." The prompt bans that explicitly, and `audit.sh` greps for the worst phrases.
- **Truncated API responses drop tokens silently.** One trending token vanished because the Base response was cut off.

## Not included

These are specific to our infrastructure:

- the Google Sheet one-liner writer and the Slack workflow that reads it
- a watchdog that re-checks outputs after the run and retriggers on failure
- a daily model picker that chooses the cheapest qualifying model and patches the cron job
- live-price image model selection across providers (`hero_image.py` uses a fixed model order instead)

## Disclaimer

The report is journalism about markets, not trading advice. The agent is read-only: it never trades or moves funds.
