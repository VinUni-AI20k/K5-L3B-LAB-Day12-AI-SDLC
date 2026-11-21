async function request(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    signal: AbortSignal.timeout(5000),
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Máy chủ chưa phản hồi.");
  return data;
}

function post(url, body = {}) {
  return request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const liveAdapter = {
  config: () => request("/config"),
  play: (mode) => post("/play", { mode }),
  continueDay: (stage) => post("/continue", stage ? { stage } : {}),
  restart: () => post("/restart"),
  input: (frame) => post("/input", frame),
  state: () => request("/state"),
};
