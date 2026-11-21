// Local leaderboard for the GUI (Phase 4 extension, TICKET-04 §3). Same rules as chonoi/leaderboard.py:
// top 10, score descending, ties keep write order (stable sort, new entry appended last), entry {name,score,days_completed,seed}.
// Stored per browser in localStorage "chonoi.lb" as {"entries":[...]}. One entry per finished 5-day campaign (Summary).
// The headless store (--leaderboard) is a separate file; this one never touches the Test Contract.
const KEY = "chonoi.lb";
export const TOP_N = 10;
export const NAME_MAX = 16;

const isEntry = (e) => e && typeof e.name === "string" && Number.isInteger(e.score) && Number.isInteger(e.days_completed) && Number.isInteger(e.seed);
export const rank = (entries) => entries.map((e, i) => [e, i]).sort((a, b) => b[0].score - a[0].score || a[1] - b[1]).map((x) => x[0]).slice(0, TOP_N);

export function load() {
  try {
    const d = JSON.parse(localStorage.getItem(KEY) || '{"entries":[]}');
    return rank((Array.isArray(d?.entries) ? d.entries : []).filter(isEntry));
  } catch (e) { return []; }
}

// returns { entries, place } — place is the 0-based rank of the new entry, or -1 if it did not make the top 10
export function record(name, score, days_completed, seed = 0) {
  const entry = { name: (String(name || "").trim() || "Út Sen").slice(0, NAME_MAX), score: Math.floor(score), days_completed, seed };
  const entries = rank([...load(), entry]);
  try { localStorage.setItem(KEY, JSON.stringify({ entries })); } catch (e) {}
  return { entries, place: entries.indexOf(entry) };
}
