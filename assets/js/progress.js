document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.getElementById("studentMenuButton");
  const closeButton = document.getElementById("studentSidebarClose");
  const mobileSidebar = document.getElementById("studentMobileSidebar");
  const overlay = document.getElementById("studentSidebarOverlay");
  const overallProgressText = document.getElementById("overallProgressText");
  const overallProgressCircle = document.getElementById("overallProgressCircle",);
  const overallProgressBar = document.getElementById("overallProgressBar");
  const roadmapProgressValue = document.getElementById("roadmapProgressValue");
  const roadmapProgressBar = document.getElementById("roadmapProgressBar");
  const skillsProgressValue = document.getElementById("skillsProgressValue");
  const skillsProgressBar = document.getElementById("skillsProgressBar");
  const coursesProgressValue = document.getElementById("coursesProgressValue");
  const coursesProgressBar = document.getElementById("coursesProgressBar");
  const projectsProgressValue = document.getElementById("projectsProgressValue",);
  const projectsProgressBar = document.getElementById("projectsProgressBar");
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

  if (closeButton) {
    closeButton.addEventListener("click", closeSidebar);
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

  function getProgress(storageKey, totalItems) {
    const completedItems = JSON.parse(localStorage.getItem(storageKey)) || [];

    if (totalItems === 0) {
      return 0;
    }
    return Math.round((completedItems.length / totalItems) * 100);
  }
  function setProgress(textElement, barElement, percentage) {
    if (textElement) {
      textElement.textContent = `${percentage}%`;
    }

    if (barElement) {
      barElement.style.width = `${percentage}%`;
    }
  }

  const roadmapProgress = getProgress("pathnivoCompletedSteps", 6);
  const skillsProgress = getProgress("pathnivoLearnedSkills", 6);
  const coursesProgress = getProgress("pathnivoCompletedCourses", 6);
  const projectsProgress = getProgress("pathnivoCompletedProjects", 6);
  setProgress(roadmapProgressValue, roadmapProgressBar, roadmapProgress);
  setProgress(skillsProgressValue, skillsProgressBar, skillsProgress);
  setProgress(coursesProgressValue, coursesProgressBar, coursesProgress);
  setProgress(projectsProgressValue, projectsProgressBar, projectsProgress);
  const overallProgress = Math.round(
    (roadmapProgress + skillsProgress + coursesProgress + projectsProgress) / 4,
  );
  if (overallProgressText) {
    overallProgressText.textContent = `${overallProgress}%`;
  }
  if (overallProgressCircle) {
    overallProgressCircle.textContent = `${overallProgress}%`;
  }
  if (overallProgressBar) {
    overallProgressBar.style.width = `${overallProgress}%`;
  }
});
