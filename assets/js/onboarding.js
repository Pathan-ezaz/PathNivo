document.addEventListener("DOMContentLoaded", function () {
  const onboardingForm = document.getElementById("onboardingForm");
  if (!onboardingForm) {
    console.error("onboardingForm nahi mila.");
    return;
  }

  onboardingForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const nameInput = document.getElementById("onboardingName");
    const educationInput = document.getElementById("onboardingEducation");
    const yearInput = document.getElementById("onboardingYear");
    const careerInput = document.getElementById("onboardingCareerGoal");
    const skillLevelInput = document.getElementById("onboardingSkillLevel");
    const skillsInput = document.getElementById("onboardingSkills");
    const oldYearInput = document.getElementById("studyYear");
    const oldCareerInput = document.getElementById("career");
    const oldSkillsInput = document.getElementById("skills");
    const name = nameInput ? nameInput.value.trim() : "";
    const education = educationInput ? educationInput.value.trim() : "";
    const studyYear = yearInput
      ? yearInput.value
      : oldYearInput
        ? oldYearInput.value
        : "";

    const careerGoal = careerInput
      ? careerInput.value
      : oldCareerInput
        ? oldCareerInput.value
        : "";

    const skillLevel = skillLevelInput 
        ? skillLevelInput.value
        : "Beginner";

    const skills = skillsInput
      ? skillsInput.value.trim()
      : oldSkillsInput
        ? oldSkillsInput.value.trim()
        : "";

    const selectedInterests = [];
    const interestCheckboxes = document.querySelectorAll(
      'input[name="interest"]:checked',
    );

    interestCheckboxes.forEach(function (checkbox) {
      selectedInterests.push(checkbox.value);
    });

    if (nameInput && name === "") {
      showMessage("Please enter your name.", "error");
      nameInput.focus();
      return;
    }

    if (education === "") {
      showMessage("Please enter your education.", "error");
      if (educationInput) {
        educationInput.focus();
      }
      return;
    }

    if (studyYear === "") {
      showMessage("Please select your study year.", "error");
      if (yearInput) {
        yearInput.focus();
      } else if (oldYearInput) {
        oldYearInput.focus();
      }
      return;
    }

    if (careerGoal === "") {
      showMessage("Please select your career goal.", "error");
      if (careerInput) {
        careerInput.focus();
      } else if (oldCareerInput) {
        oldCareerInput.focus();
      }
      return;
    }

    if (selectedInterests.length === 0) {
      showMessage("Please select at least one area of interest.", "error");
      return;
    }

    const onboardingData = {
      name: name,
      education: education,
      studyYear: studyYear,
      careerGoal: careerGoal,
      skillLevel: skillLevel,
      skills: skills,
      interests: selectedInterests,
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem(
      "pathnivoOnboardingData",
      JSON.stringify(onboardingData),
    );

    localStorage.setItem("pathnivoUserName", name);
    localStorage.setItem("pathnivoCareerGoal", careerGoal);
    showMessage("Your profile has been saved successfully!", "success");
    const submitButton = onboardingForm.querySelector(
      'button[type="submit"], button:not([type])',
    );

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Saving...";
    }

    setTimeout(function () {
      window.location.href = "/dashboard";
    }, 900);
  });

  function showMessage(message, type) {
    let messageBox = document.getElementById("onboardingMessage");
    if (!messageBox) {
      messageBox = document.createElement("div");
      messageBox.id = "onboardingMessage";
      onboardingForm.prepend(messageBox);
    }

    messageBox.textContent = message;
    messageBox.style.display = "block";
    messageBox.style.padding = "12px";
    messageBox.style.marginBottom = "16px";
    messageBox.style.borderRadius = "8px";
    messageBox.style.fontSize = "14px";
    messageBox.style.fontWeight = "500";

    if (type === "error") {
      messageBox.style.color = "#991b1b";
      messageBox.style.backgroundColor = "#fee2e2";
      messageBox.style.border = "1px solid #fca5a5";
    } else {
      messageBox.style.color = "#166534";
      messageBox.style.backgroundColor = "#dcfce7";
      messageBox.style.border = "1px solid #86efac";
    }
  }
});
