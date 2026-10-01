/**
 * Background Service Worker for HiringCafe Capture Queue
 * Relays API calls to http://localhost:8000 to bypass Private Network Access (PNA) rules on HTTPS pages.
 */

const API_BASE = "http://localhost:8000";
let captureState = {
  running: false,
  statusText: "Ready",
  progress: null,
  error: null,
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "API_REQUEST") {
    const { endpoint, method = "GET", body = null } = message;
    const fetchOptions = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    };
    if (body && (method === "POST" || method === "PUT")) {
      fetchOptions.body = JSON.stringify(body);
    }

    fetch(`${API_BASE}${endpoint}`, fetchOptions)
      .then(async (res) => {
        const text = await res.text();
        let data = {};
        try {
          data = JSON.parse(text);
        } catch {
          data = { text };
        }

        if (!res.ok) {
          sendResponse({ success: false, status: res.status, error: data.detail || text });
        } else {
          sendResponse({ success: true, data });
        }
      })
      .catch((err) => {
        sendResponse({
          success: false,
          error: `Could not reach backend at ${API_BASE}. Is Resume Maker running? (${err.message})`,
        });
      });

    return true; // Keep channel open for async response
  }

  if (message.type === "UPDATE_CAPTURE_STATE") {
    captureState = { ...captureState, ...message.state };
    return false;
  }

  if (message.type === "GET_CAPTURE_STATE") {
    sendResponse(captureState);
    return false;
  }
});
