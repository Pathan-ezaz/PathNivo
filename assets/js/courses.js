document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("coursesSearch");
    const filterSelect = document.getElementById("coursesFilter");
    const courseCards = document.querySelectorAll(".course-card");
    const emptyMessage = document.getElementById("coursesEmptyMessage");
    const progressBar = document.getElementById("coursesProgressBar");
    const progressText = document.getElementById("coursesProgressText");

    function filterCourses() {
        const searchText = searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";

        const selectedCategory = filterSelect
            ? filterSelect.value.toLowerCase()
            : "all";
        let visibleCourses = 0;
        courseCards.forEach(card => {
            const title = card .querySelector("h3") ?.textContent .toLowerCase() || "";
            const career = card .querySelector("p") ?.textContent .toLowerCase() || "";
            const category = card.dataset.category?.toLowerCase() || "";
            const matchesSearch = title.includes(searchText) || career.includes(searchText);
            const matchesCategory = selectedCategory === "all" || category === selectedCategory;
            if (matchesSearch && matchesCategory) {
                card.classList.remove("hidden");
                visibleCourses++;
            } else {
                card.classList.add("hidden");
            }
        });

        if (emptyMessage) {
            if (visibleCourses === 0) {
                emptyMessage.classList.remove("hidden");
            } else {
                emptyMessage.classList.add("hidden");
            }
        }
    }

    if (searchInput) {
        searchInput.addEventListener( "input", filterCourses );
    }

    if (filterSelect) {
        filterSelect.addEventListener( "change", filterCourses );
    }

    function updateCourseProgress() {
        if (!courseCards.length) {
            if (progressBar) {
                progressBar.style.width = "0%";
            }

            if (progressText) {
                progressText.textContent = "0% Completed";
            }
            return;
        }

        let totalProgress = 0;
        courseCards.forEach(card => {
            const progressTextElement = card.querySelector(".text-slate-500");
            const cardText = card.textContent || "";
            const match = cardText.match(/(\d+)% Complete/);
            if (match) {
                totalProgress += parseInt(match[1], 10);
            }
        });

        const averageProgress = Math.round( totalProgress / courseCards.length );
        if (progressBar) {
            progressBar.style.width = `${averageProgress}%`;
        }

        if (progressText) {
            progressText.textContent = `${averageProgress}% Completed`;
        }
    }

    filterCourses();
    updateCourseProgress();

});