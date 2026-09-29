document.addEventListener("DOMContentLoaded", function () {
  const menuButton = document.getElementById("studentMenuButton");
  const mobileSidebar = document.getElementById("studentMobileSidebar");
  const sidebarOverlay = document.getElementById("studentSidebarOverlay");
  function openStudentSidebar() {
    if (!mobileSidebar || !sidebarOverlay) {
      console.error("Sidebar elements not found in dashboard.html");
      return;
    }
    mobileSidebar.classList.remove("hidden");
    sidebarOverlay.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
  }

  function closeStudentSidebar() {
    if (!mobileSidebar || !sidebarOverlay) {
      return;
    }
    mobileSidebar.classList.add("hidden");
    sidebarOverlay.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
  }

  window.openStudentSidebar = openStudentSidebar;
  window.closeStudentSidebar = closeStudentSidebar;
  if (menuButton) {
    menuButton.addEventListener("click", openStudentSidebar);
  } else {
    console.error("studentMenuButton not found");
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
    const mobileLinks = mobileSidebar.querySelectorAll("a");
    mobileLinks.forEach(function (link) {
      link.addEventListener("click", closeStudentSidebar);
    });
  }

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 1024) {
      closeStudentSidebar();
    }
  });

  const currentFile = window.location.pathname.split("/").pop();
  const allSidebarLinks = document.querySelectorAll("aside a[href]");
  allSidebarLinks.forEach(function (link) {
    const linkPath = link.getAttribute("href");
    if (!linkPath) {
      return;
    }

    const linkFile = linkPath.split("/").pop();
    link.classList.remove("bg-indigo-50", "text-indigo-700", "font-semibold");

    if (
      linkFile === currentFile ||
      (currentFile === "" && linkFile === "dashboard.html")
    ) {
      link.classList.add("bg-indigo-50", "text-indigo-700", "font-semibold");
    }
  });

  function logoutStudent() { window.location.href = "/logout"; }
  window.logoutStudent = logoutStudent;
  console.log("PathNivo Student Dashboard JS loaded successfully.");
});
