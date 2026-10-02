document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("roadmapSearch");
    const filterSelect = document.getElementById("roadmapFilter");
    const roadmapSteps = document.getElementById("roadmapSteps");
    const emptyMessage = document.getElementById("roadmapEmptyMessage");
    const progressText = document.getElementById("roadmapProgressText");
    const progressBar = document.getElementById("roadmapProgressBar");

    let currentRoadmap = [];
    let completedSteps = [];
    let startedSteps = [];

    if (!roadmapSteps) {
        console.error("roadmapSteps element not found.");
        return;
    }

    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = String(value ?? "");
        return div.innerHTML;
    }

    async function loadRoadmap() {
        try {
            const response = await fetch("/api/roadmap", {
                    method: "GET",
                    headers: {"Accept": "application/json"}
                });

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                const text = await response.text();
                console.error("INVALID ROADMAP RESPONSE:", text);
                throw new Error("Server returned an invalid response. Please check the Flask terminal.");
            }

            const data = await response.json();
            console.log("ROADMAP API RESPONSE:", data);
            if (!response.ok) {throw new Error(data.message || "Unable to load roadmap.");}
            if (Array.isArray(data.roadmap)) {currentRoadmap = data.roadmap;
            } else {
                currentRoadmap = [];
            }

            if (Array.isArray(data.completed_steps)) {
                completedSteps = data.completed_steps.map(String);
            } else if (
                Array.isArray(data.completedSteps)
            ) {
                completedSteps = data.completedSteps.map(String);
            } else {
                completedSteps = [];
            }

            if (Array.isArray(data.started_steps)) {
                startedSteps = data.started_steps.map(String);
            } else if (
                Array.isArray(data.startedSteps)
            ) {
                startedSteps = data.startedSteps.map(String);
            } else {
                startedSteps = [];
            }

            currentRoadmap = currentRoadmap.map(function (step) {
                    return {
                        ...step,
                        id: String(
                            step.id ??
                            step.step_id ??
                            ""
                        )
                    };
                });
            renderRoadmap(currentRoadmap);
            openRequestedStep();
        } catch (error) {
            console.error("Roadmap loading error:", error);
            currentRoadmap = [];
            completedSteps = [];
            startedSteps = [];
            roadmapSteps.innerHTML = "";
            if (emptyMessage) {emptyMessage.classList.remove("hidden");
                emptyMessage.textContent = "Unable to load roadmap. Please try again.";}
            updateProgress();
        }
    }

    function updateProgress() {
        const totalSteps = currentRoadmap.length;
        if (totalSteps === 0) {
            if (progressText) {progressText.textContent = "0% Completed";}
            if (progressBar) {progressBar.style.width = "0%";}
            return;
        }

        const completedCount = currentRoadmap.filter(function (step) {
                return completedSteps.includes(String(step.id));}).length;
        const percentage =Math.round((completedCount / totalSteps) * 100);
        if (progressText) {progressText.textContent = `${percentage}% Completed`;}
        if (progressBar) {progressBar.style.width = `${percentage}%`;}
    }

    function renderRoadmap(roadmap) {
        currentRoadmap =
            Array.isArray(roadmap)
                ? roadmap
                : [];
        roadmapSteps.innerHTML = "";
        if (currentRoadmap.length === 0) {
            if (emptyMessage) {emptyMessage.classList.remove("hidden");
                emptyMessage.textContent ="No roadmap steps available yet.";}
            updateProgress();
            return;
        }

        if (emptyMessage) {emptyMessage.classList.add("hidden");}
        currentRoadmap.forEach(
            function (step, index) {
                const stepId =
                    String(
                        step.id ??
                        step.step_id ??
                        ""
                    );

                const isCompleted = completedSteps.includes(stepId);
                const isStarted = startedSteps.includes(stepId);
                const article = document.createElement("article");
                article.dataset.roadmapStep = stepId;
                article.dataset.category = step.category || "General";
                article.className = "rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:shadow-md";

                let learningHTML = "";
                if (isStarted) {
                    let whatToLearnHTML = "";
                    if (
                        Array.isArray(step.what_to_learn) &&
                        step.what_to_learn.length > 0
                    ) {
                        whatToLearnHTML = `
                            <div class="mb-6">
                                <h4 class="mb-3 text-sm font-bold text-slate-900">
                                    📚 What to Learn
                                </h4>

                                <ul class="space-y-2">
                                    ${step.what_to_learn
                                        .map(function (item) {
                                            return `
                                                <li class="flex gap-2 text-sm text-slate-600">
                                                    <span class="text-emerald-600">
                                                        ✓
                                                    </span>

                                                    <span>
                                                        ${escapeHtml(item)}
                                                    </span>
                                                </li>
                                            `;
                                        })
                                        .join("")
                                    }
                                </ul>
                            </div>
                        `;
                    } else {
                        whatToLearnHTML = `
                            <div class="mb-6">
                                <h4 class="mb-2 text-sm font-bold text-slate-900">
                                    📚 What to Learn
                                </h4>

                                <p class="text-sm text-slate-500">
                                    Learn the concepts described in this roadmap step and practice them with small exercises.
                                </p>
                            </div>
                        `;
                    }
                    let resourcesHTML = "";
                    if (
                        Array.isArray(step.resources) &&
                        step.resources.length > 0
                    ) {
                        resourcesHTML = `
                            <div>
                                <h4 class="mb-3 text-sm font-bold text-slate-900">
                                    🔗 Study Material
                                </h4>

                                <div class="space-y-3">
                                    ${step.resources
                                        .map(function (resource) {
                                            const url =
                                                resource &&
                                                resource.url
                                                    ? resource.url
                                                    : "#";

                                            const title =
                                                resource &&
                                                resource.title
                                                    ? resource.title
                                                    : "Learning Resource";

                                            if (url === "#") {
                                                return `
                                                    <div class="block rounded-xl border border-slate-200 bg-white p-4">
                                                        <div class="font-semibold text-slate-900">
                                                            ${escapeHtml(title)}
                                                        </div>

                                                        <div class="mt-1 text-xs text-slate-500">
                                                            Study material link is not available.
                                                        </div>
                                                    </div>
                                                `;
                                            }
                                            return `
                                                <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer"
                                                    class="block rounded-xl border border-slate-200 bg-white p-4 transition hover:border-indigo-200 hover:shadow-sm">

                                                    <div class="font-semibold text-slate-900">
                                                        ${escapeHtml(title)}
                                                    </div>

                                                    <div class="mt-1 text-xs text-indigo-600">
                                                        Open Study Material →
                                                    </div>
                                                </a>
                                            `;
                                        })
                                        .join("")
                                    }
                                </div>
                            </div>
                        `;
                    } else {
                        resourcesHTML = `
                            <div>
                                <h4 class="mb-2 text-sm font-bold text-slate-900">
                                    🔗 Study Material
                                </h4>

                                <p class="text-sm text-slate-500">
                                    Study material is not available for this topic yet.
                                </p>
                            </div>
                        `;
                    }

                    let completeHTML = "";
                    if (isCompleted) {
                        completeHTML = `
                            <div class="mt-6">
                                <div class="inline-flex rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white">
                                    ✓ Completed
                                </div>
                            </div>
                        `;
                    } else {
                        completeHTML = `
                            <div class="mt-6">
                                <button type="button" data-complete-step data-step-id="${escapeHtml(stepId)}"
                                    class="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700">
                                    Mark as Complete
                                </button>
                            </div>
                        `;
                    }

                    learningHTML = `
                        <div data-learning-content class="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                            ${whatToLearnHTML}
                            ${resourcesHTML}
                            ${completeHTML}
                        </div>
                    `;
                }

                let actionButton = "";
                if (isCompleted) {
                    actionButton = `
                        <button type="button" disabled class="rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white">
                            ✓ Completed
                        </button>
                    `;
                } else if (isStarted) {
                    actionButton = `
                        <button type="button" data-start-learn data-step-id="${escapeHtml(stepId)}"
                            class="rounded-xl bg-slate-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800">
                            Continue Learning
                        </button>
                    `;
                } else {
                    actionButton = `
                        <button type="button" data-start-learn data-step-id="${escapeHtml(stepId)}"
                            class="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700">
                            Start to Learn
                        </button>
                    `;
                }
                article.innerHTML = `
                    <div class="flex flex-col gap-5 sm:flex-row sm:items-start">
                        <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-lg font-bold text-indigo-700">
                            ${index + 1}
                        </div>

                        <div class="flex-1">
                            <div class="mb-2 flex flex-wrap items-center gap-2">
                                <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-600">
                                    ${escapeHtml(step.category ||"General")}
                                </span>
                                ${
                                    index === currentRoadmap.length - 1
                                        ? `
                                            <span class="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                                                Final Step
                                            </span>
                                        `
                                        : ""
                                }
                            </div>

                            <h3 class="text-xl font-bold text-slate-900">
                                ${escapeHtml(step.title || `Step ${index + 1}`)}
                            </h3>

                            <p class="mt-2 text-sm leading-6 text-slate-500">
                                ${escapeHtml(step.description || "Learn and practice this career skill.")}
                            </p>
                            ${learningHTML}

                            <div class="mt-5">
                                ${actionButton}
                            </div>
                        </div>
                    </div>
                `;
                roadmapSteps.appendChild(article);
            }
        );
        updateProgress();
        filterRoadmap();
    }

    async function startLearning(stepId, button) 
    {
        try {
            button.disabled = true;
            button.textContent = "Starting...";
            const response = await fetch(
                    "/api/roadmap/start",
                    {
                        method: "POST",
                        headers: {"Content-Type": "application/json",
                            "Accept": "application/json"
                        },

                        body: JSON.stringify({step_id: stepId})
                    }
                );

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes( "application/json"))     
            {const text = await response.text();
                console.error("INVALID START RESPONSE:", text);
                throw new Error("Server returned an invalid response. Please check the Flask terminal.");
            }

            const data = await response.json();
            console.log("START RESPONSE:", data);
            if (!response.ok || !data.success) 
            {
                throw new Error(data.message || "Unable to start this topic.");
            }
            if (
                !startedSteps.includes(String(stepId))) 
            {
                startedSteps.push(String(stepId));
            }

            const currentStep = currentRoadmap.find(
                    function (step) {return String(step.id) === String(stepId);}
                );
            if (
                currentStep &&
                Array.isArray(currentStep.resources) &&
                currentStep.resources.length > 0
            )
            
            {
                const firstResource = currentStep.resources[0];
                if (firstResource && firstResource.url) 
                {
                    window.open(firstResource.url, "_blank");
                }
            }

            renderRoadmap(currentRoadmap);
        } catch (error) {
            console.error("Start learning error:", error);
            button.disabled = false;
            button.textContent = "Start to Learn";
            alert(error.message || "Something went wrong while starting this topic.");
        }
    }

    async function completeStep(stepId, button) 
    {
        try {
            button.disabled = true;
            button.textContent = "Saving...";
            const response = await fetch("/api/roadmap/complete",
                    {
                        method: "POST",
                        headers: {"Content-Type": "application/json",
                            "Accept": "application/json"
                        },

                        body: JSON.stringify({step_id: stepId})
                    }
                );

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) 
            {
                const text = await response.text();
                console.error("INVALID COMPLETE RESPONSE:", text);
                throw new Error("Server returned an invalid response. Please check the Flask terminal.");
            }

            const data = await response.json();
            console.log("COMPLETE RESPONSE:", data);
            if (!response.ok || !data.success) 
            {throw new Error(data.message || "Unable to complete this topic.");}
            if (!completedSteps.includes(String(stepId))) 
            {completedSteps.push(String(stepId));}
            if (!startedSteps.includes(String(stepId))) 
            {startedSteps.push(String(stepId));}
            renderRoadmap(currentRoadmap);
        } catch (error) {
            console.error("Complete step error:", error);
            button.disabled = false;
            button.textContent = "Mark as Complete";
            alert(error.message || "Something went wrong while completing this topic.");
        }
    }

    function filterRoadmap() {
        const searchTerm = (searchInput?.value || "")
                .trim()
                .toLowerCase();
        const category = (filterSelect?.value || "all")
                .trim()
                .toLowerCase();
        const cards = roadmapSteps.querySelectorAll("[data-roadmap-step]");
        let visibleCount = 0;
        cards.forEach(
            function (card) {
                const text = card.textContent.toLowerCase();
                const cardCategory = (card.dataset.category || "")
                        .toLowerCase();
                const matchesSearch = !searchTerm || text.includes(searchTerm);
                const matchesCategory = category === "all" || cardCategory === category;
                if (matchesSearch && matchesCategory) 
                {
                    card.classList.remove("hidden");
                    visibleCount++;
                } else {
                    card.classList.add("hidden");
                }
            }
        );

        if (cards.length > 0 && visibleCount === 0) 
        {
            if (emptyMessage) {
                emptyMessage.classList.remove("hidden");
                emptyMessage.textContent = "No roadmap steps match your search.";
            }
        } else if (cards.length > 0) 
        {
            if (emptyMessage) {emptyMessage.classList.add("hidden");}
        }
    }

    async function generateAIRoadmap(career) 
    {
        career = String(career || "").trim();
        if (!career) {
            alert("Please enter a career name.");
            return;
        }
        roadmapSteps.innerHTML = `
            <div class="rounded-2xl border border-indigo-100 bg-white p-8 text-center shadow-sm">
                <div class="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-indigo-600"></div>
                <h3 class="text-lg font-bold text-slate-900">
                    Creating your roadmap...
                </h3>

                <p class="mt-2 text-sm text-slate-500">
                    Generating a roadmap for
                    <strong>
                        ${escapeHtml(career)}
                    </strong>.
                </p>
            </div>
        `;

        if (emptyMessage) {emptyMessage.classList.add("hidden");}
        try {
            const response = await fetch(
                    "/api/roadmap/generate",
                    {
                        method: "POST",
                        headers: {"Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        body: JSON.stringify({career: career})
                    }
                );

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) 
            {
                const text = await response.text();
                console.error("INVALID GENERATE RESPONSE:", text);
                throw new Error("Server returned an invalid response. Please check the Flask terminal.");
            }

            const data = await response.json();
            console.log("GENERATE RESPONSE:", data);
            if (!response.ok || !data.success) 
            {
                throw new Error(data.message || "Unable to generate roadmap.");
            }
            if (Array.isArray(data.roadmap)) 
            {
                renderRoadmap(data.roadmap);
            } else {
                throw new Error("Roadmap data was not returned by the server.");
            }
        } catch (error) {
            console.error("AI roadmap error:", error);
            roadmapSteps.innerHTML = "";
            if (emptyMessage) {
                emptyMessage.classList.remove("hidden");
                emptyMessage.textContent ="Unable to generate roadmap.";
            }
            alert(error.message || "Unable to generate roadmap right now.");
        }
    }

    if (searchInput) {
        searchInput.addEventListener("keydown",
            function (event) {
                if (event.key === "Enter") 
                {
                    event.preventDefault();
                    const career = searchInput.value.trim();
                    if (career) {generateAIRoadmap(career);}
                }
            }
        );
    }

    if (filterSelect) {filterSelect.addEventListener("change",filterRoadmap);}
    roadmapSteps.addEventListener("click",
        function (event) {
            const startButton = event.target.closest("[data-start-learn]");
            if (startButton) {
                const stepId = startButton.dataset.stepId;
                if (!stepId) {
                    alert("Step ID is missing.");
                    return;
                }

                const article = startButton.closest("[data-roadmap-step]");
                const learningContent = article?.querySelector("[data-learning-content]");
                if (startedSteps.includes(String(stepId))) 
                {
                    if (learningContent) {learningContent.classList.toggle("hidden");}
                    return;
                }
                startLearning(stepId, startButton);
                return;
            }

            const completeButton = event.target.closest("[data-complete-step]");
            if (completeButton) {
                const stepId = completeButton.dataset.stepId;
                if (!stepId) {
                    alert("Step ID is missing.");
                    return;
                }
                completeStep(stepId, completeButton);
            }
        }
    );

    function openRequestedStep() {
        const params = new URLSearchParams(window.location.search);
        const requestedStepId = params.get("step");
        if (!requestedStepId) {
            return;
        }

        const article = document.querySelector(`[data-roadmap-step="${CSS.escape(requestedStepId)}"]`);
        if (!article) {
            return;
        }

        const learningContent = article.querySelector("[data-learning-content]");
        const startButton = article.querySelector("[data-start-learn]");
        if (learningContent) {learningContent.classList.remove("hidden");}
        if (startButton) {startButton.textContent ="Continue Learning";}
        setTimeout(
            function () {
                article.scrollIntoView({behavior: "smooth", block: "center"});
            },
            300
        );
    }
    loadRoadmap();
});