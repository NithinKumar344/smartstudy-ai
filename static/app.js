
document.addEventListener("DOMContentLoaded", function () {

    // Smooth scrolling for dashboard navigation
    document.querySelectorAll('.nav[href*="#"]').forEach(function (link) {
        link.addEventListener("click", function (event) {
            const targetId = this.getAttribute("href").split("#")[1];
            const target = document.getElementById(targetId);

            if (target) {
                event.preventDefault();
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });

    // Confirmation before deleting a subject
    document.querySelectorAll(".delete-btn").forEach(function (button) {
        button.addEventListener("click", function (event) {
            if (!confirm("Are you sure you want to delete this subject?")) {
                event.preventDefault();
            }
        });
    });

    // Confirmation before logging out
    document.querySelectorAll(".logout").forEach(function (button) {
        button.addEventListener("click", function (event) {
            if (!confirm("Are you sure you want to log out?")) {
                event.preventDefault();
            }
        });
    });

    // Prevent accidental double form submissions
    document.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function () {
            const submitButton = form.querySelector('button[type="submit"]');

            if (submitButton && !submitButton.classList.contains("logout")) {
                submitButton.disabled = true;
                submitButton.style.opacity = "0.7";
                submitButton.style.cursor = "wait";
            }
        });
    });

});
