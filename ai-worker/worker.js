// Trend Momo — Ask AI proxy (Cloudflare Worker)
// Holds your Anthropic key as a SECRET and answers questions from board data the
// page sends it. The key never reaches the browser. Deploy steps: ai-worker/DEPLOY.md
//
// Required secret:  ANTHROPIC_API_KEY   (wrangler secret put ANTHROPIC_API_KEY)
// Optional vars:    ALLOWED_ORIGIN (default https://jamoenjm-alt.github.io)
//                   MODEL          (default claude-haiku-4-5-20251001)

const DEFAULTS = {
  ORIGIN: "https://jamoenjm-alt.github.io",
  MODEL: "claude-haiku-4-5-20251001",
  MAX_QUESTION: 2000,     // chars
  MAX_CONTEXT: 120000,    // chars (~30k tokens) — keeps cost bounded
  MAX_TOKENS: 800,        // answer length cap
};

function cors(origin) {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

const SYSTEM = `You are the assistant for "Trend Momo — Property", an Australian property trend & momentum board built on SQM Research asking-price data.
Answer ONLY from the DATA block the user provides. The data is a table of markets with: name, state, asking-price index, 12-month % change, trend regimes over four horizons (0-6M, 6M-1Y, 1-2Y, 2-5Y) plus an all-signals regime, gross yield, yield percentile vs the market's own history, vacancy, 12-month rent change and 12-month listings (supply) change.
Rules:
- Be concise and specific; cite the actual numbers from the data.
- If the data does not contain what is asked, say so plainly — do not invent figures or use outside knowledge about specific towns.
- "Best buy" on this board means best VALUE/income (high yield percentile, tight vacancy, rising rents), NOT best recent price performance; a falling asking price can still rank as a buy. Flag that distinction when relevant.
- A high yield percentile often means prices have fallen; note the value-trap-vs-bargain risk when a market is cheap but prices and listings are weakening.
- This is decision-support, not financial advice. You are not a licensed adviser. Do not tell the user to buy or sell; give them the figures and the trade-offs.
- Keep answers under ~180 words unless asked for more.`;

export default {
  async fetch(request, env) {
    const origin = (env && env.ALLOWED_ORIGIN) || DEFAULTS.ORIGIN;
    const headers = cors(origin);

    if (request.method === "OPTIONS") return new Response(null, { headers });
    if (request.method !== "POST")
      return json({ error: "POST only" }, 405, headers);

    if (!env || !env.ANTHROPIC_API_KEY)
      return json({ error: "Server not configured (missing ANTHROPIC_API_KEY)." }, 500, headers);

    let body;
    try { body = await request.json(); }
    catch { return json({ error: "Invalid JSON." }, 400, headers); }

    const question = (body.question || "").toString().trim();
    const context = (body.context || "").toString();
    if (!question) return json({ error: "Ask a question." }, 400, headers);
    if (question.length > DEFAULTS.MAX_QUESTION)
      return json({ error: "Question too long." }, 400, headers);
    if (context.length > DEFAULTS.MAX_CONTEXT)
      return json({ error: "Too much data sent." }, 413, headers);

    const userMsg =
      "DATA (the whole board, tab-separated):\n" + context +
      "\n\nQUESTION:\n" + question;

    let resp;
    try {
      resp = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": env.ANTHROPIC_API_KEY,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: (env && env.MODEL) || DEFAULTS.MODEL,
          max_tokens: DEFAULTS.MAX_TOKENS,
          system: SYSTEM,
          messages: [{ role: "user", content: userMsg }],
        }),
      });
    } catch (e) {
      return json({ error: "Upstream request failed." }, 502, headers);
    }

    if (!resp.ok) {
      const t = await resp.text().catch(() => "");
      return json({ error: "Claude API error (" + resp.status + ")", detail: t.slice(0, 300) }, 502, headers);
    }

    const data = await resp.json();
    const answer = (data.content || [])
      .filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
    return json({ answer: answer || "(no answer)" }, 200, headers);
  },
};

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: Object.assign({ "content-type": "application/json" }, headers),
  });
}
