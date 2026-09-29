document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("projectsSearch");
    const filterSelect = document.getElementById("projectsFilter");
    const projectCards = document.querySelectorAll(".project-card");
    const emptyMessage = document.getElementById("projectsEmptyMessage");
    const progressBar = document.getElementById("projectsProgressBar");
    const progressText = document.getElementById("projectsProgressText");
    function filterProjects() {
        const searchText = searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";

        const selectedCategory = filterSelect
            ? filterSelect.value.toLowerCase()
            : "all";
        let visibleProjects = 0;

        projectCards.forEach(card => {
            const title = card.querySelector("h2")
                    ?.textContent
                    .toLowerCase()
                    .trim() || "";

            const description = card.querySelector("p")
                    ?.textContent
                    .toLowerCase()
                    .trim() || "";

            const category = card.dataset.category
                    ?.toLowerCase()
                    .trim() || "";

            const matchesSearch = title.includes(searchText) ||
                description.includes(searchText);

            const matchesCategory = selectedCategory === "all" ||
                category === selectedCategory;

            if (matchesSearch && matchesCategory) {
                card.classList.remove("hidden");
                visibleProjects++;
            } else {
                card.classList.add("hidden");
            }
        });

        if (emptyMessage) {
            if (visibleProjects === 0) {
                emptyMessage.classList.remove("hidden");
            } else {
                emptyMessage.classList.add("hidden");
            }
        }
    }

    function updateProjectProgress() {
        if (!projectCards.length) {
            if (progressBar) { progressBar.style.width = "0%"; }
            if (progressText) { progressText.textContent = "0% Completed"; }
            return;
        }

        let totalProgress = 0;
        projectCards.forEach(card => {
            const progressElement = card.querySelector( "[data-project-progress]" );
            if (progressElement) {

                const progress = parseInt(
                        progressElement.dataset.projectProgress || "0",
                        10
                    );
                totalProgress += progress;
            } else {
                const text = card.textContent || "";
                const match = text.match(/(\d+)%/);
                if (match) { totalProgress += parseInt(match[1], 10); }
            }
        });

        const averageProgress = Math.round( totalProgress / projectCards.length );
        if (progressBar) { progressBar.style.width = `${averageProgress}%`; }
        if (progressText) { progressText.textContent = `${averageProgress}% Completed`; }
    }

        async function startProject(projectId, button) {
            if (!projectId) {
                alert("Project ID is missing.");
                return;
            }

            if (button) {
                button.disabled = true;
                button.textContent = "Starting...";
            }

            try {
                const response = await fetch("/api/projects/start", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({project_id: projectId})
                });

                const contentType = response.headers.get("content-type") || "";

                if (!contentType.includes("application/json")) {
                    const text = await response.text();
                    console.error("Invalid server response:", text);

                    throw new Error(
                        "Server returned an invalid response. Please check the Flask terminal."
                    );
                }

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(
                        data.message || "Unable to start project."
                    );
                }

                const card = document
                    .querySelector(`[data-project-id="${projectId}"]`)
                    ?.closest(".project-card");

                const updatedProgress = Number(
                    data.progress ?? 10
                );

                if (card) {
                    const progressElement = card.querySelector(
                        "[data-project-progress]"
                    );

                    if (progressElement) {
                        progressElement.dataset.projectProgress =
                            updatedProgress;

                        progressElement.textContent =
                            `${updatedProgress}%`;
                    }

                    const progressBarElement = card.querySelector(
                        "[data-project-progress-bar]"
                    );

                    if (progressBarElement) {
                        progressBarElement.style.width =
                            `${updatedProgress}%`;
                    }
                }

                if (button) {
                    button.disabled = false;
                    button.textContent = "Continue Project";
                }

                updateProjectProgress();

            } catch (error) {
                console.error("START PROJECT ERROR:", error);

                alert(
                    error.message ||
                    "Unable to start project."
                );

                if (button) {
                    button.disabled = false;
                    button.textContent = "Start Project";
                }
            }
        }

        async function completeProject(projectId, button) {
            if (!projectId) {
                alert("Project ID is missing.");
                return;
            }

            if (button) {
                button.disabled = true;
                button.textContent = "Completing...";
            }

            try {
                const response = await fetch("/api/projects/complete", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        project_id: projectId
                    })
                });

                const contentType =
                    response.headers.get("content-type") || "";

                if (!contentType.includes("application/json")) {
                    const text = await response.text();
                    console.error("Invalid server response:", text);

                    throw new Error(
                        "Server returned an invalid response. Please check the Flask terminal."
                    );
                }

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(
                        data.message || "Unable to complete project."
                    );
                }

                const card = document
                    .querySelector(`[data-project-id="${projectId}"]`)
                    ?.closest(".project-card");

                const updatedProgress = Number(
                    data.progress ?? 100
                );

                if (card) {
                    const progressElement = card.querySelector(
                        "[data-project-progress]"
                    );

                    if (progressElement) {
                        progressElement.dataset.projectProgress =
                            updatedProgress;

                        progressElement.textContent =
                            `${updatedProgress}%`;
                    }

                    const progressBarElement = card.querySelector(
                        "[data-project-progress-bar]"
                    );

                    if (progressBarElement) {
                        progressBarElement.style.width =
                            `${updatedProgress}%`;
                    }
                }

                if (button) {
                    button.disabled = true;
                    button.textContent = "Completed";
                }

                updateProjectProgress();

            } catch (error) {
                console.error("COMPLETE PROJECT ERROR:", error);

                alert(
                    error.message ||
                    "Unable to complete project."
                );

                if (button) {
                    button.disabled = false;
                    button.textContent = "Continue Project";
                }
            }
        }

    document.addEventListener( "click", event => {
            const projectButton = event.target.closest( "[data-project-button]" );
            if (!projectButton) { return; }
            const projectId = projectButton.dataset.projectId;
            if (!projectId) { alert("Project ID is missing."); return; }
            const isCompleted = projectButton.textContent .toLowerCase() .includes("completed");
            const isStarted = projectButton.textContent .toLowerCase() .includes("continue");
            if (isCompleted) { return; }
            if (isStarted) { completeProject( projectId, projectButton ); return; }
            startProject( projectId, projectButton );
        }
    );

    if (searchInput) { searchInput.addEventListener( "input", filterProjects ); }
    if (filterSelect) { filterSelect.addEventListener( "change", filterProjects ); }
    filterProjects();
    updateProjectProgress();

});