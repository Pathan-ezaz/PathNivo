document.addEventListener("DOMContentLoaded", () => {
  const menuButton = document.getElementById("studentMenuButton");
  const mobileSidebar = document.getElementById("studentMobileSidebar");
  const overlay = document.getElementById("studentSidebarOverlay");
  const profileForm = document.getElementById("profileForm");
  const resetProfileButton = document.getElementById("resetProfileButton");
  const fullNameInput = document.getElementById("fullName");
  const emailInput = document.getElementById("email");
  const educationInput = document.getElementById("education");
  const studyYearInput = document.getElementById("studyYear");
  const careerGoalInput = document.getElementById("careerGoal");
  const skillLevelInput = document.getElementById("skillLevel");
  const profileAvatar = document.getElementById("profileAvatar");
  const headerAvatar = document.getElementById("headerAvatar");
  const profileDisplayName = document.getElementById("profileDisplayName");
  const profileDisplayEmail = document.getElementById("profileDisplayEmail");
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

  if (menuButton) {menuButton.addEventListener("click", openSidebar);}
  if (overlay) {overlay.addEventListener("click", closeSidebar);}

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

  function updateAvatar(name) {
    const cleanName = name.trim();
    if (!cleanName) return;
    const firstLetter = cleanName.charAt(0).toUpperCase();
    if (profileAvatar) {profileAvatar.textContent = firstLetter;}
    if (headerAvatar) {headerAvatar.textContent = firstLetter;}
  }

  function updateProfilePreview() {
    const name = fullNameInput ? fullNameInput.value.trim() : "";
    const email = emailInput ? emailInput.value.trim() : "";
    if (profileDisplayName) {profileDisplayName.textContent = name || "Your Name";}
    if (profileDisplayEmail) {profileDisplayEmail.textContent = email || "your@email.com";}
    updateAvatar(name || "A");
}
  if (fullNameInput) {fullNameInput.addEventListener("input", updateProfilePreview);}
  if (emailInput) {emailInput.addEventListener("input", updateProfilePreview);}
  if (profileForm) {
    profileForm.addEventListener("submit", () => {
    });
  }

  const initialValues = {
    name: fullNameInput ? fullNameInput.value : "",
    email: emailInput ? emailInput.value : "",
    education: educationInput ? educationInput.value : "",
    studyYear: studyYearInput ? studyYearInput.value : "",
    careerGoal: careerGoalInput ? careerGoalInput.value : "",
    skillLevel: skillLevelInput ? skillLevelInput.value : ""
  };

  if (resetProfileButton) {
    resetProfileButton.addEventListener("click", () => {
      const confirmReset = confirm( "Are you sure you want to reset your unsaved changes?");
      if (!confirmReset) return;
      if (fullNameInput) {fullNameInput.value = initialValues.name;}
      if (emailInput) {emailInput.value = initialValues.email;}
      if (educationInput) {educationInput.value = initialValues.education;}
      if (studyYearInput) {studyYearInput.value = initialValues.studyYear;}
      if (careerGoalInput) {careerGoalInput.value = initialValues.careerGoal;}
      if (skillLevelInput) {skillLevelInput.value = initialValues.skillLevel;}
      updateProfilePreview();
    });
  }
  updateProfilePreview();
});

  const profilePictureInput = document.getElementById("profilePictureInput");
  const profilePictureName = document.getElementById("profilePictureName");
  if (profilePictureInput) {
      profilePictureInput.addEventListener("change", function () {
          const file = this.files[0];
          if (!file) {
              return;
          }

          if (profilePictureName) {profilePictureName.textContent = file.name;}
          const reader = new FileReader();
          reader.onload = function (event) {
              const oldAvatar = document.getElementById("profileAvatar");
              if (!oldAvatar) {
                  return;
              }

              const newAvatar = document.createElement("img");
              newAvatar.id = "profileAvatar";
              newAvatar.src = event.target.result;
              newAvatar.alt = "Profile Picture";
              newAvatar.className = "h-24 w-24 rounded-full object-cover border-4 border-white shadow";
              oldAvatar.replaceWith(newAvatar);
          };
          reader.readAsDataURL(file);
      });
  }