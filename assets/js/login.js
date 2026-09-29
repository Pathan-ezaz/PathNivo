/*
document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (!loginForm) {
    return;
  }

  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const messageElement = document.getElementById("loginMessage");
  const loginButton = loginForm.querySelector('button[type="submit"]');
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

  loginForm.addEventListener("submit", (event) => {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    if (!email || !password) {
      event.preventDefault();
      showMessage("Please enter email and password.");
      return;
    }
    if (loginButton) {
      loginButton.disabled = true;
      loginButton.textContent = "Logging in...";
    }
  });
});
*/

document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const loginButton = loginForm?.querySelector('button[type="submit"]');

    if (!loginForm) {
        return;
    }

    loginForm.addEventListener("submit", function () {
        if (loginButton) {
            loginButton.disabled = true;
            loginButton.textContent = "Logging in...";
        }

        /*
         * Important:
         * Yahan preventDefault() nahi lagana hai.
         * Flask ko normal POST request receive karne do.
         */
    });
});