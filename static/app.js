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
    const settingsBtn = document.getElementById("settings-btn");
    const settingsMenu = document.getElementById("settings-menu");
    const projectsList = document.getElementById("projects-list");
    const newProjectBtn = document.getElementById("new-project-btn");
    const saveDocBtn = document.getElementById("save-doc-btn");
    const saveStatus = document.getElementById("save-status");
    const currentProjectTitle = document.getElementById("current-project-title");
    const guidedProgress = document.getElementById("guided-progress");
    const guidedPhaseBar = document.getElementById("guided-phase-bar");
    const guidedNextBtn = document.getElementById("guided-next-btn");
    const guidedNextTooltip = document.getElementById("guided-next-tooltip");
    const modalOverlay = document.getElementById("modal-overlay");
    const newProjectModal = document.getElementById("new-project-modal");
    const newProjectTitleInput = document.getElementById("new-project-title");
    const newProjectGoalInput = document.getElementById("new-project-goal");
    const newProjectInitialModeSelect = document.getElementById("new-project-initial-mode");
    const newProjectTemplateSelect = document.getElementById("new-project-template");
    const newProjectCounter = document.getElementById("new-project-counter");
    const newProjectError = document.getElementById("new-project-error");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const modalCreateBtn = document.getElementById("modal-create-btn");
    const modalFocusableSelector = "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex='-1'])";
    const projectOnboarding = document.getElementById("project-onboarding");
    const projectOnboardingText = document.getElementById("project-onboarding-text");
    const onboardingWriteThesisBtn = document.getElementById("onboarding-write-thesis");
    const onboardingGuidedModeBtn = document.getElementById("onboarding-guided-mode");
    const onboardingPasteDraftBtn = document.getElementById("onboarding-paste-draft");
    const phaseHintPanel = document.getElementById("phase-hint-panel");
    const phaseHintName = document.getElementById("phase-hint-name");
    const phaseHintDesc = document.getElementById("phase-hint-desc");
    const phaseHintReq = document.getElementById("phase-hint-req");
    const phaseExamplesList = document.getElementById("phase-examples-list");
    const tutorialOverlay = document.getElementById("tutorial-overlay");
    const tutorialNextBtn = document.getElementById("tutorial-next-btn");
    const tutorialSkipBtn = document.getElementById("tutorial-skip-btn");
    const helpBtn = document.getElementById("help-btn");
    const guidedNoProjectOverlay = document.getElementById("guided-no-project-overlay");
    const guidedNoProjectModal = document.getElementById("guided-no-project-modal");
    const gnpCancelBtn = document.getElementById("gnp-cancel-btn");
    const gnpCreateBtn = document.getElementById("gnp-create-btn");

    const GUIDED_STAGES = ["idea", "estructura", "introduccion", "desarrollo", "contraargumento", "conclusion", "completado"];
    const STAGE_LABELS = {
        idea: "Idea",
        estructura: "Estructura",
        introduccion: "Intro",
        desarrollo: "Desarrollo",
        contraargumento: "Contra",
        conclusion: "Conclusión",
        completado: "✓",
    };
    const API_TOKEN_KEY = "sysiphus_api_token";
    const USER_ID_KEY = "sysiphus_user_id";
    const TUTORIAL_SEEN_KEY = "sysiphus_tutorial_seen";

    // ── Phase hints data ──────────────────────────────────────────────────────
    const PHASE_HINTS = {
        idea: {
            name: "Fase: Idea",
            desc: "Explora y define la idea central de tu ensayo. No necesitas tenerla clara del todo — el Oráculo te ayudará a afinarla.",
            req: "⏳ Escribe tu idea y consulta al Oráculo para poder avanzar.",
            examples: [
                "Quiero escribir sobre si el libre albedrío existe realmente.",
                "Mi tesis es que la tecnología no nos hace más libres, sino más dependientes.",
                "Explórame la idea de que el sufrimiento tiene valor filosófico.",
            ],
        },
        estructura: {
            name: "Fase: Estructura",
            desc: "Define el esqueleto argumental de tu ensayo. ¿Qué argumentos vas a usar? ¿Cómo se conectan? El Oráculo te propondrá un esquema.",
            req: "⏳ Escribe un borrador de estructura y consulta al Oráculo.",
            examples: [
                "Ayúdame a crear un esquema con tesis, 3 argumentos y un contraargumento.",
                "¿Qué orden lógico deberían tener mis ideas para ser más convincentes?",
                "Propón una estructura de 5 partes para este argumento filosófico.",
            ],
        },
        introduccion: {
            name: "Fase: Introducción",
            desc: "Redacta la introducción de tu ensayo. Debe enganchar al lector, presentar el tema y enunciar tu tesis central.",
            req: "⏳ Escribe al menos 80 caracteres y consulta al Oráculo.",
            examples: [
                "Ayúdame a escribir una introducción que enganche desde la primera frase.",
                "Critica mi borrador de introducción y sugiere mejoras concretas.",
                "¿Mi tesis está suficientemente clara en esta introducción?",
            ],
        },
        desarrollo: {
            name: "Fase: Desarrollo",
            desc: "Desarrolla los argumentos principales de tu ensayo. Es el cuerpo del texto — aquí se construye tu razonamiento con evidencia y ejemplos.",
            req: "⏳ Escribe al menos 80 caracteres y consulta al Oráculo.",
            examples: [
                "Desarrolla este argumento con mayor profundidad y añade un ejemplo concreto.",
                "¿Falta algún paso lógico entre este argumento y el siguiente?",
                "Refuerza esta sección con una cita o referencia filosófica relevante.",
            ],
        },
        contraargumento: {
            name: "Fase: Contraargumento",
            desc: "Presenta la objeción más fuerte a tu tesis y respóndela. Un buen ensayo reconoce las posiciones contrarias y las refuta.",
            req: "⏳ Escribe al menos 80 caracteres y consulta al Oráculo.",
            examples: [
                "¿Cuál es la objeción más fuerte a mi argumento? Ayúdame a responderla.",
                "Genera el mejor contraargumento posible contra mi tesis.",
                "¿Mi respuesta al contraargumento es convincente o deja flancos abiertos?",
            ],
        },
        conclusion: {
            name: "Fase: Conclusión",
            desc: "Cierra el ensayo sintetizando tus argumentos y reafirmando tu tesis. Una buena conclusión deja al lector con algo en qué pensar.",
            req: "⏳ Escribe al menos 80 caracteres y consulta al Oráculo.",
            examples: [
                "Escribe una conclusión que sintetice el argumento sin repetir literalmente lo dicho.",
                "¿Mi conclusión deja una pregunta abierta o un giro interesante?",
                "Propón un cierre con una cita o imagen final que refuerce la tesis.",
            ],
        },
        completado: {
            name: "Ensayo completado ✓",
            desc: "Tu ensayo está completo. El texto acumulado ha sido guardado en el lienzo. Puedes seguir refinándolo con los modos Mejora, Crítica o Estilo.",
            req: "",
            examples: [],
        },
    };

    let currentMode = "ensayo";
    let activeProjectId = null;
    let typingTimer;
    let currentGuidedStage = "idea";
    let accumulatedContent = "";
    let canAdvanceStage = false;
    let historyOffset = 0;
    const historyLimit = 20;
    let lastFocusedElement = null;
    let tutorialCurrentSlide = 0;
    const TUTORIAL_TOTAL_SLIDES = 3;

    // ═══════════════════════════════════════════════════════════════════
    // TUTORIAL DE BIENVENIDA
    // ═══════════════════════════════════════════════════════════════════

    function showWelcomeTutorial() {
        tutorialCurrentSlide = 0;
        renderTutorialSlide(0);
        tutorialOverlay.classList.remove("hidden");
    }

    function closeWelcomeTutorial() {
        tutorialOverlay.classList.add("hidden");
        localStorage.setItem(TUTORIAL_SEEN_KEY, "1");
    }

    function renderTutorialSlide(index) {
        const slides = tutorialOverlay.querySelectorAll(".tutorial-slide");
        const dots = tutorialOverlay.querySelectorAll(".tutorial-dot");
        slides.forEach((s, i) => s.classList.toggle("active", i === index));
        dots.forEach((d, i) => d.classList.toggle("active", i === index));
        const isLast = index === TUTORIAL_TOTAL_SLIDES - 1;
        tutorialNextBtn.textContent = isLast ? "¡Empezar! 🚀" : "Siguiente →";
    }

    tutorialNextBtn.addEventListener("click", () => {
        if (tutorialCurrentSlide < TUTORIAL_TOTAL_SLIDES - 1) {
            tutorialCurrentSlide++;
            renderTutorialSlide(tutorialCurrentSlide);
        } else {
            closeWelcomeTutorial();
        }
    });

    tutorialSkipBtn.addEventListener("click", closeWelcomeTutorial);

    helpBtn.addEventListener("click", () => {
        tutorialCurrentSlide = 0;
        renderTutorialSlide(0);
        tutorialOverlay.classList.remove("hidden");
    });

    function showGuidedNoProjectModal() {
        guidedNoProjectOverlay.classList.remove("hidden");
        guidedNoProjectModal.classList.remove("hidden");
        gnpCreateBtn.focus();
    }

    function closeGuidedNoProjectModal() {
        guidedNoProjectOverlay.classList.add("hidden");
        guidedNoProjectModal.classList.add("hidden");
    }

    gnpCancelBtn.addEventListener("click", closeGuidedNoProjectModal);
    guidedNoProjectOverlay.addEventListener("click", closeGuidedNoProjectModal);
    gnpCreateBtn.addEventListener("click", () => {
        closeGuidedNoProjectModal();
        // Pre-select Modo Guia in the project creation modal
        openNewProjectModal();
        newProjectInitialModeSelect.value = "guia";
    });

    // Toggle del menú de ajustes
    if (settingsBtn && settingsMenu) {
        settingsBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            settingsMenu.classList.toggle("hidden");
        });
        
        // Cerrar menú al hacer clic fuera
        document.addEventListener("click", (e) => {
            if (!settingsMenu.contains(e.target) && !settingsBtn.contains(e.target)) {
                settingsMenu.classList.add("hidden");
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════
    // AUTH / IDENTITY
    // ═══════════════════════════════════════════════════════════════════

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
            "Authorization": "Bearer " + (localStorage.getItem(API_TOKEN_KEY) || ""),
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

    // ═══════════════════════════════════════════════════════════════════
    // UI HELPERS
    // ═══════════════════════════════════════════════════════════════════

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
        newProjectTitleInput.removeAttribute("aria-invalid");
        if (lastFocusedElement && typeof lastFocusedElement.focus === "function") {
            lastFocusedElement.focus();
        }
    }

    function showProjectTitleError(message) {
        if (!message) {
            newProjectError.textContent = "";
            newProjectError.classList.add("hidden");
            newProjectTitleInput.setAttribute("aria-invalid", "false");
            return;
        }
        newProjectError.textContent = message;
        newProjectError.classList.remove("hidden");
        newProjectTitleInput.setAttribute("aria-invalid", "true");
    }

    function validateProjectTitle() {
        const rawTitle = newProjectTitleInput.value;
        const trimmedTitle = rawTitle.trim();
        const count = rawTitle.length;
        newProjectCounter.textContent = `${count}/120`;

        if (count === 0 || trimmedTitle.length === 0) {
            modalCreateBtn.disabled = true;
            showProjectTitleError("El título es obligatorio.");
            return false;
        }
        if (count > 120) {
            modalCreateBtn.disabled = true;
            showProjectTitleError("El título no puede superar 120 caracteres.");
            return false;
        }

        modalCreateBtn.disabled = false;
        showProjectTitleError("");
        return true;
    }

    function hideProjectOnboarding() {
        projectOnboarding.classList.add("hidden");
    }

    function showProjectOnboarding(projectTitle) {
        projectOnboardingText.textContent = `Proyecto "${projectTitle}" creado. Elige un primer paso:`;
        projectOnboarding.classList.remove("hidden");
    }

    // ═══════════════════════════════════════════════════════════════════
    // BARRA DE PROGRESO DE FASES
    // ═══════════════════════════════════════════════════════════════════

    function renderGuidedProgressBar(currentStage) {
        const currentIdx = GUIDED_STAGES.indexOf(currentStage);
        guidedPhaseBar.innerHTML = "";

        const track = document.createElement("div");
        track.className = "phase-bar-track";

        GUIDED_STAGES.forEach((stage, i) => {
            const step = document.createElement("div");
            step.className = "phase-step";

            if (i < currentIdx) step.classList.add("done");
            else if (i === currentIdx) step.classList.add("active");
            else step.classList.add("pending");

            const dot = document.createElement("div");
            dot.className = "phase-dot-btn";
            dot.textContent = i < currentIdx ? "✓" : "";

            const label = document.createElement("span");
            label.className = "phase-label";
            label.textContent = STAGE_LABELS[stage] || stage;

            step.appendChild(dot);
            step.appendChild(label);
            track.appendChild(step);
        });

        guidedPhaseBar.appendChild(track);
    }

    // ═══════════════════════════════════════════════════════════════════
    // PANEL DE AYUDA CONTEXTUAL POR FASE
    // ═══════════════════════════════════════════════════════════════════

    function renderPhaseHint(stage) {
        const hint = PHASE_HINTS[stage];
        if (!hint) return;

        phaseHintName.textContent = hint.name;
        phaseHintDesc.textContent = hint.desc;
        phaseHintReq.textContent = hint.req;

        // Render clickable examples
        phaseExamplesList.innerHTML = "";
        hint.examples.forEach(example => {
            const btn = document.createElement("button");
            btn.className = "phase-example-btn";
            btn.textContent = example;
            btn.addEventListener("click", () => {
                oracleInstruction.value = example;
                oracleInstruction.focus();
                showToast("Instrucción insertada — pulsa Ctrl+Enter para consultar.");
            });
            phaseExamplesList.appendChild(btn);
        });

        phaseHintPanel.classList.remove("hidden");
    }

    function hidePhaseHint() {
        phaseHintPanel.classList.add("hidden");
    }

    // ═══════════════════════════════════════════════════════════════════
    // GUIDED UI
    // ═══════════════════════════════════════════════════════════════════

    function updateGuidedUI() {
        if (activeProjectId && currentMode === "guia") {
            guidedProgress.classList.remove("hidden");
            renderGuidedProgressBar(currentGuidedStage);
            renderPhaseHint(currentGuidedStage);

            const isCompleted = currentGuidedStage === "completado";
            guidedNextBtn.classList.toggle("hidden", isCompleted);
            guidedNextBtn.disabled = !canAdvanceStage || isCompleted;

            // Update tooltip visibility based on can_advance
            if (guidedNextTooltip) {
                guidedNextTooltip.style.display = canAdvanceStage ? "none" : "";
            }

            const stageLabel = STAGE_LABELS[currentGuidedStage] || currentGuidedStage;
            mainEditor.placeholder = `Modo Guía — ${hint_for(currentGuidedStage)}\n\nRedacta aquí tu borrador para esta fase.`;
        } else {
            guidedProgress.classList.add("hidden");
            hidePhaseHint();
            mainEditor.placeholder = activeProjectId
                ? "Empieza con tu tesis o pega un borrador. Después usa Ctrl+Enter para consultarlo con el Oráculo."
                : "Plasma tu idea, premisa o borrador aquí. Selecciona o crea un proyecto para mantener tus reflexiones persistentes...";
        }
    }

    function hint_for(stage) {
        const h = PHASE_HINTS[stage];
        return h ? h.name : stage;
    }

    // ═══════════════════════════════════════════════════════════════════
    // TEMPLATES
    // ═══════════════════════════════════════════════════════════════════

    function getTemplateSetup(templateId, title, goal) {
        const goalLine = goal ? `\nObjetivo del proyecto: ${goal}\n` : "";
        if (templateId === "exploracion_socratica") {
            return {
                draft: `Pregunta central: ¿Qué idea quiero examinar a fondo?${goalLine}\nHipótesis inicial:\n- \n\nSupuestos que debo cuestionar:\n1. \n2. \n\nPosibles objeciones:\n- `,
                instruction: "Ayúdame a profundizar esta pregunta con una secuencia socrática en 5 pasos."
            };
        }
        if (templateId === "critica_texto") {
            return {
                draft: `Texto o tesis a criticar: ${title}${goalLine}\nResumen objetivo del texto:\n\nFortalezas argumentales:\n1. \n\nDebilidades argumentales:\n1. \n\nPropuesta de mejora:\n`,
                instruction: "Genera una crítica estructurada con tesis, evidencia, contraargumento y mejora concreta."
            };
        }
        if (templateId === "ensayo_argumentativo") {
            return {
                draft: `Tesis central:${goal ? ` ${goal}` : ""}\n\nArgumento 1:\n\nArgumento 2:\n\nContraargumento:\n\nConclusión provisional:\n`,
                instruction: "Ayúdame a convertir este esquema en un ensayo sólido y coherente."
            };
        }
        return {
            draft: goal ? `Objetivo del proyecto: ${goal}\n\n` : "",
            instruction: ""
        };
    }

    // ═══════════════════════════════════════════════════════════════════
    // MODAL DE NUEVO PROYECTO
    // ═══════════════════════════════════════════════════════════════════

    function openNewProjectModal() {
        lastFocusedElement = document.activeElement;
        modalOverlay.classList.remove("hidden");
        newProjectModal.classList.remove("hidden");
        newProjectTitleInput.value = "";
        newProjectGoalInput.value = "";
        newProjectInitialModeSelect.value = "ensayo";
        newProjectTemplateSelect.value = "ensayo_argumentativo";
        newProjectCounter.textContent = "0/120";
        showProjectTitleError("El título es obligatorio.");
        modalCreateBtn.disabled = true;
        newProjectTitleInput.focus();
    }

    function trapModalFocus(event) {
        if (newProjectModal.classList.contains("hidden")) return;
        if (event.key === "Escape") {
            event.preventDefault();
            closeModal();
            return;
        }
        if (event.key !== "Tab") return;

        const focusables = newProjectModal.querySelectorAll(modalFocusableSelector);
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }

    async function handleCreateProject() {
        if (!validateProjectTitle()) return;
        const title = newProjectTitleInput.value.trim();
        const goal = newProjectGoalInput.value.trim();
        const initialMode = newProjectInitialModeSelect.value;
        const templateId = newProjectTemplateSelect.value;
        const templateSetup = getTemplateSetup(templateId, title, goal);
        const originalText = modalCreateBtn.textContent;
        modalCreateBtn.disabled = true;
        modalCreateBtn.textContent = "Creando...";
        try {
            const res = await apiFetch("/api/projects", {
                method: "POST",
                body: JSON.stringify({ title }),
            });
            const project = await res.json();
            await loadProjects();
            await selectProject(project.id);
            setModeVisual(initialMode);
            mainEditor.value = templateSetup.draft;
            oracleInstruction.value = templateSetup.instruction;
            if (templateSetup.draft) {
                await saveActiveDocument();
            }
            renderEmptyResult("Proyecto listo. Usa un paso sugerido o escribe y presiona Ctrl+Enter.");
            showProjectOnboarding(project.title);
            closeModal();
            showToast("Proyecto creado.");
        } catch (e) {
            showToast(`Error creando proyecto: ${e.message}`, "error");
        } finally {
            modalCreateBtn.textContent = originalText;
            validateProjectTitle();
        }
    }

    function setModeVisual(modeId) {
        modeButtons.forEach(b => {
            b.classList.toggle("active", b.getAttribute("data-mode") === modeId);
        });
        currentMode = modeId;
        styleContainer.classList.toggle("hidden", currentMode !== "estilo");
        updateGuidedUI();
    }

    // ═══════════════════════════════════════════════════════════════════
    // PROYECTOS
    // ═══════════════════════════════════════════════════════════════════

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
            
            const timeStr = new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            el.innerHTML = `<span>🕒 ${item.mode.charAt(0).toUpperCase() + item.mode.slice(1)}</span> <span style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">${timeStr}</span>`;
            
            el.onclick = () => {
                if (el.classList.contains("viewing")) {
                    el.classList.remove("viewing");
                    renderEmptyResult("Historial cerrado. Escribe tu instrucción y consulta al Oráculo para continuar.");
                } else {
                    document.querySelectorAll(".history-item").forEach(i => i.classList.remove("viewing"));
                    el.classList.add("viewing");
                    renderMarkdownSafe(item.ai_output);
                    if (item.mode !== "guia") setModeVisual(item.mode);
                }
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
            hideProjectOnboarding();
            renderEmptyResult("Proyecto seleccionado. Escribe tu tesis o una instrucción y presiona Ctrl+Enter.");
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
                hideProjectOnboarding();
                renderEmptyResult("Proyecto eliminado. Crea uno nuevo para conservar contexto e historial.");
                saveDocBtn.classList.add("hidden");
                historyPanel.classList.add("hidden");
                saveStatus.textContent = "";
            }
            await loadProjects();
        } catch (e) {
            showToast(`Error al eliminar: ${e.message}`, "error");
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    // GUARDAR DOCUMENTO
    // ═══════════════════════════════════════════════════════════════════

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

    // ═══════════════════════════════════════════════════════════════════
    // PROCESAR — ORÁCULO
    // ═══════════════════════════════════════════════════════════════════

    async function processText() {
        const draftText = mainEditor.value.trim();
        const instructionText = oracleInstruction.value.trim();
        if (!draftText && !instructionText) {
            showToast("No hay contenido para procesar.", "error");
            return;
        }
        if (currentMode === "guia" && !activeProjectId) {
            showGuidedNoProjectModal();
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
                
                if (canAdvanceStage && currentGuidedStage !== "completado") {
                    const inlineBtn = document.createElement("button");
                    inlineBtn.className = "inline-advance-btn";
                    inlineBtn.innerHTML = "🌟 ¡Fase superada! Avanzar a la siguiente fase ➔";
                    inlineBtn.onclick = () => guidedNextBtn.click();
                    resultsContent.appendChild(inlineBtn);
                }
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

    // ═══════════════════════════════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════════════════════════════

    ensureClientIdentity();
    loadProjects();

    // Mostrar tutorial solo la primera vez
    if (!localStorage.getItem(TUTORIAL_SEEN_KEY)) {
        showWelcomeTutorial();
    }

    // ═══════════════════════════════════════════════════════════════════
    // EVENT LISTENERS
    // ═══════════════════════════════════════════════════════════════════

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
                showGuidedNoProjectModal();
                return;
            }
            setModeVisual(selectedMode);
        });
    });

    guidedNextBtn.addEventListener("click", async () => {
        if (!canAdvanceStage) {
            showToast("Primero consulta al Oráculo con suficiente contenido en el lienzo.", "error");
            return;
        }
        const idx = GUIDED_STAGES.indexOf(currentGuidedStage);
        if (idx < GUIDED_STAGES.length - 1) {
            currentGuidedStage = GUIDED_STAGES[idx + 1];
            canAdvanceStage = false;
            if (currentGuidedStage === "completado") {
                mainEditor.value = accumulatedContent;
                await saveActiveDocument();
                showToast("¡Ensayo completado y guardado! 🎉");
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

    newProjectBtn.addEventListener("click", openNewProjectModal);
    modalCancelBtn.addEventListener("click", closeModal);
    modalOverlay.addEventListener("click", closeModal);
    onboardingWriteThesisBtn.addEventListener("click", () => {
        if (!mainEditor.value.trim()) {
            mainEditor.value = "Tesis inicial: ";
        }
        mainEditor.focus();
        hideProjectOnboarding();
    });
    onboardingGuidedModeBtn.addEventListener("click", () => {
        if (!activeProjectId) return;
        setModeVisual("guia");
        if (!oracleInstruction.value.trim()) {
            oracleInstruction.value = "Guíame para construir la mejor tesis de este proyecto.";
        }
        oracleInstruction.focus();
        hideProjectOnboarding();
    });
    onboardingPasteDraftBtn.addEventListener("click", () => {
        setModeVisual("mejora");
        mainEditor.focus();
        hideProjectOnboarding();
    });
    newProjectModal.addEventListener("keydown", trapModalFocus);
    newProjectTitleInput.addEventListener("input", validateProjectTitle);
    newProjectTitleInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleCreateProject();
        }
        if (e.key === "Escape") closeModal();
    });
    modalCreateBtn.addEventListener("click", handleCreateProject);
});
