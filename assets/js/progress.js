document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.getElementById("studentMenuButton");
    const mobileSidebar = document.getElementById("studentMobileSidebar");
    const overlay = document.getElementById("studentSidebarOverlay");
    function openSidebar() {
        if (!mobileSidebar || !overlay) return;
        mobileSidebar.classList.remove("hidden");
        overlay.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");
    }

    function closeSidebar() {
        if (!mobileSidebar || !overlay) return;
        mobileSidebar.classList.add("hidden");
        overlay.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
    }

    if (menuButton) {
        menuButton.addEventListener("click", openSidebar);
    }

    if (overlay) {
        overlay.addEventListener("click", closeSidebar);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeSidebar();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth >= 1024) {
            closeSidebar();
        }
    });
});

    const overallProgressText = document.getElementById("overallProgressText");
    const overallProgressCircle = document.getElementById("overallProgressCircle");
    const overallProgressBar = document.getElementById("overallProgressBar");
    const roadmapProgressValue = document.getElementById("roadmapProgressValue");
    const roadmapProgressBar = document.getElementById("roadmapProgressBar");
    const skillsProgressValue = document.getElementById("skillsProgressValue");
    const skillsProgressBar = document.getElementById("skillsProgressBar");
    const coursesProgressValue = document.getElementById("coursesProgressValue");
    const coursesProgressBar = document.getElementById("coursesProgressBar");
    const projectsProgressValue = document.getElementById("projectsProgressValue");
    const projectsProgressBar = document.getElementById("projectsProgressBar");
    const roadmapProgress = Number("{{ progress.roadmap_progress }}");
    const skillsProgress = Number("{{ progress.skill_progress }}");
    const coursesProgress = Number("{{ progress.course_progress }}");
    const projectsProgress = Number("{{ progress.project_progress }}");
    const overallProgress = Number("{{ progress.overall_progress }}");
    function updateProgress(textElement, barElement, percentage) {
        percentage = Math.max(0, Math.min(100, percentage));
        if (textElement) {textElement.textContent = `${percentage}%`;}
        if (barElement) {barElement.style.width = `${percentage}%`;}
    }

    updateProgress(
        roadmapProgressValue,
        roadmapProgressBar,
        roadmapProgress
    );

    updateProgress(
        skillsProgressValue,
        skillsProgressBar,
        skillsProgress
    );

    updateProgress(
        coursesProgressValue,
        coursesProgressBar,
        coursesProgress
    );

    updateProgress(
        projectsProgressValue,
        projectsProgressBar,
        projectsProgress
    );

    if (overallProgressText) {overallProgressText.textContent = `${overallProgress}%`;}
    if (overallProgressCircle) {overallProgressCircle.textContent = `${overallProgress}%`;}
    if (overallProgressBar) {overallProgressBar.style.width = `${overallProgress}%`;}
});