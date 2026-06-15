export async function runLabAction(action) {
  if (action.type === "navigate") {
    window.open(action.navigate, "_blank");
    return { status: "navigated", url: action.navigate };
  }

  if (action.type === "command") {
    return {
      status: "info",
      message: "Bu komutu terminalde çalıştırın:",
      command: action.command,
    };
  }

  if (action.type === "api_get") {
    const response = await fetch(action.endpoint, { method: "GET" });
    return parseResponse(response);
  }

  if (action.type === "api_post") {
    const response = await fetch(action.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(action.body || {}),
    });
    return parseResponse(response);
  }

  throw new Error(`Bilinmeyen action type: ${action.type}`);
}

async function parseResponse(response) {
  const text = await response.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return {
    status: response.status,
    ok: response.ok,
    body,
  };
}

export function formatJson(data) {
  return JSON.stringify(data, null, 2);
}
