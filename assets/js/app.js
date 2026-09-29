console.log("PathNivo frontend loaded successfully.");
const profileForm = document.getElementById("profileForm");
const profileMessage = document.getElementById("profileMessage");

profileForm.addEventListener("submit", function (event) {
  event.preventDefault();
  profileMessage.textContent =
    "Profile changes saved successfully in demo mode.";
  profileMessage.classList.remove("hidden", "text-red-700", "bg-red-100");
  profileMessage.classList.add("text-green-700", "bg-green-100");
});