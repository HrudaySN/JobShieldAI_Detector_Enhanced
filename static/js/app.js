(function () {

  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) sidebarToggle.addEventListener("click", () => document.body.classList.toggle("sidebar-open"));

  /* ---------- Editorial heading reveal ---------- */
  document.querySelectorAll("[data-reveal-text]").forEach((heading) => {
    const text = heading.getAttribute("data-reveal-text");
    if (!text) return;
    heading.setAttribute("aria-label", text);
    heading.innerHTML = "";
    [...text].forEach((character, index) => {
      const letter = document.createElement("span");
      letter.className = "letter";
      letter.setAttribute("aria-hidden", "true");
      letter.textContent = character === " " ? "\u00a0" : character;
      letter.style.animationDelay = `${120 + index * 55}ms`;
      if (index >= text.length - 2) letter.style.color = "var(--teal-600)";
      heading.appendChild(letter);
    });
  });

  /* ---------- Generic toast ---------- */
  window.showToast = function (message) {
    let toast = document.querySelector(".toast-fixed");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast-fixed";
      document.body.appendChild(toast);
    }
    toast.innerHTML = `<div class="card-surface px-3 py-2" style="min-width:240px;">
        <div class="d-flex align-items-center gap-2">
          <i class="bi bi-check-circle-fill" style="color:var(--teal-600)"></i>
          <span style="font-size:13.5px;">${message}</span>
        </div></div>`;
    toast.style.display = "block";
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => (toast.style.display = "none"), 3200);
  };

  /* ---------- Tab pill groups (Paste / Upload etc.) ---------- */
  document.querySelectorAll("[data-tab-group]").forEach((group) => {
    const groupName = group.getAttribute("data-tab-group");
    const pills = group.querySelectorAll(".tab-pill");
    pills.forEach((pill) => {
      pill.addEventListener("click", () => {
        pills.forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        const target = pill.getAttribute("data-tab-target");
        document.querySelectorAll(`[data-tab-panel="${groupName}"]`).forEach((panel) => {
          panel.style.display = panel.getAttribute("data-panel-name") === target ? "block" : "none";
        });
      });
    });
  });

  /* ---------- Jump to another tab-pill from a button elsewhere on the page ---------- */
  document.querySelectorAll("[data-jump-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-jump-tab");
      const pill = document.querySelector(`.tab-pill[data-tab-target="${target}"]`);
      if (pill) {
        pill.click();
        pill.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  /* ---------- Drag & drop / click-to-browse upload zones ---------- */
  document.querySelectorAll(".upload-zone").forEach((zone) => {
    const inputId = zone.getAttribute("data-input");
    const input = document.getElementById(inputId);
    if (!input) return;

    zone.addEventListener("click", () => input.click());
    ["dragenter", "dragover"].forEach((evt) =>
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
      })
    );
    zone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        handleFilePreview(input);
      }
    });
    input.addEventListener("change", () => handleFilePreview(input));
  });

  function handleFilePreview(input) {
    const previewId = input.getAttribute("data-preview");
    const zoneId = input.getAttribute("data-zone");
    const nameId = input.getAttribute("data-filename");
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];

    if (nameId) {
      const el = document.getElementById(nameId);
      if (el) el.textContent = file.name;
    }

    if (previewId) {
      const previewWrap = document.getElementById(previewId);
      if (previewWrap && file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          previewWrap.innerHTML = `<img src="${e.target.result}" class="upload-preview" alt="Preview of ${file.name}">`;
          previewWrap.style.display = "block";
        };
        reader.readAsDataURL(file);
      } else if (previewWrap) {
        previewWrap.innerHTML = `<div class="d-flex align-items-center gap-2"><i class="bi bi-file-earmark-text fs-3" style="color:var(--teal-600)"></i><span>${file.name}</span></div>`;
        previewWrap.style.display = "block";
      }
    }

    if (zoneId) {
      const zone = document.getElementById(zoneId);
      if (zone) zone.style.display = "none";
    }

    const changeBtnId = input.getAttribute("data-change-btn");
    if (changeBtnId) {
      const btn = document.getElementById(changeBtnId);
      if (btn) btn.style.display = "inline-flex";
    }
  }

  document.querySelectorAll("[data-remove-upload]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const inputId = btn.getAttribute("data-remove-upload");
      const input = document.getElementById(inputId);
      if (!input) return;
      input.value = "";
      const previewId = input.getAttribute("data-preview");
      const zoneId = input.getAttribute("data-zone");
      if (previewId) {
        const p = document.getElementById(previewId);
        if (p) { p.innerHTML = ""; p.style.display = "none"; }
      }
      if (zoneId) {
        const z = document.getElementById(zoneId);
        if (z) z.style.display = "block";
      }
      btn.style.display = "none";
    });
  });

  /* ---------- Textarea character counters ---------- */
  document.querySelectorAll("textarea[data-max]").forEach((ta) => {
    const max = parseInt(ta.getAttribute("data-max"), 10);
    const counterId = ta.getAttribute("data-counter");
    const counter = counterId ? document.getElementById(counterId) : null;
    ta.addEventListener("input", () => {
      const len = Math.min(ta.value.length, max);
      if (counter) counter.textContent = `${len} / ${max}`;
    });
  });

  /* ---------- Detector: explainable job safety scan ---------- */
  const analyzeBtn = document.getElementById("analyzeBtn");
  if (analyzeBtn) analyzeBtn.addEventListener("click", runJobAnalysis);

  let latestAnalysis = null;
  let scanTimer = null;

  document.querySelectorAll(".segmented").forEach((group) => {
    group.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-value]");
      if (!button) return;
      group.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
      button.classList.add("active");
    });
  });

  async function runJobAnalysis() {
    const description = document.getElementById("jobDescription");
    const fileInput = document.getElementById("jobFileInput");
    const button = analyzeBtn;
    const resultEmpty = document.getElementById("resultEmpty");
    const resultCard = document.getElementById("resultCard");
    const progressCard = document.getElementById("scanProgress");
    const original = button.innerHTML;
    let text = description?.value.trim() || "";

    // If a file is selected, extract it first. This keeps Paste and Upload on the same detector path.
    if (!text && fileInput?.files?.[0]) {
      button.disabled = true;
      button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Reading file…';
      try {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        const extractResponse = await fetch("/api/extract-job-file", { method: "POST", body: formData });
        const extracted = await extractResponse.json();
        if (!extractResponse.ok) throw new Error(extracted.error || "Could not read the selected file.");
        text = (extracted.text || "").trim();
        if (description) {
          description.value = text;
          description.dispatchEvent(new Event("input", { bubbles: true }));
        }
      } catch (error) {
        button.disabled = false;
        button.innerHTML = original;
        showToast(error.message);
        return;
      }
    }

    if (!text) {
      showToast("Paste a job description or select a job file first.");
      return;
    }
    if (text.split(/\s+/).filter(Boolean).length < 4) {
      showToast("Please provide a little more job information before scanning.");
      return;
    }

    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Scanning…';
    if (resultCard) resultCard.style.display = "none";
    if (resultEmpty) resultEmpty.style.display = "block";
    startScanProgress(progressCard);

    const payload = {
      text,
      job_url: document.getElementById("jobUrl")?.value.trim() || "",
      recruiter_email: document.getElementById("recruiterEmail")?.value.trim() || "",
      company_website: document.getElementById("companyWebsite")?.value.trim() || "",
      questions: collectQuestions()
    };

    try {
      const response = await fetch("/api/analyze-job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Analysis could not be completed.");
      finishScanProgress();
      latestAnalysis = { payload, result };
      renderJobAnalysis(result);
      if (resultEmpty) resultEmpty.style.display = "none";
      if (resultCard) {
        resultCard.style.display = "block";
        resultCard.classList.remove("result-revealed");
        requestAnimationFrame(() => resultCard.classList.add("result-revealed"));
        resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      showToast("Scan complete — review the reasons before applying.");
    } catch (error) {
      stopScanProgress();
      showToast(error.message);
    } finally {
      button.disabled = false;
      button.innerHTML = original;
    }
  }

  function collectQuestions() {
    const questions = {};
    document.querySelectorAll(".segmented[data-question]").forEach((group) => {
      questions[group.dataset.question] = group.querySelector("button.active")?.dataset.value || "not_sure";
    });
    return questions;
  }

  function startScanProgress(card) {
    if (!card) return;
    card.style.display = "block";
    const labels = ["Reading job content…", "Checking source signals…", "Scoring risk…", "Preparing guidance…"];
    let step = 1;
    const update = () => {
      const percent = Math.min(90, step * 24);
      document.getElementById("scanProgressLabel").textContent = labels[Math.min(step - 1, 3)];
      document.getElementById("scanPercent").textContent = `${percent}%`;
      document.getElementById("scanProgressBar").style.width = `${percent}%`;
      document.querySelectorAll(".scan-step").forEach((el, i) => {
        el.classList.toggle("active", i + 1 === step);
        el.classList.toggle("done", i + 1 < step);
      });
    };
    update();
    clearInterval(scanTimer);
    scanTimer = setInterval(() => { if (step < 4) { step += 1; update(); } }, 650);
  }

  function finishScanProgress() {
    clearInterval(scanTimer);
    const bar = document.getElementById("scanProgressBar");
    const percent = document.getElementById("scanPercent");
    const label = document.getElementById("scanProgressLabel");
    if (bar) bar.style.width = "100%";
    if (percent) percent.textContent = "100%";
    if (label) label.textContent = "Scan complete";
    document.querySelectorAll(".scan-step").forEach((el) => { el.classList.remove("active"); el.classList.add("done"); });
    setTimeout(() => { const card = document.getElementById("scanProgress"); if (card) card.style.display = "none"; }, 450);
  }

  function stopScanProgress() {
    clearInterval(scanTimer);
    const card = document.getElementById("scanProgress");
    if (card) card.style.display = "none";
  }

  function renderJobAnalysis(result) {
    const badge = document.getElementById("verdictBadge");
    const level = document.getElementById("riskLevel");
    const verdict = document.getElementById("verdictText");
    const riskScore = document.getElementById("riskScore");
    const riskScoreLarge = document.getElementById("riskScoreLarge");
    const progress = document.getElementById("riskProgress");
    const modelInfo = document.getElementById("modelInfo");
    const flags = document.getElementById("riskFlags");
    const positives = document.getElementById("positiveSignals");
    const sources = document.getElementById("sourceChecks");
    const actions = document.getElementById("nextActions");
    const gauge = document.getElementById("riskGauge");
    const tone = result.tone || "review";
    if (badge) {
      badge.className = `verdict-badge ${tone}`;
      badge.querySelector("i").className = tone === "genuine" ? "bi bi-check-circle-fill" : tone === "review" ? "bi bi-exclamation-circle-fill" : "bi bi-exclamation-triangle-fill";
    }
    if (level) level.textContent = result.risk_level || "Medium";
    if (verdict) verdict.textContent = result.verdict;
    if (riskScore) riskScore.textContent = `${result.risk_score}%`;
    if (riskScoreLarge) riskScoreLarge.textContent = result.risk_score;
    if (progress) { progress.className = `progress-fill ${tone === "genuine" ? "" : "risk"}`; progress.style.width = "0%"; requestAnimationFrame(() => progress.style.width = `${result.risk_score}%`); }
    if (modelInfo) modelInfo.textContent = `${result.model.name} · ${result.model.training_examples} labelled examples`;
    if (gauge) gauge.style.background = tone === "fake" ? "linear-gradient(145deg,#d95a5a,#9f3030)" : tone === "review" ? "linear-gradient(145deg,#e2a13a,#b7791f)" : "linear-gradient(145deg,var(--teal-500),var(--teal-800))";
    if (flags) flags.innerHTML = (result.evidence || []).filter(x => x.type === "red_flag" || x.type === "screening").map(x => `<div class="evidence-row"><span class="evidence-phrase">“${escapeHtml(x.phrase)}”</span><span>${escapeHtml(x.message)}</span></div>`).join("") || '<span class="reason-chip neutral"><i class="bi bi-info-circle"></i>No strong suspicious phrase was matched.</span>';
    if (positives) positives.innerHTML = (result.positive_signals || []).map(x => `<span class="reason-chip ok"><i class="bi bi-check-circle"></i>${escapeHtml(x)}</span>`).join("");
    if (sources) sources.innerHTML = (result.source_checks || []).map(x => `<div class="source-check ${x.status}"><i class="bi ${x.status === "ok" ? "bi-check-circle" : x.status === "warning" ? "bi-exclamation-triangle" : "bi-info-circle"}"></i>${escapeHtml(x.message)}</div>`).join("");
    if (actions) actions.innerHTML = (result.actions || []).map(x => `<div class="action-row"><i class="bi bi-arrow-right-circle-fill"></i><span>${escapeHtml(x)}</span></div>`).join("");
  }

  const saveReportBtn = document.getElementById("saveReportBtn");
  if (saveReportBtn) saveReportBtn.addEventListener("click", async () => {
    if (!latestAnalysis) return showToast("Run a scan before saving a report.");
    saveReportBtn.disabled = true;
    try {
      const response = await fetch("/api/save-analysis", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(latestAnalysis.payload && { ...latestAnalysis.payload, result: latestAnalysis.result }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not save report.");
      saveReportBtn.innerHTML = '<i class="bi bi-check-circle"></i> Saved to History';
      showToast("Report saved to your History.");
    } catch (error) { showToast(error.message); } finally { saveReportBtn.disabled = false; }
  });

  const downloadReportBtn = document.getElementById("downloadReportBtn");
  if (downloadReportBtn) downloadReportBtn.addEventListener("click", () => {
    if (!latestAnalysis) return showToast("Run a scan before downloading the report.");
    const { payload, result } = latestAnalysis;
    const evidence = (result.evidence || []).map(x => `- ${x.phrase}: ${x.message}`).join("\n") || "- No strong suspicious phrase matched.";
    const sources = (result.source_checks || []).map(x => `- ${x.message}`).join("\n") || "- No source details supplied.";
    const actions = (result.actions || []).map(x => `- ${x}`).join("\n");
    const report = `JOBSHIELD AI — JOB SAFETY REPORT\n================================\nGenerated: ${new Date().toLocaleString()}\n\nRISK LEVEL: ${result.risk_level}\nRISK SCORE: ${result.risk_score}%\nVERDICT: ${result.verdict}\n\nSOURCE DETAILS\n--------------\nJob URL: ${payload.job_url || "Not supplied"}\nRecruiter email: ${payload.recruiter_email || "Not supplied"}\nCompany website: ${payload.company_website || "Not supplied"}\n\nWHY THIS RESULT\n---------------\n${evidence}\n\nSOURCE CHECKS\n-------------\n${sources}\n\nWHAT TO DO NEXT\n---------------\n${actions}\n\nJOB DESCRIPTION\n---------------\n${payload.text}\n`;
    const blob = new Blob([report], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `jobshield-report-${Date.now()}.txt`; a.click();
    URL.revokeObjectURL(url);
    showToast("Report downloaded.");
  });

  function escapeHtml(value) {
    const node = document.createElement("div");
    node.textContent = value == null ? "" : String(value);
    return node.innerHTML;
  }

  /* ---------- Detector FAQ accordion ---------- */
  document.querySelectorAll(".faq-item").forEach((item) => {
    item.addEventListener("click", () => {
      const answer = item.nextElementSibling;
      if (!answer || !answer.classList.contains("faq-answer")) return;
      const wasOpen = answer.classList.contains("open");
      document.querySelectorAll(".faq-item.open").forEach((el) => el.classList.remove("open"));
      document.querySelectorAll(".faq-answer.open").forEach((el) => el.classList.remove("open"));
      if (!wasOpen) { item.classList.add("open"); answer.classList.add("open"); }
    });
  });

  /* ---------- Resume screening simulation ---------- */
  const screenBtn = document.getElementById("screenResumeBtn");
  if (screenBtn) {
    screenBtn.addEventListener("click", function () {
      const resultBlock = document.getElementById("resumeResults");
      screenBtn.disabled = true;
      screenBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Screening…';
      setTimeout(() => {
        screenBtn.disabled = false;
        screenBtn.innerHTML = '<i class="bi bi-stars"></i> Screen Resume';
        if (resultBlock) {
          resultBlock.style.display = "block";
          const fill = resultBlock.querySelector(".progress-fill");
          if (fill) setTimeout(() => (fill.style.width = fill.getAttribute("data-value") + "%"), 100);
          resultBlock.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        showToast("Resume screened — sample recommendations shown below.");
      }, 1200);
    });
  }

  /* ---------- Contact form (front-end only) ---------- */
  const contactForm = document.getElementById("contactForm");
  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault();
      showToast("Message sent! Our team will get back to you soon.");
      contactForm.reset();
    });
  }

  /* ---------- History filter (front-end only) ---------- */
  const historyTabs = document.querySelectorAll("[data-history-tab]");
  historyTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      historyTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll("[data-history-panel]").forEach((panel) => {
        panel.style.display =
          panel.getAttribute("data-history-panel") === tab.getAttribute("data-history-tab")
            ? "block"
            : "none";
      });
    });
  });
})();
