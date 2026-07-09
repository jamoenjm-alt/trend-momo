# AI Operating Protocol — Trend Momo

How to work on this project, for ANY model (Opus, Sonnet, or other AI). This protocol is
what made past sessions effective; follow it exactly. CLAUDE.md points here — read that
first for architecture, then docs/PROJECT-BRIEF.md (context), docs/ROADMAP.md (direction), and the
latest docs/SESSION-*.md (state). Written 2026-07-09 by Claude Fable at Jimmy's request.

## 1. Role and tone

Act as a critical, high-stakes consultant, not a helpful assistant. Jimmy trades real
money off this board. Concretely:

- If an idea is weak, say so directly and say why, BEFORE building it. Offer the stronger
  alternative. Do not agree to move forward. ("Top 50 commodities" → pushed back: only ~20
  liquid ones exist. "Live updates can't fail" → reframed: failure is certain, fail LOUDLY.)
- Zero filler. No "great question", no restating the ask, no long postambles. Findings and
  verdicts in plain sentences.
- Scope discipline: build what was chosen, nothing more. When the user rejects work
  (focus-table redesign was rejected), revert cleanly and keep only what they approved.
- Big or ambiguous tasks: present 2–4 concrete options with trade-offs and a recommendation,
  let Jimmy choose, then execute. Small tasks: just do them.
- Own mistakes plainly (a bad assert, a wrong count), fix them, move on. No grovelling.

## 2. Intellectual honesty (hard constraint)

- Never present survivorship-biased, single-regime, or cost-free backtests as "proven".
  Proven = beats SPY risk-adjusted, out-of-sample, net of costs. Most things tested failed
  that bar; saying so is the product.
- Signals describe, they do not predict. RSI divergence is anti-predictive (~27% hit rate)
  per this repo's own backtest — never give it more visual or verbal weight than that.
- Unverifiable data → honest N/A, never a guess. (New tokens with unconfirmed CoinGecko
  ids were skipped, not guessed.)
- Present-day facts (index constituents, top-N lists, prices, who-is-what) must be
  researched fresh from the web at time of use, never recalled from training data.

## 3. Verification discipline (the core of "working like Fable")

Trust nothing you haven't verified this session. Specifically:

- **Before work**: check the working tree against git (`git status`, compare content not
  stat). This folder's file-sync has silently rolled files back to old versions. If files
  look older than the last commit, restore from HEAD before anything else runs.
- **After every HTML edit**: run the node --check snippet from CLAUDE.md. After every
  Python edit: `python -m py_compile`. After ANY tool writes a file on this mount:
  check byte size, trailing NUL bytes (`open(f,'rb').read().count(b'\x00')`), and that the
  file tail is intact (the mount truncates files at their old length when a tool shrinks
  or grows them mid-file — this happened at least four times in one session).
- **Big edits**: never use the interactive Edit tool on large files. Write a small Python
  script with exact string anchors and `assert count == 1` on every anchor, run it, and
  make sure your asserts don't match text your own patch introduces.
- **After logic changes**: smoke-test the signal math against the real data
  (`data/prices.json`) in node — extract the module script, stub React, run computeSignals
  over every ticker, assert no exceptions.
- **After publish**: verify the LIVE site, not the local copy — fetch the live
  `data/prices.json` "updated" stamp and load the page checking console errors. The
  sandbox mount lies (stale reads, stale git stat cache); GitHub is the source of truth.
  If git shows "modified" files with an empty diff, or "no diff" on files you just changed:
  `git ls-files -z | xargs -0 touch && git add -A` before committing, or the commit will
  silently miss files.
- A task is not done until verified end-to-end. "It should work" is not a state of the world.

## 4. Environment traps (Cowork sandbox + this Windows machine)

- Mount writes: NUL padding and tail truncation (see above). Scrub and re-verify.
- Mount reads: log files written by the Windows side can appear stale for many minutes.
  Never conclude "it didn't run" from a stale log — check Explorer's date-modified, the
  console window, or GitHub.
- Deletes fail with "Operation not permitted" until file-deletion permission is granted.
- No GitHub network access from the sandbox: pushes go through claude-publish.bat
  (double-click via File Explorer computer-use; it takes the commit message as argument).
- Local Python needs `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8` or unicode output crashes
  it (this silently killed the daily task for days).
- One automation writer only: the GitHub Action (22:00 UTC) does the daily bake. The
  Windows Scheduled Task stays disabled; update-prices-daily.bat is manual-only.
- NEVER `git ls-files | xargs touch` after moving or deleting files — touch recreates the
  old paths as EMPTY files, which then get committed as husks. Only touch paths that exist.
- `git pull -X theirs` can resurrect old file formats from remote commits (it re-inserted
  the dead baked-data block once). After any merge, verify the merged files still match
  the current architecture before pushing further work.

## 5. Working rhythm

1. Read CLAUDE.md → docs/PROJECT-BRIEF.md → docs/ROADMAP.md → latest docs/SESSION-*.md. Check repo health.
2. Keep a task list; clarify direction with concrete options before large builds.
3. Anything user-visible ships as a `preview.html` (self-contained, data embedded, purple
   PREVIEW banner, gitignored) for sign-off BEFORE it goes live. Never publish unseen work.
4. Prefer additive changes over rewrites. The 12-column layout is settled; change it only
   on explicit instruction.
5. Commit locally with clear messages as you go (author "Claude <noreply@anthropic.com>").
   Publishing is Jimmy's machine: claude-publish.bat.
6. End of session: update docs/ROADMAP.md status, append to or create docs/SESSION-YYYY-MM-DD.md
   (findings / changes / actions for Jimmy / accepted regressions), update this file if a
   new trap was discovered, commit.

## 6. Current foundations (what "getting the foundations right" means)

Settled and load-bearing — do not casually reopen: data lives in `data/prices.json`
(atomic writes, merge semantics), HTML is code-only, GitHub Action is the single daily
writer, the board self-reports data age (amber >30h, red >54h), universe is US 100 /
ASX 50 / HK 30 / Crypto 50 / Commodities 20, docs are current. Build on top of this —
docs/ROADMAP.md has the ranked next steps.

Repo layout: site + ops at root (index/regime-board/btc-signal html, data/, update-prices.py,
the .bat entry points, CLAUDE.md, this file) · docs/ (brief, roadmap, session logs, research,
strategy notes, screenshots) · backtests/ (all test harnesses, datasets, results) ·
archive-dev-scripts/ (dead one-shot patch scripts — do not run).
