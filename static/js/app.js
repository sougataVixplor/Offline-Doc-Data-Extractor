/**
 * app.js
 * Frontend interactions, file upload, sample testing, and data visualization.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropzonePrompt = document.getElementById("dropzonePrompt");
  const previewContainer = document.getElementById("previewContainer");
  const imagePreview = document.getElementById("imagePreview");
  const previewFileName = document.getElementById("previewFileName");
  const clearBtn = document.getElementById("clearBtn");
  const extractBtn = document.getElementById("extractBtn");
  const forceTypeSelect = document.getElementById("forceTypeSelect");

  const emptyState = document.getElementById("emptyState");
  const loadingState = document.getElementById("loadingState");
  const resultsContainer = document.getElementById("resultsContainer");
  const resultActions = document.getElementById("resultActions");

  const resDocType = document.getElementById("resDocType");
  const resConfidence = document.getElementById("resConfidence");
  const resLatency = document.getElementById("resLatency");
  const resEngine = document.getElementById("resEngine");
  const fieldsGrid = document.getElementById("fieldsGrid");
  const jsonContent = document.getElementById("jsonContent");
  const ocrContent = document.getElementById("ocrContent");
  const copyJsonBtn = document.getElementById("copyJsonBtn");
  const toast = document.getElementById("toast");

  let currentFile = null;
  let currentSamplePath = null;
  let lastResultData = null;

  // Initialize System Health Status
  fetchHealthStatus();

  // Drag and Drop Events
  ["dragenter", "dragover"].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove("dragover");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleSelectedFile(files[0]);
    }
  });

  browseBtn.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("click", (e) => {
    if (!currentFile && !currentSamplePath && e.target !== clearBtn) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  clearBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUpload();
  });

  function handleSelectedFile(file) {
    currentFile = file;
    currentSamplePath = null;
    clearActiveChips();

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      previewFileName.textContent = file.name;
      dropzonePrompt.style.display = "none";
      previewContainer.style.display = "flex";
      extractBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function resetUpload() {
    currentFile = null;
    currentSamplePath = null;
    fileInput.value = "";
    imagePreview.src = "";
    previewContainer.style.display = "none";
    dropzonePrompt.style.display = "flex";
    extractBtn.disabled = true;
    clearActiveChips();
  }

  // Quick Sample Chips
  const sampleChips = document.querySelectorAll(".chip");
  sampleChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const samplePath = chip.getAttribute("data-sample");
      selectSample(samplePath, chip);
    });
  });

  function clearActiveChips() {
    sampleChips.forEach(c => c.classList.remove("active"));
  }

  function selectSample(sampleRelPath, chipElement) {
    clearActiveChips();
    chipElement.classList.add("active");

    currentSamplePath = sampleRelPath;
    currentFile = null;

    // Load preview from server sample endpoint
    const sampleUrl = `/api/sample/${encodeURIComponent(sampleRelPath)}`;
    imagePreview.src = sampleUrl;
    previewFileName.textContent = sampleRelPath.split("/").pop();
    dropzonePrompt.style.display = "none";
    previewContainer.style.display = "flex";
    extractBtn.disabled = false;

    // Trigger extraction automatically for instant showcase
    executeExtraction();
  }

  // Extract Button Click
  extractBtn.addEventListener("click", () => {
    executeExtraction();
  });

  async function executeExtraction() {
    if (!currentFile && !currentSamplePath) return;

    // UI State: Loading
    emptyState.style.display = "none";
    resultsContainer.style.display = "none";
    resultActions.style.display = "none";
    loadingState.style.display = "flex";
    extractBtn.disabled = true;

    const forceType = forceTypeSelect.value;
    const formData = new FormData();

    if (forceType) {
      formData.append("force_type", forceType);
    }

    let endpoint = "/api/extract";

    if (currentSamplePath) {
      formData.append("sample_path", currentSamplePath);
    } else if (currentFile) {
      formData.append("file", currentFile);
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      lastResultData = data;
      renderResults(data);
    } catch (err) {
      console.error(err);
      alert("Error processing KYC document: " + err.message);
    } finally {
      loadingState.style.display = "none";
      extractBtn.disabled = false;
    }
  }

  function renderResults(data) {
    if (data.status === "error") {
      alert("Error: " + (data.message || "Unknown extraction error"));
      emptyState.style.display = "flex";
      return;
    }

    // Document header info
    const docType = data.document_type || "UNKNOWN";
    resDocType.textContent = docType;
    resConfidence.textContent = Math.round((data.classification_confidence || 0) * 100) + "% Conf";
    resLatency.textContent = (data.processing_time_ms || 0) + " ms";
    resEngine.textContent = data.ocr_engine || "RapidOCR";

    // Set doc type color theme
    setDocTypeStyle(docType);

    // Populate Fields Grid
    fieldsGrid.innerHTML = "";
    const extracted = data.extracted_data || {};

    const primaryNumberKeys = ["pan_number", "aadhaar_number", "dl_number", "passport_number", "voter_id"];

    for (const [key, val] of Object.entries(extracted)) {
      if (key === "document_type" || key === "mrz") continue;

      const card = document.createElement("div");
      card.className = "field-card";

      const isPrimary = primaryNumberKeys.includes(key);
      const displayVal = val !== null && val !== undefined ? (Array.isArray(val) ? val.join(", ") : String(val)) : "Not Detected";
      const isNull = val === null || val === undefined;

      const friendlyKey = key.replace(/_/g, " ");

      card.innerHTML = `
        <div class="field-card-main">
          <span class="field-key">${friendlyKey}</span>
          <span class="field-value ${isPrimary ? 'highlight' : ''} ${isNull ? 'null-val' : ''}">${displayVal}</span>
        </div>
        ${!isNull ? `
          <button class="btn-copy-field" title="Copy field value" data-copy="${escapeHtml(displayVal)}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        ` : ''}
      `;
      fieldsGrid.appendChild(card);
    }

    // If MRZ exists for passport, display it
    if (extracted.mrz && Array.isArray(extracted.mrz)) {
      const mrzCard = document.createElement("div");
      mrzCard.className = "field-card";
      mrzCard.style.gridColumn = "1 / -1";
      mrzCard.innerHTML = `
        <div class="field-card-main">
          <span class="field-key">Machine Readable Zone (MRZ)</span>
          <span class="field-value highlight" style="font-size: 0.85rem;">${extracted.mrz.join("<br>")}</span>
        </div>
      `;
      fieldsGrid.appendChild(mrzCard);
    }

    // Add copy event listener to field copy buttons
    document.querySelectorAll(".btn-copy-field").forEach(btn => {
      btn.addEventListener("click", () => {
        const text = btn.getAttribute("data-copy");
        copyToClipboard(text);
      });
    });

    // Populate JSON Viewer
    jsonContent.textContent = JSON.stringify(data, null, 2);

    // Populate OCR Content
    ocrContent.textContent = data.raw_text || "No OCR lines extracted.";

    // Show Results
    resultsContainer.style.display = "flex";
    resultActions.style.display = "flex";
  }

  function setDocTypeStyle(docType) {
    const banner = document.getElementById("classificationBanner");
    const colors = {
      "PAN CARD": "linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(99, 102, 241, 0.2) 100%)",
      "AADHAR CARD": "linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.2) 100%)",
      "DRIVING LICENCE": "linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.2) 100%)",
      "PASSPORT": "linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)",
      "VOTAR CARD": "linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(219, 39, 119, 0.2) 100%)"
    };
    banner.style.background = colors[docType] || colors["PAN CARD"];
  }

  // Tab Switching
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetTab = btn.getAttribute("data-tab");
      document.getElementById(targetTab).classList.add("active");
    });
  });

  // Copy JSON button
  copyJsonBtn.addEventListener("click", () => {
    if (lastResultData) {
      copyToClipboard(JSON.stringify(lastResultData, null, 2));
    }
  });

  // Copy to Clipboard helper
  function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      showToast();
    }).catch(() => {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      showToast();
    });
  }

  function showToast() {
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2000);
  }

  function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // System Health
  async function fetchHealthStatus() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (data.status === "ok") {
        document.getElementById("engineNameText").textContent = (data.ocr_engine || "RapidOCR") + " (Offline CPU)";
        if (data.memory_mb) {
          document.getElementById("serverMemText").textContent = `RAM: ${data.memory_mb} MB`;
        }
      }
    } catch (e) {
      console.warn("Could not fetch health status:", e);
    }
  }
});
