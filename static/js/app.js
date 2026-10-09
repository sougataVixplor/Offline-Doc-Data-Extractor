/**
 * app.js
 * Frontend interactions for Offline Document Data Extractor
 * Supports:
 * 1. Normal Text OCR (Default - Pure Text Extraction without KYC classification or masking)
 * 2. KYC Document Mode (Classification, Field Extraction & 80% Confidential Masking)
 * Includes clipboard image paste (Ctrl+V), live text search, line numbers gutter,
 * export to .TXT & .JSON, and real-time offline metrics.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Mode State: 'normal' (Default) or 'kyc'
  let currentMode = "normal";

  // Elements: Header & Mode Switcher
  const modeNormalBtn = document.getElementById("modeNormalBtn");
  const modeKycBtn = document.getElementById("modeKycBtn");
  const appTitle = document.getElementById("appTitle");
  const appSubtitle = document.getElementById("appSubtitle");
  const modeBadgeText = document.getElementById("modeBadgeText");
  const panelModeBadge = document.getElementById("panelModeBadge");
  const panelHeaderDesc = document.getElementById("panelHeaderDesc");
  const resultsPanelTitle = document.getElementById("resultsPanelTitle");
  const resultsPanelDesc = document.getElementById("resultsPanelDesc");

  // Elements: Upload & Control
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropzonePrompt = document.getElementById("dropzonePrompt");
  const previewContainer = document.getElementById("previewContainer");
  const imagePreview = document.getElementById("imagePreview");
  const previewFileName = document.getElementById("previewFileName");
  const clearBtn = document.getElementById("clearBtn");
  const extractBtn = document.getElementById("extractBtn");
  const extractBtnText = document.getElementById("extractBtnText");
  const extractKycBtn = document.getElementById("extractKycBtn");
  const forceTypeSelect = document.getElementById("forceTypeSelect");
  const securityBadge = document.getElementById("securityBadge");

  // Option Bars & Info Cards
  const normalOptionsBar = document.getElementById("normalOptionsBar");
  const kycOptionsBar = document.getElementById("kycOptionsBar");
  const normalInfoCard = document.getElementById("normalInfoCard");
  const kycSecurityCard = document.getElementById("kycSecurityCard");
  const kycDocTypesCard = document.getElementById("kycDocTypesCard");

  // Elements: Results & States
  const emptyState = document.getElementById("emptyState");
  const emptyStateTitle = document.getElementById("emptyStateTitle");
  const emptyStateDesc = document.getElementById("emptyStateDesc");
  const loadingState = document.getElementById("loadingState");
  const loadingText = document.getElementById("loadingText");
  const loadingDesc = document.getElementById("loadingDesc");
  const resultsContainer = document.getElementById("resultsContainer");
  const resultActions = document.getElementById("resultActions");

  // Normal Mode Result Elements
  const textStatsBanner = document.getElementById("textStatsBanner");
  const statLinesCount = document.getElementById("statLinesCount");
  const statWordsCount = document.getElementById("statWordsCount");
  const statCharsCount = document.getElementById("statCharsCount");
  const statAvgConfidence = document.getElementById("statAvgConfidence");
  const statLatency = document.getElementById("statLatency");
  const statEngine = document.getElementById("statEngine");

  const textToolbar = document.getElementById("textToolbar");
  const textSearchInput = document.getElementById("textSearchInput");
  const clearSearchBtn = document.getElementById("clearSearchBtn");
  const searchMatchBadge = document.getElementById("searchMatchBadge");
  const toggleLineNumbersBtn = document.getElementById("toggleLineNumbersBtn");
  const toggleWordWrapBtn = document.getElementById("toggleWordWrapBtn");

  const normalTabsHeader = document.getElementById("normalTabsHeader");
  const kycTabsHeader = document.getElementById("kycTabsHeader");

  const tabNormalText = document.getElementById("tabNormalText");
  const tabLineByLine = document.getElementById("tabLineByLine");
  const tabBoundingBoxes = document.getElementById("tabBoundingBoxes");
  const tabJson = document.getElementById("tabJson");
  const tabFields = document.getElementById("tabFields");
  const tabCoords = document.getElementById("tabCoords");
  const tabOcr = document.getElementById("tabOcr");

  const lineNumbersGutter = document.getElementById("lineNumbersGutter");
  const extractedTextBody = document.getElementById("extractedTextBody");
  const linesList = document.getElementById("linesList");
  const boxesGrid = document.getElementById("boxesGrid");

  // KYC Mode Result Elements
  const classificationBanner = document.getElementById("classificationBanner");
  const resDocType = document.getElementById("resDocType");
  const resConfidence = document.getElementById("resConfidence");
  const resLatency = document.getElementById("resLatency");
  const resEngine = document.getElementById("resEngine");
  const fieldsGrid = document.getElementById("fieldsGrid");
  const coordsList = document.getElementById("coordsList");
  const ocrContent = document.getElementById("ocrContent");

  // Actions & Buttons
  const copyAllTextBtn = document.getElementById("copyAllTextBtn");
  const downloadTxtBtn = document.getElementById("downloadTxtBtn");
  const downloadJsonBtn = document.getElementById("downloadJsonBtn");
  const jsonContent = document.getElementById("jsonContent");
  const toast = document.getElementById("toast");

  // State Variables
  let currentFile = null;
  let currentSamplePath = null;
  let lastResultData = null;
  let rawExtractedText = "";
  let showLineNumbers = true;
  let enableWordWrap = true;

  // Initialize System Health Status
  fetchHealthStatus();

  // Mode Switcher Listeners
  modeNormalBtn.addEventListener("click", () => switchMode("normal"));
  modeKycBtn.addEventListener("click", () => switchMode("kyc"));

  function switchMode(newMode) {
    if (currentMode === newMode) return;
    currentMode = newMode;

    if (currentMode === "normal") {
      // Buttons
      modeNormalBtn.classList.add("active");
      modeKycBtn.classList.remove("active");

      // Header Branding
      appTitle.textContent = "Document Text Extractor";
      appSubtitle.textContent = "Offline Neural OCR • Pure Text Extraction (No KYC / No Classification) • 2-4GB RAM Optimized";
      modeBadgeText.textContent = "Mode: Normal Text OCR";
      panelModeBadge.textContent = "Pure OCR";
      panelHeaderDesc.textContent = "Works with any photo, scan, document, receipt, or pasted screenshot";
      resultsPanelTitle.textContent = "2. Extracted Text Results";
      resultsPanelDesc.textContent = "Raw extracted text, line details, and coordinates";

      // Options & Info Cards
      normalOptionsBar.style.display = "flex";
      kycOptionsBar.style.display = "none";
      normalInfoCard.style.display = "flex";
      kycSecurityCard.style.display = "none";
      kycDocTypesCard.style.display = "none";

      // Result Headers & Tabs
      normalTabsHeader.style.display = "flex";
      kycTabsHeader.style.display = "none";
      textStatsBanner.style.display = "grid";
      textToolbar.style.display = "flex";
      classificationBanner.style.display = "none";

      // Empty state copy
      emptyStateTitle.textContent = "No Document Extracted Yet";
      emptyStateDesc.textContent = "Upload or paste an image or choose one of the quick test samples on the left to extract text offline.";

      // Sample chip labels
      updateSampleChipLabels("normal");

      // Actions buttons
      copyAllTextBtn.style.display = "inline-flex";
      downloadTxtBtn.style.display = "inline-flex";

      // Activate default normal tab
      activateTab("tabNormalText");
    } else {
      // Buttons
      modeNormalBtn.classList.remove("active");
      modeKycBtn.classList.add("active");

      // Header Branding
      appTitle.textContent = "KYC Offline Extractor";
      appSubtitle.textContent = "Classification & Extraction • 80% Confidential Masking • 2-4GB Server Optimized";
      modeBadgeText.textContent = "Mode: KYC Classifier & Masker";
      panelModeBadge.textContent = "KYC Mode";
      panelHeaderDesc.textContent = "Classifies PAN, Aadhaar, DL, Passport & Voter cards with 80% masking";
      resultsPanelTitle.textContent = "2. Extracted KYC Results";
      resultsPanelDesc.textContent = "Classified metadata, confidential coordinates & 80% black box preview";

      // Options & Info Cards
      normalOptionsBar.style.display = "none";
      kycOptionsBar.style.display = "flex";
      normalInfoCard.style.display = "none";
      kycSecurityCard.style.display = "flex";
      kycDocTypesCard.style.display = "flex";

      // Result Headers & Tabs
      normalTabsHeader.style.display = "none";
      kycTabsHeader.style.display = "flex";
      textStatsBanner.style.display = "none";
      textToolbar.style.display = "none";
      classificationBanner.style.display = "flex";

      // Empty state copy
      emptyStateTitle.textContent = "No KYC Document Extracted Yet";
      emptyStateDesc.textContent = "Upload a KYC photo or click one of the quick test samples on the left to inspect extraction and 80% masking results.";

      // Sample chip labels
      updateSampleChipLabels("kyc");

      // Activate default KYC tab
      activateTab("tabFields");
    }

    // Reset results view when switching mode to avoid inconsistent views
    emptyState.style.display = "flex";
    resultsContainer.style.display = "none";
    resultActions.style.display = "none";
  }

  function updateSampleChipLabels(mode) {
    const chipLabels = {
      "PAN CARD SAMPLE/SAMPLE-3.jpg": mode === "normal" ? "Sample Document 1" : "PAN Card",
      "AADHAR CARD SAMPLE/SAMPLE-2.webp": mode === "normal" ? "Sample Document 2" : "Aadhaar Card",
      "DRIVING LICENCE SAMPLE/SAMPLE-1.webp": mode === "normal" ? "Sample Document 3" : "Driving Licence",
      "PASSPORT SAMPLE/SAMPLE-1.webp": mode === "normal" ? "Sample Document 4" : "Passport",
      "VOTAR CARD SAMPLE/SAMPLE-1.webp": mode === "normal" ? "Sample Document 5" : "Voter Card"
    };

    document.querySelectorAll(".chip").forEach(chip => {
      const samplePath = chip.getAttribute("data-sample");
      const dot = chip.querySelector(".chip-dot");
      const dotClass = dot ? dot.className : "";
      const dotHtml = dot ? `<span class="${dotClass}"></span> ` : "";
      if (chipLabels[samplePath]) {
        chip.innerHTML = dotHtml + chipLabels[samplePath];
      }
    });
  }

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

  // Global Clipboard Paste Support (Ctrl+V)
  window.addEventListener("paste", (e) => {
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (const item of items) {
      if (item.type.indexOf("image") === 0) {
        const file = item.getAsFile();
        if (file) {
          handleSelectedFile(file);
          showToast("Image pasted from clipboard!");
          break;
        }
      }
    }
  });

  function handleSelectedFile(file) {
    currentFile = file;
    currentSamplePath = null;
    clearActiveChips();
    if (securityBadge) securityBadge.style.display = "none";

    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      previewFileName.textContent = file.name || "Pasted_Screenshot.png";
      dropzonePrompt.style.display = "none";
      previewContainer.style.display = "flex";
      extractBtn.disabled = false;
      extractKycBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function resetUpload() {
    currentFile = null;
    currentSamplePath = null;
    fileInput.value = "";
    imagePreview.src = "";
    if (securityBadge) securityBadge.style.display = "none";
    previewContainer.style.display = "none";
    dropzonePrompt.style.display = "flex";
    extractBtn.disabled = true;
    extractKycBtn.disabled = true;
    clearActiveChips();
    emptyState.style.display = "flex";
    resultsContainer.style.display = "none";
    resultActions.style.display = "none";
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
    if (securityBadge) securityBadge.style.display = "none";

    currentSamplePath = sampleRelPath;
    currentFile = null;

    const sampleUrl = `/api/sample/${encodeURIComponent(sampleRelPath)}`;
    imagePreview.src = sampleUrl;
    previewFileName.textContent = sampleRelPath.split("/").pop();
    dropzonePrompt.style.display = "none";
    previewContainer.style.display = "flex";
    extractBtn.disabled = false;
    extractKycBtn.disabled = false;

    // Trigger extraction automatically
    executeExtraction();
  }

  // Extract Buttons
  extractBtn.addEventListener("click", () => executeExtraction());
  extractKycBtn.addEventListener("click", () => executeExtraction());

  async function executeExtraction() {
    if (!currentFile && !currentSamplePath) return;

    emptyState.style.display = "none";
    resultsContainer.style.display = "none";
    resultActions.style.display = "none";
    loadingState.style.display = "flex";
    extractBtn.disabled = true;
    extractKycBtn.disabled = true;

    if (currentMode === "normal") {
      loadingText.textContent = "Extracting Text Offline...";
      loadingDesc.textContent = "Pre-processing image • Running ONNX OCR • Detecting text lines & bounding boxes";
      await executeNormalExtraction();
    } else {
      loadingText.textContent = "Processing Document Offline...";
      loadingDesc.textContent = "Pre-processing • Classifying KYC type • Locating coordinates • Applying 80% mask";
      await executeKycExtraction();
    }

    loadingState.style.display = "none";
    extractBtn.disabled = false;
    extractKycBtn.disabled = false;
  }

  // 1. Normal Mode Text Extraction API Call
  async function executeNormalExtraction() {
    const formData = new FormData();
    if (currentSamplePath) {
      formData.append("sample_path", currentSamplePath);
    } else if (currentFile) {
      formData.append("file", currentFile);
    }

    try {
      const response = await fetch("/api/extract-text", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      lastResultData = data;
      renderNormalResults(data);
    } catch (err) {
      console.error(err);
      alert("Error extracting text: " + err.message);
      emptyState.style.display = "flex";
    }
  }

  // 2. KYC Mode Extraction API Call
  async function executeKycExtraction() {
    const formData = new FormData();
    const forceType = forceTypeSelect.value;
    if (forceType) {
      formData.append("force_type", forceType);
    }

    if (currentSamplePath) {
      formData.append("sample_path", currentSamplePath);
    } else if (currentFile) {
      formData.append("file", currentFile);
    }

    try {
      const response = await fetch("/api/extract", {
        method: "POST",
        body: formData
      });

      const data = await response.json();
      lastResultData = data;
      renderKycResults(data);
    } catch (err) {
      console.error(err);
      alert("Error processing KYC document: " + err.message);
      emptyState.style.display = "flex";
    }
  }

  // Render Normal Text Extraction Results
  function renderNormalResults(data) {
    if (data.status === "error") {
      alert("Extraction Error: " + (data.message || "Failed to extract text"));
      emptyState.style.display = "flex";
      return;
    }

    rawExtractedText = data.text || data.raw_text || "";
    const lines = data.lines || [];
    const details = data.details || [];
    const words = data.words_count !== undefined ? data.words_count : rawExtractedText.split(/\s+/).filter(Boolean).length;
    const chars = data.characters_count !== undefined ? data.characters_count : rawExtractedText.length;

    // Compute average confidence
    let avgConf = 0;
    if (details.length > 0) {
      const totalScore = details.reduce((sum, item) => sum + (item.score || 0), 0);
      avgConf = Math.round((totalScore / details.length) * 100);
    }

    // Populate Metrics Banner
    statLinesCount.textContent = lines.length;
    statWordsCount.textContent = words;
    statCharsCount.textContent = chars;
    statAvgConfidence.textContent = details.length > 0 ? `${avgConf}%` : "N/A";
    statLatency.textContent = `${data.processing_time_ms || 0} ms`;
    statEngine.textContent = data.ocr_engine || "RapidOCR";

    // Populate Tab 1: Extracted Text & Line Numbers
    renderFormattedText(rawExtractedText);

    // Populate Tab 2: Line-by-Line Breakdown
    renderLineBreakdown(lines, details);

    // Populate Tab 3: Bounding Boxes
    renderBoundingBoxes(details);

    // Populate Tab 4: JSON Viewer
    jsonContent.textContent = JSON.stringify(data, null, 2);

    // Reset search input
    textSearchInput.value = "";
    searchMatchBadge.style.display = "none";
    clearSearchBtn.style.display = "none";

    // Display results container
    resultsContainer.style.display = "flex";
    resultActions.style.display = "flex";
    copyAllTextBtn.style.display = "inline-flex";
    downloadTxtBtn.style.display = "inline-flex";

    activateTab("tabNormalText");
  }

  function renderFormattedText(text) {
    extractedTextBody.textContent = text || "(No text recognized in image)";
    updateLineNumbers(text);
  }

  function updateLineNumbers(text) {
    const linesArr = text.split("\n");
    let gutterHtml = "";
    for (let i = 1; i <= Math.max(linesArr.length, 1); i++) {
      gutterHtml += `${i}<br>`;
    }
    lineNumbersGutter.innerHTML = gutterHtml;
    lineNumbersGutter.classList.toggle("hidden", !showLineNumbers);
  }

  function renderLineBreakdown(lines, details) {
    linesList.innerHTML = "";
    if (lines.length === 0) {
      linesList.innerHTML = `<div style="color: var(--text-dim); padding: 16px;">No individual lines detected.</div>`;
      return;
    }

    lines.forEach((lineText, idx) => {
      const card = document.createElement("div");
      card.className = "line-card";

      // Match confidence if detail item exists
      const detail = details[idx] || {};
      const score = detail.score !== undefined ? Math.round(detail.score * 100) : null;
      let scoreBadgeHtml = "";
      if (score !== null) {
        let scoreClass = score >= 90 ? "score-high" : (score >= 70 ? "score-med" : "score-low");
        scoreBadgeHtml = `<span class="line-score-badge ${scoreClass}">${score}% Conf</span>`;
      }

      card.innerHTML = `
        <div class="line-card-left">
          <span class="line-num-badge">#${idx + 1}</span>
          <span class="line-text-content">${escapeHtml(lineText)}</span>
        </div>
        <div class="line-card-right">
          ${scoreBadgeHtml}
          <button type="button" class="btn-copy-line" title="Copy this line" data-copy="${escapeHtml(lineText)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </div>
      `;
      linesList.appendChild(card);
    });

    linesList.querySelectorAll(".btn-copy-line").forEach(btn => {
      btn.addEventListener("click", () => {
        copyToClipboard(btn.getAttribute("data-copy"));
      });
    });
  }

  function renderBoundingBoxes(details) {
    boxesGrid.innerHTML = "";
    if (details.length === 0) {
      boxesGrid.innerHTML = `<div style="color: var(--text-dim); padding: 16px;">No bounding box coordinates provided.</div>`;
      return;
    }

    details.forEach((item, idx) => {
      const card = document.createElement("div");
      card.className = "box-card";
      const box = item.box || [];
      const score = item.score !== undefined ? Math.round(item.score * 100) : "--";

      card.innerHTML = `
        <div class="box-card-header">
          <span class="box-text-preview">#${idx + 1}: ${escapeHtml(item.text || '')}</span>
          <span class="line-score-badge score-high">${score}%</span>
        </div>
        <div class="box-coords-snippet">
          Bounding Box Polygon: [ ${box.map(pt => `[${pt[0]}, ${pt[1]}]`).join(", ")} ]
        </div>
      `;
      boxesGrid.appendChild(card);
    });
  }

  // Render KYC Extraction Results
  function renderKycResults(data) {
    if (data.status === "error") {
      alert("Error: " + (data.message || "Unknown extraction error"));
      emptyState.style.display = "flex";
      return;
    }

    if (data.masked_image_base64) {
      imagePreview.src = data.masked_image_base64;
      if (securityBadge) securityBadge.style.display = "inline-flex";
      const cleanName = previewFileName.textContent.replace(/^\[80% Masked\]\s*/, "");
      previewFileName.textContent = `[80% Masked] ${cleanName}`;
      showToast("Original image purged. Displaying 80% masked image.");
    }

    const docType = data.document_type || "UNKNOWN";
    resDocType.textContent = docType;
    resConfidence.textContent = Math.round((data.classification_confidence || 0) * 100) + "% Conf";
    resLatency.textContent = (data.processing_time_ms || 0) + " ms";
    resEngine.textContent = data.ocr_engine || "RapidOCR";

    setDocTypeStyle(docType);

    // KYC Fields
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
          <span class="field-key">${friendlyKey} ${isPrimary ? '(80% Masked on Card)' : ''}</span>
          <span class="field-value ${isPrimary ? 'highlight' : ''} ${isNull ? 'null-val' : ''}">${escapeHtml(displayVal)}</span>
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

    document.querySelectorAll(".btn-copy-field").forEach(btn => {
      btn.addEventListener("click", () => {
        copyToClipboard(btn.getAttribute("data-copy"));
      });
    });

    // Masked coordinates
    coordsList.innerHTML = "";
    const coords = data.confidential_coordinates || [];
    if (coords.length === 0) {
      coordsList.innerHTML = `<div class="empty-coords" style="color: var(--text-dim); font-size: 0.85rem; padding: 12px;">No confidential numbers detected to mask.</div>`;
    } else {
      coords.forEach((c, idx) => {
        const card = document.createElement("div");
        card.className = "coord-card";
        const b = c.bounding_rect || {};
        const m = c.mask_rect_80 || {};
        card.innerHTML = `
          <div class="coord-header">
            <span class="coord-field">Region #${idx + 1}: ${c.field}</span>
            <span class="coord-badge">80% Redacted</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-mono);">
            Matched Text: <strong style="color: #fff;">${escapeHtml(c.detected_text || '')}</strong>
          </div>
          <div class="coord-box-row">
            <div class="coord-box">
              <div class="coord-label">OCR Bounding Box [x, y, w, h]</div>
              <div class="coord-val">[X: ${b.x}, Y: ${b.y}, W: ${b.width}, H: ${b.height}]</div>
            </div>
            <div class="coord-box">
              <div class="coord-label">80% Black Mask Box [x, y, w, h]</div>
              <div class="coord-val text-success">[X: ${m.x}, Y: ${m.y}, W: ${m.width}, H: ${m.height}]</div>
            </div>
          </div>
        `;
        coordsList.appendChild(card);
      });
    }

    jsonContent.textContent = JSON.stringify(data, null, 2);
    ocrContent.textContent = data.raw_text || "No OCR lines extracted.";

    resultsContainer.style.display = "flex";
    resultActions.style.display = "flex";
    copyAllTextBtn.style.display = "none";
    downloadTxtBtn.style.display = "none";

    activateTab("tabFields");
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

  // Live Text Search in Extracted Text
  textSearchInput.addEventListener("input", () => {
    performSearch();
  });

  clearSearchBtn.addEventListener("click", () => {
    textSearchInput.value = "";
    performSearch();
  });

  function performSearch() {
    const query = textSearchInput.value.trim();
    if (!query) {
      extractedTextBody.textContent = rawExtractedText;
      searchMatchBadge.style.display = "none";
      clearSearchBtn.style.display = "none";
      return;
    }

    clearSearchBtn.style.display = "block";
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escapedQuery})`, "gi");
    const matches = rawExtractedText.match(regex);
    const count = matches ? matches.length : 0;

    searchMatchBadge.textContent = `${count} ${count === 1 ? 'match' : 'matches'}`;
    searchMatchBadge.style.display = "inline-block";

    if (count > 0) {
      // Highlight matches in body safely
      const escapedText = escapeHtml(rawExtractedText);
      const highlighted = escapedText.replace(regex, `<mark class="search-highlight">$1</mark>`);
      extractedTextBody.innerHTML = highlighted;
    } else {
      extractedTextBody.textContent = rawExtractedText;
    }
  }

  // Line Numbers Toggle
  toggleLineNumbersBtn.addEventListener("click", () => {
    showLineNumbers = !showLineNumbers;
    toggleLineNumbersBtn.classList.toggle("active", showLineNumbers);
    lineNumbersGutter.classList.toggle("hidden", !showLineNumbers);
  });

  // Word Wrap Toggle
  toggleWordWrapBtn.addEventListener("click", () => {
    enableWordWrap = !enableWordWrap;
    toggleWordWrapBtn.classList.toggle("active", enableWordWrap);
    extractedTextBody.classList.toggle("wrap-enabled", enableWordWrap);
  });

  // Export Actions: Copy, TXT, JSON
  copyAllTextBtn.addEventListener("click", () => {
    const textToCopy = rawExtractedText || extractedTextBody.textContent;
    if (textToCopy) copyToClipboard(textToCopy);
  });

  downloadTxtBtn.addEventListener("click", () => {
    const textToDownload = rawExtractedText || extractedTextBody.textContent;
    if (!textToDownload) return;
    const blob = new Blob([textToDownload], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `extracted_text_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded text file!");
  });

  downloadJsonBtn.addEventListener("click", () => {
    if (!lastResultData) return;
    const blob = new Blob([JSON.stringify(lastResultData, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ocr_result_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded JSON file!");
  });

  // Tab Switching Logic
  const allTabBtns = document.querySelectorAll(".tab-btn");
  allTabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      activateTab(targetTab);
    });
  });

  function activateTab(tabId) {
    const targetElement = document.getElementById(tabId);
    if (!targetElement) return;

    // Remove active from all tabs and buttons in current header
    const currentHeader = currentMode === "normal" ? normalTabsHeader : kycTabsHeader;
    currentHeader.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));

    // Hide all tab contents
    document.querySelectorAll(".tab-content").forEach(tc => {
      tc.classList.remove("active");
      tc.style.display = "none";
    });

    // Activate selected button
    const targetBtn = currentHeader.querySelector(`[data-tab="${tabId}"]`);
    if (targetBtn) targetBtn.classList.add("active");

    // Show selected content
    targetElement.classList.add("active");
    targetElement.style.display = "block";
  }

  // Helpers
  function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      showToast("Copied to clipboard!");
    }).catch(() => {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      showToast("Copied to clipboard!");
    });
  }

  function showToast(msg = "Copied to clipboard!") {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 2800);
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // Health Status Fetch
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
