document.addEventListener("DOMContentLoaded", () => {
    const modeButtons = document.querySelectorAll(".mode-btn");
    const styleContainer = document.getElementById("style-selector-container");
    const styleSelect = document.getElementById("style-select");
    const processBtn = document.getElementById("process-btn");
    const loadingDiv = document.getElementById("loading");
    const mainEditor = document.getElementById("main-editor");
    const resultsContent = document.getElementById("results-content");
    const oracleInstruction = document.getElementById("oracle-instruction");
    const historyPanel = document.getElementById("history-panel");
    const historyList = document.getElementById("history-list");
    const historyMoreBtn = document.getElementById("history-more-btn");
    const toastContainer = document.getElementById("toast-container");
    const fontSizeControl = document.getElementById("font-size-control");
    const lineHeightControl = document.getElementById("line-height-control");
    const projectsList = document.getElementById("projects-list");
    const newProjectBtn = document.getElementById("new-project-btn");
    const saveDocBtn = document.getElementById("save-doc-btn");
    const saveStatus = document.getElementById("save-status");
    const currentProjectTitle = document.getElementById("current-project-title");
    const guidedProgress = document.getElementById("guided-progress");
    const guidedStageLabel = document.getElementById("guided-stage-label");
    const guidedNextBtn = document.getElementById("guided-next-btn");
    const modalOverlay = document.getElementById("modal-overlay");
    const newProjectModal = document.getElementById("new-project-modal");
    const newProjectTitleInput = document.getElementById("new-project-title");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const modalCreateBtn = document.getElementById("modal-create-btn");
    const GUIDED_STAGES = ["idea", "estructura", "introduccion", "desarrollo", "contraargumento", "conclusion", "completado"];
    const API_TOKEN_KEY = "sysiphus_api_token";
    const USER_ID_KEY = "sysiphus_user_id";

    let currentMode = "ensayo";
    let activeProjectId = null;
    let typingTimer;
    let currentGuidedStage = "idea";
    let accumulatedContent = "";
    let canAdvanceStage = false;
    let historyOffset = 0;
    const historyLimit = 20;

    function ensureClientIdentity() {
        if (!localStorage.getItem(API_TOKEN_KEY)) {
            localStorage.setItem(API_TOKEN_KEY, "dev-token");
        }
        if (!localStorage.getItem(USER_ID_KEY)) {
            localStorage.setItem(USER_ID_KEY, crypto.randomUUID());
        }
    }

    function getHeaders() {
        return {
            "Content-Type": "application/json",
            "X-Api-Token": localStorage.getItem(API_TOKEN_KEY) || "",
            "X-User-Id": localStorage.getItem(USER_ID_KEY) || "",
        };
    }

    async function apiFetch(url, opts = {}) {
        const headers = { ...getHeaders(), ...(opts.headers || {}) };
        const response = await fetch(url, { ...opts, headers });
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            throw new Error(body.detail || "Error en la solicitud");
        }
        return response;
    }

    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type === "error" ? "error" : ""}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 2800);
    }

    function renderMarkdownSafe(markdown) {
        const html = marked.parse(markdown || "");
        const clean = DOMPurify.sanitize(html);
        resultsContent.innerHTML = clean;
    }

    function renderEmptyResult(text) {
        resultsContent.innerHTML = `<div class="empty-state">${text}</div>`;
    }

    function closeModal() {
        modalOverlay.classList.add("hidden");
        newProjectModal.classList.add("hidden");
    }

    function setModeVisual(modeId) {
        modeButtons.forEach(b => {
            b.classList.toggle("active", b.getAttribute("data-mode") === modeId);
        });
        currentMode = modeId;
        styleContainer.classList.toggle("hidden", currentMode !== "estilo");
        updateGuidedUI();
    }

    function updateGuidedUI() {
        if (activeProjectId && currentMode === "guia") {
            guidedProgress.classList.remove("hidden");
            const stageLabel = (currentGuidedStage.charAt(0).toUpperCase() + currentGuidedStage.slice(1)).replace("Contraargumento", "Contra-Arg");
            guidedStageLabel.textContent = "Fase: " + stageLabel;
            guidedNextBtn.classList.toggle("hidden", currentGuidedStage === "completado");
            guidedNextBtn.disabled = !canAdvanceStage || currentGuidedStage === "completado";
            mainEditor.placeholder = `Modo Guía (${stageLabel})...\nRedacta aquí tu borrador para esta fase.`;
        } else {
            guidedProgress.classList.add("hidden");
            mainEditor.placeholder = "Plasma tu idea, premisa o borrador aquí. Selecciona o crea un proyecto para mantener tus reflexiones persistentes...";
        }
    }

    async function loadProjects() {
        try {
            const res = await apiFetch("/api/projects?limit=100&offset=0");
            renderProjects(await res.json());
        } catch (e) {
            showToast(`Error cargando proyectos: ${e.message}`, "error");
        }
    }

    function renderProjects(projects) {
        projectsList.innerHTML = "";
        projects.forEach(p => {
            const el = document.createElement("div");
            el.className = `project-item ${activeProjectId === p.id ? "active" : ""}`;
            const titleSpan = document.createElement("span");
            titleSpan.textContent = p.title;
            const delBtn = document.createElement("button");
            delBtn.className = "del-project-btn";
            delBtn.textContent = "×";
            delBtn.title = "Eliminar proyecto";
            delBtn.onclick = (e) => {
                e.stopPropagation();
                deleteProject(p.id);
            };
            el.appendChild(titleSpan);
            el.appendChild(delBtn);
            el.onclick = () => selectProject(p.id);
            projectsList.appendChild(el);
        });
    }

    async function loadInteractionHistory(reset = true) {
        if (!activeProjectId) {
            historyPanel.classList.add("hidden");
            return;
        }
        if (reset) {
            historyOffset = 0;
            historyList.innerHTML = "";
        }
        const res = await apiFetch(`/api/projects/${activeProjectId}/interactions?limit=${historyLimit}&offset=${historyOffset}`);
        const data = await res.json();
        historyPanel.classList.remove("hidden");
        data.items.forEach((item) => {
            const el = document.createElement("div");
            el.className = "history-item";
            el.textContent = `${item.mode.toUpperCase()} · ${new Date(item.timestamp).toLocaleString()}`;
            el.onclick = () => {
                renderMarkdownSafe(item.ai_output);
                if (item.mode !== "guia") setModeVisual(item.mode);
            };
            historyList.appendChild(el);
        });
        historyOffset += data.items.length;
        historyMoreBtn.disabled = historyOffset >= data.total;
    }

    async function selectProject(id) {
        try {
            const res = await apiFetch(`/api/projects/${id}`);
            const project = await res.json();
            activeProjectId = project.id;
            currentProjectTitle.textContent = project.title;
            saveDocBtn.classList.remove("hidden");
            mainEditor.value = project.documents?.[0]?.content || "";
            if (project.guided_state) {
                currentGuidedStage = project.guided_state.current_stage || "idea";
                accumulatedContent = project.guided_state.accumulated_content || "";
            } else {
                currentGuidedStage = "idea";
                accumulatedContent = "";
            }
            canAdvanceStage = false;
            renderEmptyResult("Proyecto seleccionado. Puedes escribir ahora.");
            await loadInteractionHistory(true);
            await loadProjects();
            saveStatus.textContent = "";
            updateGuidedUI();
        } catch (e) {
            showToast(`No se pudo abrir el proyecto: ${e.message}`, "error");
        }
    }

    async function deleteProject(id) {
        if (!confirm("¿Estás seguro de que quieres eliminar este proyecto para siempre?")) return;
        try {
            await apiFetch(`/api/projects/${id}`, { method: "DELETE" });
            if (activeProjectId === id) {
                activeProjectId = null;
                currentProjectTitle.textContent = "Documento efímero (Sin proyecto)";
                mainEditor.value = "";
                renderEmptyResult("Proyecto eliminado.");
                saveDocBtn.classList.add("hidden");
                historyPanel.classList.add("hidden");
                saveStatus.textContent = "";
            }
            await loadProjects();
        } catch (e) {
            showToast(`Error al eliminar: ${e.message}`, "error");
        }
    }

    async function saveActiveDocument() {
        if (!activeProjectId) return;
        saveStatus.textContent = "Guardando...";
        try {
            await apiFetch(`/api/projects/${activeProjectId}/document`, {
                method: "PUT",
                body: JSON.stringify({ content: mainEditor.value }),
            });
            saveStatus.textContent = "Guardado";
            setTimeout(() => {
                if (saveStatus.textContent === "Guardado") saveStatus.textContent = "";
            }, 2000);
        } catch (e) {
            saveStatus.textContent = "Error al guardar";
            showToast(e.message, "error");
        }
    }

    async function processText() {
        const draftText = mainEditor.value.trim();
        const instructionText = oracleInstruction.value.trim();
        if (!draftText && !instructionText) {
            showToast("No hay contenido para procesar.", "error");
            return;
        }
        if (currentMode === "guia" && !activeProjectId) {
            showToast("Debes seleccionar un proyecto para usar modo guía.", "error");
            return;
        }

        processBtn.classList.add("hidden");
        loadingDiv.classList.remove("hidden");
        resultsContent.style.opacity = 0.5;
        if (activeProjectId) await saveActiveDocument();

        let endpoint = "/api/chat";
        let payload;
        if (currentMode === "guia") {
            endpoint = "/api/guided-mode";
            payload = {
                project_id: activeProjectId,
                user_input: instructionText || draftText,
                current_stage: currentGuidedStage,
                accumulated_content: accumulatedContent,
                draft_content: draftText,
            };
        } else {
            payload = {
                messages: [{ role: "user", content: instructionText || draftText }],
                modo: currentMode,
                estilo_seleccionado: currentMode === "estilo" ? styleSelect.value : null,
                project_id: activeProjectId,
                draft_content: draftText,
                oracle_prompt: instructionText,
            };
        }

        try {
            const response = await apiFetch(endpoint, {
                method: "POST",
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            renderMarkdownSafe(data.response);
            if (currentMode === "guia") {
                currentGuidedStage = data.current_stage;
                accumulatedContent = data.accumulated_content;
                canAdvanceStage = Boolean(data.can_advance);
                updateGuidedUI();
            }
            if (activeProjectId) await loadInteractionHistory(true);
        } catch (error) {
            resultsContent.innerHTML = `<div style="color: var(--danger); font-weight: 500;">X ${error.message}</div>`;
            showToast(error.message, "error");
        } finally {
            resultsContent.style.opacity = 1;
            processBtn.classList.remove("hidden");
            loadingDiv.classList.add("hidden");
        }
    }

    ensureClientIdentity();
    loadProjects();
    fontSizeControl.addEventListener("input", () => {
        mainEditor.style.fontSize = `${fontSizeControl.value}px`;
    });
    lineHeightControl.addEventListener("input", () => {
        mainEditor.style.lineHeight = lineHeightControl.value;
    });
    processBtn.addEventListener("click", processText);
    historyMoreBtn.addEventListener("click", () => loadInteractionHistory(false));
    saveDocBtn.addEventListener("click", saveActiveDocument);

    modeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const selectedMode = btn.getAttribute("data-mode");
            if (selectedMode === "guia" && !activeProjectId) {
                showToast("Crea o selecciona un proyecto para Modo Guía.", "error");
                return;
            }
            setModeVisual(selectedMode);
        });
    });

    guidedNextBtn.addEventListener("click", async () => {
        if (!canAdvanceStage) {
            showToast("Primero procesa esta fase con suficiente contenido.", "error");
            return;
        }
        const idx = GUIDED_STAGES.indexOf(currentGuidedStage);
        if (idx < GUIDED_STAGES.length - 1) {
            currentGuidedStage = GUIDED_STAGES[idx + 1];
            canAdvanceStage = false;
            if (currentGuidedStage === "completado") {
                mainEditor.value = accumulatedContent;
                await saveActiveDocument();
                showToast("Ensayo completado y guardado.");
            } else {
                mainEditor.value = "";
            }
            updateGuidedUI();
        }
    });

    mainEditor.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") processText();
    });
    mainEditor.addEventListener("input", () => {
        if (!activeProjectId) return;
        saveStatus.textContent = "Modificado...";
        clearTimeout(typingTimer);
        typingTimer = setTimeout(saveActiveDocument, 2000);
    });

    newProjectBtn.addEventListener("click", () => {
        modalOverlay.classList.remove("hidden");
        newProjectModal.classList.remove("hidden");
        newProjectTitleInput.value = "";
        newProjectTitleInput.focus();
    });
    modalCancelBtn.addEventListener("click", closeModal);
    modalOverlay.addEventListener("click", closeModal);
    newProjectTitleInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") modalCreateBtn.click();
        if (e.key === "Escape") closeModal();
    });
    modalCreateBtn.addEventListener("click", async () => {
        const title = newProjectTitleInput.value.trim();
        if (!title) return;
        try {
            const res = await apiFetch("/api/projects", {
                method: "POST",
                body: JSON.stringify({ title }),
            });
            const project = await res.json();
            await loadProjects();
            await selectProject(project.id);
            closeModal();
            showToast("Proyecto creado.");
        } catch (e) {
            showToast(`Error creando proyecto: ${e.message}`, "error");
        }
    });
});
