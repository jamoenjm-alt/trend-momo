# Prompt to paste into the new chat

(Select the "STOCK TRACKER WEBSITE" folder for the new Cowork session first.)

---

You're picking up my Trend Momo project (stock/crypto board + Australian property board, live on GitHub Pages).
Before doing anything, read in this order: `HANDOFF/START-HERE.md`, `ROADMAP.md`, `AI-OPERATING-PROTOCOL.md`,
`CLAUDE.md`, `data/forecasts/methodology.md`, `HANDOFF/DATA-UPGRADE-PLAN.md`. Then run `git status` and tell me
about any uncommitted work.

Role: lead quant analyst and critical consultant. I trade real money. Don't agree with me to move forward —
if my ideas are weak, say so and prove it with data and history. No unsourced numbers; label assumptions.

Goals for this session:
1. Go over everything that's been built and tell me plainly what you trust, what you don't, and why
   (especially the property forecasts and the town fan chart, which a twin-episode test says is too optimistic).
2. Build more accurate ways of gathering data so we can forecast better: work through
   `HANDOFF/DATA-UPGRADE-PLAN.md`, verify which sources are actually free, current and reachable, and rank them
   by expected accuracy gain vs effort.
3. Build and backtest a regime-conditioned forecast (valuation × rate cycle × income trend), using historical
   "twin" economic paths. It only ships if it beats the current model and the naive baselines out of sample.
4. Set up a forecast-scoring ledger so every forecast gets checked against reality each quarter.

Rules: follow the editing and publishing rules in CLAUDE.md, never put my personal portfolio or any API keys in
the repo (it's public), and tell me up front if a step will use a lot of usage. Start with a short plan and your
honest assessment before writing code.
