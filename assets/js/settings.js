document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.getElementById("studentMenuButton");
  const closeButton = document.getElementById("studentSidebarClose");
  const mobileSidebar = document.getElementById("studentMobileSidebar");
  const overlay = document.getElementById("studentSidebarOverlay");
  const themeSelect = document.getElementById("themeSelect");
  const emailNotifications = document.getElementById("emailNotifications");
  const learningReminder = document.getElementById("learningReminder");
  const saveSettingsButton = document.getElementById("saveSettingsButton");
  const settingsStatus = document.getElementById("settingsStatus");
  const logoutButton = document.getElementById("logoutButton");
  const headerAvatar = document.getElementById("headerAvatar");
  const SETTINGS_KEY = "pathnivoSettings";
  const PROFILE_KEY = "pathnivoStudentProfile";
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

  const defaultSettings = {
    theme: "light",
    emailNotifications: true,
    learningReminder: true,
  };

  let settings = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || defaultSettings;
  const savedProfile = JSON.parse(localStorage.getItem(PROFILE_KEY));
  if (savedProfile && savedProfile.fullName && headerAvatar) {
    headerAvatar.textContent = savedProfile.fullName
      .trim()
      .charAt(0)
      .toUpperCase();
  }

  function loadSettings() {
    themeSelect.value = settings.theme;
    emailNotifications.checked = settings.emailNotifications;
    learningReminder.checked = settings.learningReminder;
    applyTheme(settings.theme);
  }

  function applyTheme(theme) {
    if (theme === "dark") {
      document.body.classList.add("bg-slate-900", "text-black");
      document.body.classList.remove("bg-slate-50", "text-slate-900");
    } else {
      document.body.classList.remove("bg-slate-900", "text-black");
      document.body.classList.add("bg-slate-50", "text-slate-900");
    }
  }

  function showStatus(message) {
    if (!settingsStatus) return;
    settingsStatus.textContent = message;
    settingsStatus.classList.remove("hidden");
    setTimeout(() => {
      settingsStatus.classList.add("hidden");
    }, 2500);
  }

  if (saveSettingsButton) {
    saveSettingsButton.addEventListener("click", () => {
      settings = {
        theme: themeSelect.value,
        emailNotifications: emailNotifications.checked,
        learningReminder: learningReminder.checked,
      };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
      applyTheme(settings.theme);
      showStatus("Settings saved successfully.");
    });
  }

  if (themeSelect) {
    themeSelect.addEventListener("change", () => {
      applyTheme(themeSelect.value);
    });
  }

  loadSettings();
});
