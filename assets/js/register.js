document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.getElementById("registerForm");
  if (!registerForm) {
    return;
  }

  const nameInput = document.getElementById("registerName");
  const emailInput = document.getElementById("registerEmail");
  const passwordInput = document.getElementById("registerPassword");
  const confirmPasswordInput = document.getElementById("registerConfirmPassword",);
  const messageElement = document.getElementById("registerMessage");
  function showMessage(message, type = "error") {
    if (!messageElement) {
      return;
    }
    messageElement.textContent = message;
    messageElement.classList.remove("hidden", "text-red-600", "text-green-600");
    if (type === "success") {
      messageElement.classList.add("text-green-600");
    } else {
      messageElement.classList.add("text-red-600");
    }
  }

  registerForm.addEventListener("submit", (event) => {
    const fullName = nameInput.value.trim();
    const email = emailInput.value.trim().toLowerCase();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    if (fullName.length < 2) {
      showMessage("Please enter a valid full name.");
      return;
    }

    if (!email.includes("@") || !email.includes(".")) {
      showMessage("Please enter a valid email address.");
      return;
    }

    if (password.length < 6) {
      showMessage("Password must contain at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      showMessage("Passwords do not match.");
      return;
    }

    const existingUser = JSON.parse(
      localStorage.getItem("pathnivoUser") || "null",
    );

    if (existingUser && existingUser.email === email) {
      showMessage("This email is already registered. Please login.");
      return;
    }

    const user = {
      fullName,
      email,
      password,
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem("pathnivoUser", JSON.stringify(user));
    const profile = {
      fullName,
      email,
      education: "BCA",
      studyYear: "3rd Year",
      careerGoal: "Full Stack Developer",
      skillLevel: "Beginner",
    };

    localStorage.setItem("pathnivoStudentProfile", JSON.stringify(profile));
    localStorage.removeItem("pathnivoLoggedIn");
    showMessage(
      "Account created successfully. Redirecting to login...",
      "success",
    );
    setTimeout(() => {
      window.location.href = "login.html";
    }, 1000);
  });
});
