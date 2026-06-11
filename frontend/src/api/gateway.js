export const gatewayUrl = import.meta.env.VITE_GATEWAY_URL || "http://localhost:3000";
export const defaultPreviewFrontendUrl = "http://localhost:15173";

export async function gatewayJson(path, options = {}) {
  const response = await fetch(`${gatewayUrl}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Gateway request failed: ${response.status}`);
  }
  return data;
}

export function normalizeStreamEvent(rawEvent) {
  return {
    type: rawEvent?.type || "unknown",
    node: rawEvent?.node || "gateway",
    message: rawEvent?.message || "",
    state: rawEvent?.state || null,
  };
}
