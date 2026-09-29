document.addEventListener("DOMContentLoaded", function () {
  "use strict";
  const menuButton = document.getElementById("studentMenuButton");
  const mobileSidebar = document.getElementById("studentMobileSidebar");
  const sidebarOverlay = document.getElementById("studentSidebarOverlay");
  function openStudentSidebar() {
    if (mobileSidebar) {
      mobileSidebar.classList.remove("hidden");
    }

    if (sidebarOverlay) {
      sidebarOverlay.classList.remove("hidden");
    }
    document.body.classList.add("overflow-hidden");
  }

  function closeStudentSidebar() {
    if (mobileSidebar) {
      mobileSidebar.classList.add("hidden");
    }
    if (sidebarOverlay) {
      sidebarOverlay.classList.add("hidden");
    }
    document.body.classList.remove("overflow-hidden");
  }

  window.closeStudentSidebar = closeStudentSidebar;
  if (menuButton) {
    menuButton.addEventListener("click", openStudentSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeStudentSidebar);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeStudentSidebar();
    }
  });

  if (mobileSidebar) {
    mobileSidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeStudentSidebar);
    });
  }

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 1024) {
      closeStudentSidebar();
    }
  });

  const currentPage = window.location.pathname.split("/").pop().toLowerCase();
  document.querySelectorAll("aside a").forEach(function (link) {
    const href = link.getAttribute("href");
    if (!href) {
      return;
    }

    const linkPage = href.split("/").pop().toLowerCase();
    if (linkPage === currentPage) {
      link.classList.add("bg-indigo-50", "text-indigo-700", "font-semibold");
    }
  });

  const skillCards = document.querySelectorAll(".skill-card");
  const learnButtons = document.querySelectorAll("[data-learn-skill]");
  const savedSkills = JSON.parse(localStorage.getItem("pathnivoLearnedSkills")) || [];
  function updateSkillCard(card) {
    const skillId = card.getAttribute("data-skill");
    const percentText = card.querySelector("[data-skill-percent]");
    const progressBar = card.querySelector("[data-skill-bar]");
    const button = card.querySelector("[data-learn-skill]");
    const isLearned = savedSkills.includes(skillId);
    if (isLearned) {
      if (percentText) {
        percentText.textContent = "100%";
      }

      if (progressBar) {
        progressBar.style.width = "100%";
        progressBar.classList.remove("bg-indigo-600");
        progressBar.classList.add("bg-green-600");
      }

      if (button) {
        button.textContent = "✓ Learned";
        button.classList.remove("bg-indigo-600", "hover:bg-indigo-700");
        button.classList.add("bg-green-600", "hover:bg-green-700");
      }
      card.classList.add("border-green-300", "bg-green-50");
    } else {
      if (percentText) {
        percentText.textContent = "0%";
      }

      if (progressBar) {
        progressBar.style.width = "0%";
        progressBar.classList.remove("bg-green-600");
        progressBar.classList.add("bg-indigo-600");
      }

      if (button) {
        button.textContent = "Mark as Learned";
        button.classList.remove("bg-green-600", "hover:bg-green-700");
        button.classList.add("bg-indigo-600", "hover:bg-indigo-700");
      }
      card.classList.remove("border-green-300", "bg-green-50");
    }
  }

  function updateOverallProgress() {
    const progressBar = document.getElementById("skillsProgressBar");
    const progressText = document.getElementById("skillsProgressText");
    const totalSkills = skillCards.length;
    const learnedSkills = savedSkills.length;
    let percentage = 0;

    if (totalSkills > 0) {
      percentage = Math.round((learnedSkills / totalSkills) * 100);
    }

    if (percentage > 100) {
      percentage = 100;
    }

    if (progressBar) {
      progressBar.style.width = percentage + "%";
    }

    if (progressText) {
      progressText.textContent = percentage + "% Learned";
    }
  }

  skillCards.forEach(function (card) {
    updateSkillCard(card);
  });
  updateOverallProgress();
  learnButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const skillId = button.getAttribute("data-learn-skill");
      const skillIndex = savedSkills.indexOf(skillId);

      if (skillIndex === -1) {
        savedSkills.push(skillId);
      } else {
        savedSkills.splice(skillIndex, 1);
      }

      localStorage.setItem(
        "pathnivoLearnedSkills",
        JSON.stringify(savedSkills),
      );

      skillCards.forEach(function (card) {
        updateSkillCard(card);
      });

      updateOverallProgress();
    });
  });

  const skillsSearch = document.getElementById("skillsSearch");
  const skillsFilter = document.getElementById("skillsFilter");
  const emptyMessage = document.getElementById("skillsEmptyMessage");
  function filterSkills() {
    const searchValue = skillsSearch
      ? skillsSearch.value.toLowerCase().trim()
      : "";

    const selectedCategory = skillsFilter ? skillsFilter.value : "all";
    let visibleCount = 0;
    skillCards.forEach(function (card) {
      const skillName = card.textContent.toLowerCase();
      const skillCategory = card.getAttribute("data-category");
      const matchesSearch = skillName.includes(searchValue);
      const matchesCategory = selectedCategory === "all" || skillCategory === selectedCategory;
      if (matchesSearch && matchesCategory) {
        card.classList.remove("hidden");
        visibleCount++;
      } else {
        card.classList.add("hidden");
      }
    });

    if (emptyMessage) {
      if (visibleCount === 0) {
        emptyMessage.classList.remove("hidden");
      } else {
        emptyMessage.classList.add("hidden");
      }
    }
  }

  if (skillsSearch) {
    skillsSearch.addEventListener("input", filterSkills);
  }

  if (skillsFilter) {
    skillsFilter.addEventListener("change", filterSkills);
  }
});
