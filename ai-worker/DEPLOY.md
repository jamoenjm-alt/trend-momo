# Ask-AI proxy — deploy in ~5 minutes (free)

This is a tiny Cloudflare Worker that holds your Anthropic API key and answers
questions from the property board. The key stays on Cloudflare's servers and is
**never** sent to the browser, so the public page can use it safely.

## What you need
- A free Cloudflare account (dash.cloudflare.com)
- An Anthropic API key (console.anthropic.com → API keys). Billing on this key is
  **yours** — every question costs a fraction of a cent on Haiku. Set a monthly
  spend cap in the Anthropic console.

## Option A — Dashboard (no tools, easiest)
1. Cloudflare dashboard → **Workers & Pages → Create → Create Worker**. Name it
   e.g. `trend-momo-ai`. Deploy the starter, then click **Edit code**.
2. Delete the starter code, paste the entire contents of `worker.js`, click **Deploy**.
3. **Settings → Variables and Secrets**:
   - Add **Secret** `ANTHROPIC_API_KEY` = your key.
   - (optional) Add **Variable** `MODEL` = `claude-sonnet-5` for smarter answers
     (costs more), or leave unset for cheap Haiku.
   - (optional) `ALLOWED_ORIGIN` = `https://jamoenjm-alt.github.io` (already the default).
4. Copy the worker URL (looks like `https://trend-momo-ai.<you>.workers.dev`).
5. On the property board: click **✨ Ask AI → ⚙** and paste that URL once. Done.

## Option B — Wrangler (CLI)
```bash
npm i -g wrangler
wrangler login
cd ai-worker
wrangler deploy worker.js --name trend-momo-ai
wrangler secret put ANTHROPIC_API_KEY      # paste key when prompted
```
Then paste the printed URL into the board (✨ Ask AI → ⚙).

## IMPORTANT — stop abuse / runaway cost
A public AI endpoint on your key **can be hammered**. Protect it:
- **Anthropic console:** set a hard monthly spend limit on the key. Do this first.
- **Cloudflare rate limiting (free):** dashboard → your Worker → **Settings →
  Rate limiting**, add a rule like *10 requests / 10 seconds per IP* on this route.
- The worker already caps question length, data size, and answer length.

If costs ever spike, delete the `ANTHROPIC_API_KEY` secret and the box goes dark
immediately — no code change needed.
