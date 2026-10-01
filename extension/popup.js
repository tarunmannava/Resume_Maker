const captureBtn = document.getElementById("captureBtn");
const statusText = document.getElementById("statusText");
const progressContainer = document.getElementById("progressContainer");
const progressBar = document.getElementById("progressBar");
const hostBadge = document.getElementById("hostBadge");

let activeTab = null;

async function initPopup() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  activeTab = tabs[0];

  if (!activeTab || !activeTab.url || !activeTab.url.includes("hiringcafe.com")) {
    captureBtn.disabled = true;
    hostBadge.textContent = "Inactive";
    hostBadge.style.color = "#f87171";
    statusText.textContent = "Please open a HiringCafe search page before capturing.";
    statusText.className = "status-text";
    return;
  }

  hostBadge.textContent = "HiringCafe OK";
  hostBadge.style.color = "#4ade80";

  // Check ongoing state from background worker
  chrome.runtime.sendMessage({ type: "GET_CAPTURE_STATE" }, (state) => {
    if (state) {
      applyState(state);
    }
  });
}

function applyState(state) {
  if (state.running) {
    captureBtn.disabled = true;
    statusText.textContent = state.statusText || "Processing...";
    statusText.className = "status-text";

    if (state.progress && state.progress.total) {
      progressContainer.style.display = "block";
      const pct = Math.round((state.progress.current / state.progress.total) * 100);
      progressBar.style.width = `${pct}%`;
    } else {
      progressContainer.style.display = "none";
    }
  } else {
    captureBtn.disabled = false;
    progressContainer.style.display = "none";

    if (state.error) {
      statusText.textContent = `Error: ${state.error}`;
      statusText.className = "status-text error-text";
    } else if (state.statusText) {
      statusText.textContent = state.statusText;
      statusText.className = state.statusText.includes("Done") ? "status-text success-text" : "status-text";
    }
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "UPDATE_CAPTURE_STATE") {
    applyState(message.state);
  }
});

captureBtn.addEventListener("click", async () => {
  if (!activeTab || !activeTab.id) return;

  captureBtn.disabled = true;
  statusText.textContent = "Initializing capture in HiringCafe tab...";
  statusText.className = "status-text";
  progressContainer.style.display = "none";

  try {
    // Inject content script into active tab
    await chrome.scripting.executeScript({
      target: { tabId: activeTab.id },
      files: ["content.js"],
    });

    // Send start capture message to content script
    chrome.tabs.sendMessage(activeTab.id, { type: "START_CAPTURE" }, (res) => {
      if (chrome.runtime.lastError) {
        console.warn("Script message response error:", chrome.runtime.lastError.message);
      }
    });
  } catch (err) {
    statusText.textContent = `Failed to start: ${err.message}`;
    statusText.className = "status-text error-text";
    captureBtn.disabled = false;
  }
});

initPopup();
