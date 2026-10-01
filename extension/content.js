/**
 * Content Script for HiringCafe Tab
 * Re-fetches the page internally to read fresh __NEXT_DATA__, queries known IDs,
 * paces description fetches with 2-4s jitter, and captures jobs to localhost:8000 via background relay.
 */

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getRandomDelay(minSec = 2.0, maxSec = 4.0) {
  const ms = (minSec + Math.random() * (maxSec - minSec)) * 1000;
  return Math.round(ms);
}

function updateProgress(text, details = null) {
  chrome.runtime.sendMessage({
    type: "UPDATE_CAPTURE_STATE",
    state: {
      running: true,
      statusText: text,
      progress: details,
    },
  });
}

async function fetchPageNextData() {
  const res = await fetch(window.location.href, {
    headers: {
      Accept: "text/html,application/xhtml+xml,application/xml",
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to re-fetch page: HTTP ${res.status}`);
  }
  const html = await res.text();
  const match = html.match(/<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/i);
  if (!match) {
    throw new Error("Could not find __NEXT_DATA__ on HiringCafe page.");
  }
  return JSON.parse(match[1]);
}

async function fetchJobDescription(jobId) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const res = await fetch(`https://hiringcafe.com/api/job-description?id=${encodeURIComponent(jobId)}`);
      if (res.status === 429) {
        console.warn(`[Capture Queue] Rate limited on job ${jobId}. Backing off 12 seconds...`);
        updateProgress(`Rate-limited by HiringCafe. Pausing 12s...`);
        await sleep(12000);
        continue;
      }
      if (!res.ok) {
        console.warn(`[Capture Queue] Job description API returned HTTP ${res.status} for ${jobId}`);
        return "";
      }
      const data = await res.json();
      return (
        data.job?.job_information?.description ||
        data.job_information?.description ||
        data.description ||
        ""
      );
    } catch (err) {
      console.warn(`[Capture Queue] Error fetching JD for ${jobId}:`, err);
      if (attempt === 1) await sleep(3000);
    }
  }
  return "";
}

async function executeHiringCafeCapture() {
  try {
    updateProgress("Reading latest hits from HiringCafe page...");
    const nextData = await fetchPageNextData();
    const pageProps = nextData.props?.pageProps || {};
    const ssrHits = pageProps.ssrHits || pageProps.initialSearchResults || pageProps.jobs || [];

    if (!ssrHits.length) {
      throw new Error("No jobs found on this page. Make sure you are on a search results page with active listings.");
    }

    console.log(`[Capture Queue] Found ${ssrHits.length} total hits in page data.`);

    // 1. Map raw hits
    const mappedJobs = ssrHits.map((h) => {
      const v = h.v5_processed_job_data || {};
      const title = h.job_information?.title || v.core_job_title || "Software Engineer";
      const company = v.company_name || h.company_name || "Company";
      const location = v.formatted_workplace_location || "United States";
      const applyUrl = h.apply_url || v.apply_url || `https://hiringcafe.com/jobs/${h.id}`;
      const yoe = v.min_industry_and_role_yoe ?? null;
      const seniority = v.seniority_level || "";
      const reqSummary = v.requirements_summary || "";
      const tools = v.technical_tools || [];

      return {
        id: String(h.id),
        title,
        company,
        location,
        apply_url: applyUrl,
        requirements_summary: reqSummary,
        technical_tools: Array.isArray(tools) ? tools : [],
        yoe,
        seniority,
        description_text: "",
      };
    });

    const allIds = mappedJobs.map((j) => j.id);

    // 2. Query backend for already captured IDs
    updateProgress(`Checking backend for duplicate jobs (${allIds.length} found)...`);
    const knownRes = await new Promise((resolve) => {
      chrome.runtime.sendMessage(
        {
          type: "API_REQUEST",
          endpoint: "/api/queue/known",
          method: "POST",
          body: { ids: allIds },
        },
        resolve
      );
    });

    if (!knownRes || !knownRes.success) {
      throw new Error(knownRes?.error || "Could not reach Resume Maker queue API.");
    }

    const knownSet = new Set(knownRes.data?.known_ids || []);
    const newJobs = mappedJobs.filter((j) => !knownSet.has(j.id));

    console.log(`[Capture Queue] ${mappedJobs.length} on page, ${knownSet.size} already in queue, ${newJobs.length} net new.`);

    // 3. Fetch each new job's description and save it right away, so the worker can start
    //    immediately and a closed tab doesn't lose the jobs fetched so far.
    let added = 0;
    let duplicates = knownSet.size;
    for (let i = 0; i < newJobs.length; i++) {
      const job = newJobs[i];
      const stepText = `${mappedJobs.length} on page, ${newJobs.length} new, fetching description ${i + 1}/${newJobs.length}: ${job.title} @ ${job.company}`;
      console.log(`[Capture Queue] ${stepText}`);
      updateProgress(stepText, { current: i + 1, total: newJobs.length });

      job.description_text = await fetchJobDescription(job.id);

      const captureRes = await new Promise((resolve) => {
        chrome.runtime.sendMessage(
          {
            type: "API_REQUEST",
            endpoint: "/api/queue/capture",
            method: "POST",
            body: { jobs: [job] },
          },
          resolve
        );
      });
      if (!captureRes || !captureRes.success) {
        throw new Error(
          `Saved ${added} jobs, then failed: ${captureRes?.error || "could not reach Resume Maker queue API."}`
        );
      }
      added += captureRes.data.added;
      duplicates += captureRes.data.duplicates;

      if (i < newJobs.length - 1) {
        const delay = getRandomDelay(2.0, 3.8);
        await sleep(delay);
      }
    }

    const summary = { added, duplicates, total_submitted: mappedJobs.length };
    const finalMsg = `Done! Added ${summary.added} new jobs to queue (${summary.duplicates} already in queue).`;
    console.log(`[Capture Queue] ${finalMsg}`);

    chrome.runtime.sendMessage({
      type: "UPDATE_CAPTURE_STATE",
      state: {
        running: false,
        statusText: finalMsg,
        progress: null,
        error: null,
        lastResult: summary,
      },
    });

    return { success: true, summary };
  } catch (err) {
    console.error("[Capture Queue Error]", err);
    chrome.runtime.sendMessage({
      type: "UPDATE_CAPTURE_STATE",
      state: {
        running: false,
        statusText: "Capture failed",
        error: err.message,
      },
    });
    return { success: false, error: err.message };
  }
}

// The popup injects this script on every click; register the listener only once per page,
// and ignore clicks while a capture is already running.
if (!window.__hcCaptureListenerRegistered) {
  window.__hcCaptureListenerRegistered = true;
  let captureInFlight = false;
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "START_CAPTURE") {
      if (captureInFlight) {
        sendResponse({ success: false, error: "Capture already running" });
        return false;
      }
      captureInFlight = true;
      executeHiringCafeCapture()
        .then(sendResponse)
        .finally(() => {
          captureInFlight = false;
        });
      return true;
    }
  });
}
