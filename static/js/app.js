/* DocMind AI — Enterprise Workspace Application Controller */

document.addEventListener("DOMContentLoaded", () => {
  let activeView = "overview";
  let activeChatId = null;
  let conversations = [];
  let documents = [];

  let selectedDocIds = []; // Array of selected document IDs for scoping, or [] for All Documents
  let uploadQueueFiles = []; // File objects queued for upload

  // DOM Elements
  const railItems = document.querySelectorAll(".rail-item");
  const viewPanels = document.querySelectorAll(".view-panel");

  // Hero Elements
  const btnHeroTry = document.getElementById("btn-hero-try");
  const btnHeroExplore = document.getElementById("btn-hero-explore");
  const btnFinalTry = document.getElementById("btn-final-try");

  // Rail Session Shortcuts
  const railSessionsList = document.getElementById("rail-sessions-list");
  const btnRailNewChat = document.getElementById("btn-rail-new-chat");

  // Chat Elements
  const messagesContainer = document.getElementById("messages-container");
  const chatInput = document.getElementById("chat-input");
  const btnSend = document.getElementById("btn-send");

  // Document Scope Dropdown Elements
  const btnDocScopeTrigger = document.getElementById("btn-doc-scope-trigger");
  const docScopeMenu = document.getElementById("doc-scope-menu");
  const docScopeOptions = document.getElementById("doc-scope-options");
  const docScopeLabel = document.getElementById("doc-scope-label");

  // Knowledge Base Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const btnTriggerUpload = document.getElementById("btn-trigger-upload");
  const knowledgeTableBody = document.getElementById("knowledge-table-body");
  const uploadQueueCard = document.getElementById("upload-queue-card");
  const uploadQueueList = document.getElementById("upload-queue-list");
  const uploadQueueTitle = document.getElementById("upload-queue-title");
  const btnProcessUploadQueue = document.getElementById("btn-process-upload-queue");

  // Insights View Elements
  const insightDocCount = document.getElementById("insight-doc-count");
  const insightPageCount = document.getElementById("insight-page-count");
  const insightChunkCount = document.getElementById("insight-chunk-count");
  const insightsTableBody = document.getElementById("insights-table-body");

  // Drawer Elements
  const docViewerModal = document.getElementById("doc-viewer-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const modalDocTitle = document.getElementById("modal-doc-title");
  const modalDocBody = document.getElementById("modal-doc-body");

  // History Table
  const historyTableBody = document.getElementById("history-table-body");

  // Settings Elements
  const settingsForm = document.getElementById("settings-form");
  const settingProvider = document.getElementById("setting-provider");
  const settingModelSelect = document.getElementById("setting-model-select");
  const groupOllamaUrl = document.getElementById("group-ollama-url");
  const groupApiKey = document.getElementById("group-api-key");
  const settingApiKey = document.getElementById("setting-api-key");
  const btnToggleKeyVisibility = document.getElementById("btn-toggle-key-visibility");
  const settingEmbedding = document.getElementById("setting-embedding");
  const settingChunkSize = document.getElementById("setting-chunk-size");
  const settingChunkOverlap = document.getElementById("setting-chunk-overlap");
  const settingTemperature = document.getElementById("setting-temperature");
  const valTemperature = document.getElementById("val-temperature");
  const settingMaxTokens = document.getElementById("setting-max-tokens");
  const activeLlmText = document.getElementById("active-llm-text");
  const topbarDbText = document.getElementById("topbar-db-text");
  const topbarDbDot = document.getElementById("topbar-db-dot");
  const topbarAiText = document.getElementById("topbar-ai-text");
  const topbarAiDot = document.getElementById("topbar-ai-dot");
  const connectionStatusBadge = document.getElementById("connection-status-badge");
  const btnTestConnection = document.getElementById("btn-test-connection");

  async function refreshSystemHealth() {
    try {
      const h = await ApiClient.getHealth();
      
      if (h.database && h.database.connected) {
        if (topbarDbText) topbarDbText.textContent = "PostgreSQL Connected";
        if (topbarDbDot) topbarDbDot.style.background = "var(--success-color)";
      } else {
        if (topbarDbText) topbarDbText.textContent = "PostgreSQL Offline";
        if (topbarDbDot) topbarDbDot.style.background = "var(--danger-color)";
      }

      if (h.llm) {
        const isOnline = h.llm.connected;
        const statusWord = isOnline ? "AI Connected" : "AI Offline";
        const label = `${statusWord} · ${h.llm.provider} · ${h.llm.model}`;
        
        if (topbarAiText) topbarAiText.textContent = label;
        if (topbarAiDot) topbarAiDot.style.background = isOnline ? "var(--success-color)" : "var(--danger-color)";

        if (activeLlmText) activeLlmText.textContent = `${h.llm.provider} (${h.llm.model})`;
      }
    } catch (err) {
      console.error("Health check error:", err);
      if (topbarDbText) topbarDbText.textContent = "PostgreSQL Offline";
      if (topbarDbDot) topbarDbDot.style.background = "var(--danger-color)";
      if (topbarAiText) topbarAiText.textContent = "AI Offline";
      if (topbarAiDot) topbarAiDot.style.background = "var(--danger-color)";
    }
  }

  // Initialize App
  async function init() {
    setupNavigation();
    setupEventListeners();
    setupDocScopeDropdown();

    try {
      await refreshSystemHealth();
    } catch (e) {
      console.warn("Health check initialization deferred:", e);
    }

    try {
      await loadWorkspaceData();
    } catch (e) {
      console.warn("Workspace data initialization deferred:", e);
    }

    switchView("overview");
  }

  // Navigation Setup
  function setupNavigation() {
    railItems.forEach((item) => {
      item.addEventListener("click", () => {
        const targetView = item.getAttribute("data-view");
        switchView(targetView);
      });
    });

    if (btnHeroTry) {
      btnHeroTry.addEventListener("click", () => startNewChat());
    }
    if (btnHeroExplore) {
      btnHeroExplore.addEventListener("click", () => switchView("knowledge"));
    }
    if (btnFinalTry) {
      btnFinalTry.addEventListener("click", () => startNewChat());
    }
  }

  function switchView(viewName) {
    activeView = viewName;

    railItems.forEach((item) => {
      if (item.getAttribute("data-view") === viewName) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });

    viewPanels.forEach((panel) => {
      if (panel.id === `view-${viewName}`) {
        panel.classList.add("active");
      } else {
        panel.classList.remove("active");
      }
    });

    try {
      if (viewName === "knowledge") renderKnowledgeTable();
      if (viewName === "history") renderHistoryTable();
      if (viewName === "insights") renderInsightsView();
      if (viewName === "settings") loadSettingsView();
      if (viewName === "chat") renderDocScopeOptions();
    } catch (err) {
      console.error("View rendering error:", err);
    }
  }

  // Document Scope Dropdown Setup
  function setupDocScopeDropdown() {
    if (!btnDocScopeTrigger || !docScopeMenu) return;

    btnDocScopeTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const isVisible = docScopeMenu.style.display === "block";
      docScopeMenu.style.display = isVisible ? "none" : "block";
    });

    document.addEventListener("click", (e) => {
      if (docScopeMenu && !docScopeMenu.contains(e.target) && e.target !== btnDocScopeTrigger) {
        docScopeMenu.style.display = "none";
      }
    });
  }

  function renderDocScopeOptions() {
    if (!docScopeOptions) return;
    docScopeOptions.innerHTML = "";

    // 1. All Documents Checkbox
    const allRow = document.createElement("label");
    allRow.style.cssText = "display:flex; align-items:center; gap:8px; font-size:0.8rem; cursor:pointer; padding:4px 0;";
    const allChecked = selectedDocIds.length === 0;
    allRow.innerHTML = `
      <input type="checkbox" id="chk-scope-all" ${allChecked ? "checked" : ""}>
      <span style="font-weight:600;">✓ All Documents</span>
    `;

    allRow.querySelector("input").addEventListener("change", (e) => {
      if (e.target.checked) {
        selectedDocIds = [];
      }
      renderDocScopeOptions();
      updateDocScopeLabel();
    });
    docScopeOptions.appendChild(allRow);

    if (documents.length === 0) {
      const emptyItem = document.createElement("div");
      emptyItem.style.cssText = "font-size:0.75rem; color:var(--text-muted); padding:4px 0;";
      emptyItem.textContent = "No documents uploaded.";
      docScopeOptions.appendChild(emptyItem);
      updateDocScopeLabel();
      return;
    }

    // 2. Individual Document Checkboxes
    documents.forEach((doc) => {
      const row = document.createElement("label");
      row.style.cssText = "display:flex; align-items:center; gap:8px; font-size:0.8rem; cursor:pointer; padding:3px 0;";
      const isChecked = selectedDocIds.includes(doc.id);
      row.innerHTML = `
        <input type="checkbox" value="${doc.id}" ${isChecked ? "checked" : ""}>
        <span style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">📄 ${escapeHtml(doc.filename)}</span>
      `;

      row.querySelector("input").addEventListener("change", (e) => {
        const did = doc.id;
        if (e.target.checked) {
          if (!selectedDocIds.includes(did)) selectedDocIds.push(did);
        } else {
          selectedDocIds = selectedDocIds.filter(id => id !== did);
        }
        renderDocScopeOptions();
        updateDocScopeLabel();
      });

      docScopeOptions.appendChild(row);
    });

    updateDocScopeLabel();
  }

  function updateDocScopeLabel() {
    if (!docScopeLabel) return;
    if (selectedDocIds.length === 0) {
      docScopeLabel.textContent = "DOCUMENT SCOPE: All Documents";
    } else if (selectedDocIds.length === 1) {
      const d = documents.find(doc => doc.id === selectedDocIds[0]);
      docScopeLabel.textContent = `SCOPE: ${d ? d.filename : '1 Document'}`;
    } else {
      docScopeLabel.textContent = `SCOPE: ${selectedDocIds.length} Documents Selected`;
    }
  }

  // Load Workspace Data
  async function loadWorkspaceData() {
    await refreshDocuments();
    await refreshConversations();
  }

  async function refreshDocuments() {
    try {
      const data = await ApiClient.getDocuments();
      documents = data.documents || [];

      if (activeView === "knowledge") renderKnowledgeTable();
      if (activeView === "insights") renderInsightsView();
      renderDocScopeOptions();
    } catch (err) {
      console.error("Failed to fetch documents:", err);
    }
  }

  async function refreshConversations() {
    try {
      const data = await ApiClient.getConversations();
      conversations = data.conversations || data.chats || [];

      renderRailSessionsList();
      if (activeView === "history") renderHistoryTable();
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    }
  }

  // Rail Recent Chats List
  function renderRailSessionsList() {
    if (!railSessionsList) return;
    railSessionsList.innerHTML = "";

    if (conversations.length === 0) {
      railSessionsList.innerHTML = `
        <div style="font-size:0.75rem; color:var(--text-muted); padding:8px 4px; text-align:center;">
          <div>No conversations yet.</div>
          <button class="btn-xs btn-primary" id="btn-rail-start-first" style="margin-top:6px; width:100%;">Start your first chat</button>
        </div>
      `;
      const btnFirst = document.getElementById("btn-rail-start-first");
      if (btnFirst) btnFirst.addEventListener("click", () => startNewChat());
      return;
    }

    conversations.slice(0, 8).forEach((chat) => {
      const item = document.createElement("div");
      item.className = `rail-session-item ${chat.id === activeChatId ? 'active' : ''}`;
      item.textContent = `💬 ${chat.title}`;
      item.addEventListener("click", () => {
        selectConversation(chat.id);
        switchView("chat");
      });
      railSessionsList.appendChild(item);
    });
  }

  // Document Insights View Rendering
  function renderInsightsView() {
    let totalPages = 0;
    let totalChunks = 0;

    documents.forEach((d) => {
      totalPages += (d.pages || 0);
      totalChunks += (d.chunks || 0);
    });

    if (insightDocCount) insightDocCount.textContent = documents.length;
    if (insightPageCount) insightPageCount.textContent = totalPages;
    if (insightChunkCount) insightChunkCount.textContent = totalChunks;

    if (!insightsTableBody) return;
    insightsTableBody.innerHTML = "";
    if (documents.length === 0) {
      insightsTableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:16px;">No indexed documents in knowledge base.</td></tr>`;
      return;
    }

    documents.forEach((doc) => {
      const tr = document.createElement("tr");
      const ext = (doc.file_type || doc.filename.split('.').pop() || 'pdf').toUpperCase();
      tr.innerHTML = `
        <td style="font-weight:600;">📄 ${escapeHtml(doc.filename)}</td>
        <td><span class="tool-badge">${ext}</span></td>
        <td>${doc.pages || 0}</td>
        <td>${doc.chunks || 0}</td>
        <td><span style="color:var(--success-color); font-weight:600;">${doc.status || 'Ready'}</span></td>
      `;
      insightsTableBody.appendChild(tr);
    });
  }

  // Knowledge Base Data Table & Batch Upload Queue
  function renderKnowledgeTable() {
    if (!knowledgeTableBody) return;
    knowledgeTableBody.innerHTML = "";
    if (documents.length === 0) {
      knowledgeTableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:24px;">Your knowledge base is empty. Upload your first document to start asking questions.</td></tr>`;
      return;
    }

    documents.forEach((doc) => {
      const tr = document.createElement("tr");
      const ext = (doc.file_type || doc.filename.split('.').pop() || 'pdf').toUpperCase();
      tr.innerHTML = `
        <td style="font-weight:600;">📄 ${escapeHtml(doc.filename)}</td>
        <td><span class="tool-badge">${ext}</span></td>
        <td>${doc.pages || 0}</td>
        <td>${doc.chunks || 0}</td>
        <td><span style="color:var(--success-color); font-weight:600;">${doc.status || 'Ready'}</span></td>
        <td style="text-align:right;">
          <button class="btn-xs btn-inspect-doc">Inspect</button>
          <button class="btn-xs btn-xs-danger btn-delete-doc">Delete</button>
        </td>
      `;

      tr.querySelector(".btn-inspect-doc").addEventListener("click", () => openDocumentViewer(doc));
      tr.querySelector(".btn-delete-doc").addEventListener("click", async () => {
        if (confirm(`Delete document '${doc.filename}'?`)) {
          await ApiClient.deleteDocument(doc.id);
          await refreshDocuments();
        }
      });
      knowledgeTableBody.appendChild(tr);
    });
  }

  function renderUploadQueue() {
    if (!uploadQueueCard || !uploadQueueList || !uploadQueueTitle) return;
    if (uploadQueueFiles.length === 0) {
      uploadQueueCard.style.display = "none";
      return;
    }

    uploadQueueCard.style.display = "block";
    uploadQueueTitle.textContent = `Selected Files Queue (${uploadQueueFiles.length} files)`;
    uploadQueueList.innerHTML = "";

    uploadQueueFiles.forEach((file, idx) => {
      const item = document.createElement("div");
      item.style.cssText = "display:flex; justify-content:space-between; align-items:center; background:var(--bg-rail); border:1px solid var(--border-color); padding:8px 12px; border-radius:6px; font-size:0.82rem;";
      const sizeKb = (file.size / 1024).toFixed(1);
      item.innerHTML = `
        <div>
          <span style="font-weight:600;">📄 ${escapeHtml(file.name)}</span>
          <span style="color:var(--text-muted); margin-left:8px;">(${sizeKb} KB)</span>
        </div>
        <button class="btn-icon-xs btn-remove-queued-file" title="Remove File">✕</button>
      `;

      item.querySelector(".btn-remove-queued-file").addEventListener("click", () => {
        uploadQueueFiles.splice(idx, 1);
        renderUploadQueue();
      });

      uploadQueueList.appendChild(item);
    });
  }

  // Document Viewer Drawer
  async function openDocumentViewer(doc) {
    if (!modalDocTitle || !modalDocBody || !docViewerModal) return;
    modalDocTitle.textContent = `📄 Document: ${doc.filename}`;
    modalDocBody.innerHTML = `
      <div style="margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid var(--border-color);">
        <div><strong>Filename:</strong> ${escapeHtml(doc.filename)}</div>
        <div><strong>File Format:</strong> ${(doc.file_type || 'PDF').toUpperCase()}</div>
        <div><strong>Page Count:</strong> ${doc.pages || 0}</div>
        <div><strong>Indexed Sections:</strong> ${doc.chunks || 0}</div>
      </div>
      <div><strong>Processing Status:</strong> <span style="color:var(--success-color); font-weight:600;">${doc.status || 'Ready'}</span></div>
    `;
    docViewerModal.classList.add("active");
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener("click", () => {
      if (docViewerModal) docViewerModal.classList.remove("active");
    });
  }
  if (docViewerModal) {
    docViewerModal.addEventListener("click", (e) => {
      if (e.target === docViewerModal) docViewerModal.classList.remove("active");
    });
  }

  // History Table
  function renderHistoryTable() {
    if (!historyTableBody) return;
    historyTableBody.innerHTML = "";
    if (conversations.length === 0) {
      historyTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:20px;">No saved conversation history sessions.</td></tr>`;
      return;
    }

    conversations.forEach((chat) => {
      const tr = document.createElement("tr");
      const createdDate = chat.created_at ? new Date(chat.created_at).toLocaleString() : "Recent";
      tr.innerHTML = `
        <td style="font-weight:600;">💬 ${escapeHtml(chat.title)}</td>
        <td style="color:var(--text-muted); font-family:'JetBrains Mono', monospace; font-size:0.78rem;">#${chat.id}</td>
        <td style="color:var(--text-muted); font-size:0.78rem;">${createdDate}</td>
        <td style="text-align:right;">
          <button class="btn-xs btn-open-chat">Open Chat</button>
          <button class="btn-xs btn-xs-danger btn-delete-chat">Delete</button>
        </td>
      `;

      tr.querySelector(".btn-open-chat").addEventListener("click", () => {
        selectConversation(chat.id);
        switchView("chat");
      });
      tr.querySelector(".btn-delete-chat").addEventListener("click", async () => {
        if (confirm(`Delete conversation session '${chat.title}'?`)) {
          await ApiClient.deleteConversation(chat.id);
          if (activeChatId === chat.id) activeChatId = null;
          await refreshConversations();
        }
      });
      historyTableBody.appendChild(tr);
    });
  }

  // Settings Logic
  async function updateProviderUI(provider, selectedModel = null) {
    if (!groupOllamaUrl || !groupApiKey || !settingModelSelect) return;
    if (provider === "Ollama") {
      groupOllamaUrl.style.display = "flex";
      groupApiKey.style.display = "none";
    } else {
      groupOllamaUrl.style.display = "none";
      groupApiKey.style.display = "flex";
    }

    try {
      const res = await ApiClient.getProviderModels(provider);
      const models = res.models || [];
      settingModelSelect.innerHTML = "";

      let foundSelected = false;
      models.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        if (m === selectedModel) {
          opt.selected = true;
          foundSelected = true;
        }
        settingModelSelect.appendChild(opt);
      });

      if (!foundSelected && models.length > 0) {
        settingModelSelect.selectedIndex = 0;
      }
    } catch (err) {
      console.error("Failed to load provider models:", err);
    }
  }

  if (settingProvider) {
    settingProvider.addEventListener("change", () => {
      updateProviderUI(settingProvider.value);
    });
  }

  if (settingTemperature && valTemperature) {
    settingTemperature.addEventListener("input", () => {
      valTemperature.textContent = settingTemperature.value;
    });
  }

  if (btnToggleKeyVisibility && settingApiKey) {
    btnToggleKeyVisibility.addEventListener("click", () => {
      if (settingApiKey.type === "password") {
        settingApiKey.type = "text";
        btnToggleKeyVisibility.textContent = "Hide";
      } else {
        settingApiKey.type = "password";
        btnToggleKeyVisibility.textContent = "Show";
      }
    });
  }

  const btnClearApiKey = document.getElementById("btn-clear-api-key");
  const apiKeyStatusHint = document.getElementById("api-key-status-hint");

  if (btnClearApiKey) {
    btnClearApiKey.addEventListener("click", async () => {
      if (confirm("Are you sure you want to clear your saved API key for this provider?")) {
        try {
          const prov = settingProvider ? settingProvider.value : "Groq";
          await ApiClient.updateSettings({
            llm_provider: prov,
            llm_model: settingModelSelect ? settingModelSelect.value : "llama-3.1-8b-instant",
            clear_api_key: true
          });
          if (settingApiKey) settingApiKey.value = "";
          if (apiKeyStatusHint) apiKeyStatusHint.textContent = "API key cleared for this provider.";
          await refreshSystemHealth();
          alert("API key cleared successfully!");
        } catch (err) {
          alert(`Failed to clear API key: ${err.message}`);
        }
      }
    });
  }

  async function loadSettingsView() {
    try {
      const st = await ApiClient.getSettings();
      const prov = st.llm_provider || "Ollama";
      const mod = st.llm_model || "llama-3.1-8b-instant";

      if (settingProvider) settingProvider.value = prov;
      await updateProviderUI(prov, mod);

      // ALWAYS keep API key input field completely EMPTY on load
      if (settingApiKey) {
        settingApiKey.value = "";
        settingApiKey.placeholder = "Enter API key to update";
      }

      const hasKey = prov === "Groq" ? (st.groq_api_key || st.api_key) : (prov === "OpenAI" ? (st.openai_api_key || st.api_key) : false);
      if (apiKeyStatusHint) {
        apiKeyStatusHint.textContent = hasKey 
          ? "✓ Stored credential active. Enter new key to update." 
          : "No API key configured for this provider.";
      }

      if (settingEmbedding) settingEmbedding.value = st.embedding_model || "all-MiniLM-L6-v2";
      if (settingChunkSize) settingChunkSize.value = st.chunk_size || 500;
      if (settingChunkOverlap) settingChunkOverlap.value = st.chunk_overlap || 50;
      if (settingTemperature) {
        settingTemperature.value = st.temperature || 0.2;
        if (valTemperature) valTemperature.textContent = settingTemperature.value;
      }
      if (settingMaxTokens) settingMaxTokens.value = st.max_tokens || 1024;

      if (activeLlmText) activeLlmText.textContent = `${prov} (${mod})`;
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  }

  if (btnTestConnection) {
    btnTestConnection.addEventListener("click", async () => {
      const prov = settingProvider ? settingProvider.value : "Ollama";
      const mod = settingModelSelect ? settingModelSelect.value : "";
      const key = settingApiKey ? settingApiKey.value : "";

      if (connectionStatusBadge) {
        connectionStatusBadge.innerHTML = `<span style="color:var(--accent-primary);">● Testing...</span>`;
      }

      try {
        const res = await ApiClient.testConnection({
          llm_provider: prov,
          llm_model: mod,
          api_key: key
        });

        if (res.success) {
          if (connectionStatusBadge) connectionStatusBadge.innerHTML = `<span style="color:var(--success-color);">✓ Connected</span>`;
          await refreshSystemHealth();
        } else {
          if (connectionStatusBadge) connectionStatusBadge.innerHTML = `<span style="color:var(--danger-color);">✕ Connection Failed</span>`;
          await refreshSystemHealth();
          alert(res.message || "Connection failed.");
        }
      } catch (err) {
        if (connectionStatusBadge) connectionStatusBadge.innerHTML = `<span style="color:var(--danger-color);">✕ Error</span>`;
        await refreshSystemHealth();
        alert(`Connection test error: ${err.message}`);
      }
    });
  }

  if (settingsForm) {
    settingsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        llm_provider: settingProvider.value,
        llm_model: settingModelSelect.value,
        api_key: settingApiKey.value,
        embedding_model: settingEmbedding.value,
        chunk_size: parseInt(settingChunkSize.value),
        chunk_overlap: parseInt(settingChunkOverlap.value),
        temperature: parseFloat(settingTemperature.value),
        max_tokens: parseInt(settingMaxTokens.value)
      };

      try {
        await ApiClient.updateSettings(payload);
        if (settingApiKey) settingApiKey.value = "";
        await loadSettingsView();
        await refreshSystemHealth();
        alert("Settings saved successfully!");
      } catch (err) {
        alert(`Failed to save settings: ${err.message}`);
      }
    });
  }

  // Event Listeners
  function setupEventListeners() {
    if (btnTriggerUpload && fileInput) {
      btnTriggerUpload.addEventListener("click", () => fileInput.click());
    }

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      
      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--accent-primary)";
      });
      dropzone.addEventListener("dragleave", () => {
        dropzone.style.borderColor = "var(--border-light)";
      });
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--border-light)";
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          Array.from(e.dataTransfer.files).forEach(f => uploadQueueFiles.push(f));
          renderUploadQueue();
        }
      });

      fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
          Array.from(fileInput.files).forEach(f => uploadQueueFiles.push(f));
          renderUploadQueue();
        }
      });
    }

    if (btnProcessUploadQueue) {
      btnProcessUploadQueue.addEventListener("click", async () => {
        if (uploadQueueFiles.length === 0) return;
        btnProcessUploadQueue.disabled = true;
        btnProcessUploadQueue.textContent = "Processing Batch...";

        try {
          const res = await ApiClient.uploadMultipleDocuments(uploadQueueFiles);
          const numSuccess = res.uploaded ? res.uploaded.length : 0;
          const numFailed = res.failed ? res.failed.length : 0;
          
          alert(`Batch upload complete:\n- Successfully indexed: ${numSuccess}\n- Rejected/Failed: ${numFailed}`);
          uploadQueueFiles = [];
          renderUploadQueue();
          await refreshDocuments();
        } catch (err) {
          alert(`Batch upload error: ${err.message}`);
        } finally {
          btnProcessUploadQueue.disabled = false;
          btnProcessUploadQueue.textContent = "Upload Documents";
        }
      });
    }

    if (btnRailNewChat) {
      btnRailNewChat.addEventListener("click", () => startNewChat());
    }

    if (btnSend && chatInput) {
      btnSend.addEventListener("click", sendMessage);
      chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendMessage();
      });
    }
  }

  async function startNewChat() {
    try {
      const chat = await ApiClient.createConversation("New Conversation");
      activeChatId = chat.id;
      await refreshConversations();
      selectConversation(chat.id);
      switchView("chat");
    } catch (err) {
      console.error("Failed to create chat:", err);
    }
  }

  async function selectConversation(chatId) {
    activeChatId = chatId;
    renderRailSessionsList();
    try {
      const chat = await ApiClient.getConversation(chatId);
      renderMessages(chat.messages || []);
    } catch (err) {
      console.error("Failed to load conversation messages:", err);
    }
  }

  function renderMessages(messages) {
    if (!messagesContainer) return;
    messagesContainer.innerHTML = "";

    if (!messages || messages.length === 0) {
      resetChatWorkspace();
      return;
    }
    messages.forEach((msg) => {
      const parsedSources = typeof msg.sources === "string" ? JSON.parse(msg.sources) : msg.sources;
      const bubble = document.createElement("div");
      bubble.className = `message-bubble message-${msg.sender}`;
      bubble.innerHTML = msg.sender === "user" ? escapeHtml(msg.content) : formatAssistantResponse(msg.content, parsedSources, []);
      messagesContainer.appendChild(bubble);
    });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function resetChatWorkspace() {
    if (!messagesContainer) return;
    messagesContainer.innerHTML = `
      <div class="empty-workspace-state">
        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <h2>Ask your documents anything.</h2>
        <p class="empty-state-sub">Select your documents, ask a question, and get grounded answers with citations from your knowledge base.</p>
        <div class="suggestion-chips-container">
          <button class="chip-query-btn" data-query="Summarize this document">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chip-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            <span>Summarize this document</span>
          </button>
          <button class="chip-query-btn" data-query="Find the key findings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chip-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <span>Find the key findings</span>
          </button>
          <button class="chip-query-btn" data-query="Compare selected documents">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chip-icon"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            <span>Compare selected documents</span>
          </button>
        </div>
      </div>
    `;

    messagesContainer.querySelectorAll(".chip-query-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const q = btn.getAttribute("data-query");
        if (q && chatInput) {
          chatInput.value = q;
          sendMessage();
        }
      });
    });
  }

  async function sendMessage() {
    if (!chatInput) return;
    const query = chatInput.value.trim();
    if (!query) return;
    chatInput.value = "";

    if (messagesContainer && messagesContainer.querySelector(".empty-workspace-state")) {
      messagesContainer.innerHTML = "";
    }

    appendMessageBubble("user", query);
    const loadingElem = appendMessageBubble("assistant", "Thinking...");

    try {
      const res = await ApiClient.sendChatMessage(activeChatId, query, selectedDocIds);
      if (res.conversation_id) {
        activeChatId = res.conversation_id;
        await refreshConversations();
      }

      loadingElem.innerHTML = formatAssistantResponse(res.answer, res.sources, res.tools_used);
      if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (err) {
      let friendlyError = "AI service unavailable. Please check your LLM configuration or start Ollama.";
      if (err.message && !err.message.includes("WinError")) {
        friendlyError = err.message;
      }
      loadingElem.innerHTML = `<span style="color:var(--danger-color);">⚠️ ${escapeHtml(friendlyError)}</span>`;
    }
  }

  function appendMessageBubble(sender, content) {
    const bubble = document.createElement("div");
    bubble.className = `message-bubble message-${sender}`;
    bubble.innerHTML = escapeHtml(content);
    if (messagesContainer) {
      messagesContainer.appendChild(bubble);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    return bubble;
  }

  function formatAssistantResponse(answer, sources, toolsUsed) {
    let html = `<div>${escapeHtml(answer)}</div>`;

    if (sources && sources.length > 0) {
      html += `<div class="citation-sources-box" style="margin-top:12px; padding:10px; background:rgba(255,255,255,0.03); border:1px solid var(--border-color); border-radius:6px; font-size:0.8rem;">`;
      html += `<div style="font-weight:700; color:var(--accent-primary); margin-bottom:6px; font-size:0.75rem; text-transform:uppercase;">Verified Document Sources</div>`;
      sources.forEach((src, idx) => {
        const docName = src.document || src.filename || "Document";
        const page = src.page ? ` (Page ${src.page})` : "";
        html += `<div style="color:var(--text-muted); margin-top:2px;">• <strong>${escapeHtml(docName)}${page}</strong></div>`;
      });
      html += `</div>`;
    }

    return html;
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  init();
});
