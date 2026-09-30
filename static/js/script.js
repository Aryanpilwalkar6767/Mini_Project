/* =========================================================
   FormaLift — Frontend Logic
   ========================================================= */

const MAX_CHARS = 500;
const HISTORY_KEY = "formalift_history_v1";
const THEME_KEY = "formalift_theme";
const MAX_HISTORY = 30;

// Elements
const inputText = document.getElementById("inputText");
const charCount = document.getElementById("charCount");
const wordCount = document.getElementById("wordCount");
const convertBtn = document.getElementById("convertBtn");
const clearBtn = document.getElementById("clearBtn");
const errorMsg = document.getElementById("errorMsg");
const outputSection = document.getElementById("outputSection");
const originalOut = document.getElementById("originalOut");
const ruleOut = document.getElementById("ruleOut");
const hybridOut = document.getElementById("hybridOut");
const ruleSkeleton = document.getElementById("ruleSkeleton");
const hybridSkeleton = document.getElementById("hybridSkeleton");
const ruleDiff = document.getElementById("ruleDiff");
const hybridDiff = document.getElementById("hybridDiff");
const downloadBtn = document.getElementById("downloadBtn");
const toggleDiffBtn = document.getElementById("toggleDiffBtn");
const themeToggle = document.getElementById("themeToggle");
const historyToggle = document.getElementById("historyToggle");
const historyDrawer = document.getElementById("historyDrawer");
const historyOverlay = document.getElementById("historyOverlay");
const closeHistoryBtn = document.getElementById("closeHistoryBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const historyList = document.getElementById("historyList");
const exampleChips = document.getElementById("exampleChips");

let lastResult = null;
let diffVisible = false;
let isConverting = false;

/* ---------- Theme ---------- */
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const theme = saved || "dark";
  document.documentElement.setAttribute("data-theme", theme);
}
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem(THEME_KEY, next);
}

/* ---------- Counts ---------- */
function updateCounts() {
  const text = inputText.value;
  const chars = text.length;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  charCount.textContent = `${chars} / ${MAX_CHARS}`;
  wordCount.textContent = `${words} word${words === 1 ? "" : "s"}`;
}

/* ---------- UI helpers ---------- */
function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.hidden = false;
}
function hideError() {
  errorMsg.hidden = true;
  errorMsg.textContent = "";
}

function setLoading(loading) {
  isConverting = loading;
  convertBtn.disabled = loading;
  const label = convertBtn.querySelector(".btn-label");
  const spinner = convertBtn.querySelector(".btn-spinner");
  if (loading) {
    label.hidden = true;
    spinner.hidden = false;
    outputSection.hidden = false;
    ruleOut.textContent = "";
    hybridOut.textContent = "";
    originalOut.textContent = inputText.value.trim();
    ruleSkeleton.hidden = false;
    hybridSkeleton.hidden = false;
    ruleDiff.hidden = true;
    hybridDiff.hidden = true;
    diffVisible = false;
    toggleDiffBtn.textContent = "Highlight changes";
  } else {
    label.hidden = false;
    spinner.hidden = true;
    ruleSkeleton.hidden = true;
    hybridSkeleton.hidden = true;
  }
}

/* ---------- Diff (word-level, approximate) ---------- */
function tokenize(text) {
  return text.match(/\S+|\s+/g) || [];
}

function wordDiffHtml(original, rewritten) {
  const a = tokenize(original);
  const b = tokenize(rewritten);
  // Simple LCS-inspired alignment for short texts
  const n = a.length;
  const m = b.length;
  const dp = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      if (a[i - 1].toLowerCase() === b[j - 1].toLowerCase()) dp[i][j] = dp[i - 1][j - 1] + 1;
      else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  const ops = [];
  let i = n, j = m;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1].toLowerCase() === b[j - 1].toLowerCase()) {
      ops.push({ type: "same", value: b[j - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      ops.push({ type: "add", value: b[j - 1] });
      j--;
    } else {
      ops.push({ type: "del", value: a[i - 1] });
      i--;
    }
  }
  ops.reverse();
  return ops
    .map((op) => {
      if (op.type === "same") return escapeHtml(op.value);
      if (op.type === "add") return `<span class="diff-add">${escapeHtml(op.value)}</span>`;
      return `<span class="diff-del">${escapeHtml(op.value)}</span>`;
    })
    .join("");
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderDiffs() {
  if (!lastResult) return;
  ruleDiff.innerHTML = wordDiffHtml(lastResult.original, lastResult.rule_based);
  hybridDiff.innerHTML = wordDiffHtml(lastResult.original, lastResult.hybrid);
}

/* ---------- Convert ---------- */
async function convert() {
  if (isConverting) return;
  hideError();
  const text = inputText.value.trim();
  if (!text) {
    showError("Please enter some informal text to convert.");
    inputText.focus();
    return;
  }

  setLoading(true);

  try {
    const res = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.error || "Conversion failed.");
    }

    lastResult = data;
    originalOut.textContent = data.original;
    ruleOut.textContent = data.rule_based;
    hybridOut.textContent = data.hybrid;
    renderDiffs();
    saveToHistory(data);
    animateOutputs();
  } catch (err) {
    showError(err.message || "Something went wrong. Please try again.");
    outputSection.hidden = true;
  } finally {
    setLoading(false);
  }
}

function animateOutputs() {
  if (typeof gsap === "undefined") return;
  gsap.fromTo(
    "#outputSection .output-card",
    { opacity: 0, y: 18 },
    { opacity: 1, y: 0, duration: 0.45, stagger: 0.08, ease: "power2.out" }
  );
}

/* ---------- History (localStorage) ---------- */
function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  } catch {
    return [];
  }
}

function saveToHistory(result) {
  const history = getHistory();
  history.unshift({
    original: result.original,
    rule_based: result.rule_based,
    hybrid: result.hybrid,
    timestamp: new Date().toISOString(),
  });
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
  renderHistory();
}

function renderHistory() {
  const history = getHistory();
  if (!history.length) {
    historyList.innerHTML =
      '<p class="history-empty">No conversions yet. Your history is stored locally in this browser.</p>';
    return;
  }
  historyList.innerHTML = history
    .map((item, idx) => {
      const time = new Date(item.timestamp).toLocaleString();
      return `
        <article class="history-item" data-index="${idx}" role="button" tabindex="0">
          <div class="history-item-time">${escapeHtml(time)}</div>
          <div class="history-item-orig">${escapeHtml(item.original)}</div>
          <div class="history-item-hybrid">${escapeHtml(item.hybrid)}</div>
        </article>`;
    })
    .join("");
}

function openHistory() {
  renderHistory();
  historyDrawer.classList.add("open");
  historyDrawer.setAttribute("aria-hidden", "false");
  historyOverlay.hidden = false;
}
function closeHistory() {
  historyDrawer.classList.remove("open");
  historyDrawer.setAttribute("aria-hidden", "true");
  historyOverlay.hidden = true;
}

function loadHistoryItem(index) {
  const history = getHistory();
  const item = history[index];
  if (!item) return;
  inputText.value = item.original;
  updateCounts();
  lastResult = {
    original: item.original,
    rule_based: item.rule_based,
    hybrid: item.hybrid,
  };
  originalOut.textContent = item.original;
  ruleOut.textContent = item.rule_based;
  hybridOut.textContent = item.hybrid;
  outputSection.hidden = false;
  renderDiffs();
  closeHistory();
  window.scrollTo({ top: outputSection.offsetTop - 80, behavior: "smooth" });
}

/* ---------- Download ---------- */
function downloadResult() {
  if (!lastResult) return;
  const content =
    `FormaLift Conversion Result\n` +
    `===========================\n\n` +
    `Original:\n${lastResult.original}\n\n` +
    `Rule-Based Output:\n${lastResult.rule_based}\n\n` +
    `Hybrid Output:\n${lastResult.hybrid}\n\n` +
    `Generated: ${new Date().toLocaleString()}\n`;
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "formalift-result.txt";
  a.click();
  URL.revokeObjectURL(url);
}

/* ---------- Copy ---------- */
async function copyText(targetId, btn) {
  const el = document.getElementById(targetId);
  if (!el || !el.textContent) return;
  try {
    await navigator.clipboard.writeText(el.textContent);
    const prev = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => (btn.textContent = prev), 1200);
  } catch {
    showError("Could not copy to clipboard.");
  }
}

/* ---------- Clear ---------- */
function clearAll() {
  inputText.value = "";
  updateCounts();
  hideError();
  outputSection.hidden = true;
  lastResult = null;
  inputText.focus();
}

/* ---------- Entrance animations ---------- */
function runEntranceAnimations() {
  if (typeof gsap === "undefined") return;
  gsap.from(".hero-badge", { opacity: 0, y: 12, duration: 0.5, ease: "power2.out" });
  gsap.from(".hero-title", { opacity: 0, y: 20, duration: 0.6, delay: 0.08, ease: "power2.out" });
  gsap.from(".hero-subtitle", { opacity: 0, y: 16, duration: 0.55, delay: 0.16, ease: "power2.out" });
  gsap.from(".pipeline-step", {
    opacity: 0, y: 10, duration: 0.4, delay: 0.28, stagger: 0.06, ease: "power2.out",
  });
  gsap.from(".converter-card", { opacity: 0, y: 24, duration: 0.55, delay: 0.35, ease: "power2.out" });
}

/* ---------- Events ---------- */
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  updateCounts();
  renderHistory();
  runEntranceAnimations();

  inputText.addEventListener("input", updateCounts);

  inputText.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") convert();
  });

  convertBtn.addEventListener("click", convert);
  clearBtn.addEventListener("click", clearAll);
  themeToggle.addEventListener("click", toggleTheme);
  downloadBtn.addEventListener("click", downloadResult);

  toggleDiffBtn.addEventListener("click", () => {
    if (!lastResult) return;
    diffVisible = !diffVisible;
    ruleDiff.hidden = !diffVisible;
    hybridDiff.hidden = !diffVisible;
    toggleDiffBtn.textContent = diffVisible ? "Hide changes" : "Highlight changes";
  });

  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => copyText(btn.dataset.target, btn));
  });

  exampleChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    inputText.value = chip.dataset.text || "";
    updateCounts();
    hideError();
    inputText.focus();
  });

  historyToggle.addEventListener("click", openHistory);
  closeHistoryBtn.addEventListener("click", closeHistory);
  historyOverlay.addEventListener("click", closeHistory);
  clearHistoryBtn.addEventListener("click", () => {
    localStorage.removeItem(HISTORY_KEY);
    renderHistory();
  });

  historyList.addEventListener("click", (e) => {
    const item = e.target.closest(".history-item");
    if (!item) return;
    loadHistoryItem(Number(item.dataset.index));
  });
});