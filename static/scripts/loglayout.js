document.addEventListener("DOMContentLoaded", () => {
    const checkbox = document.getElementById("privacyterms");
    const signupButton = document.getElementById("signupButton");

    checkbox.addEventListener("change", () => {
        signupButton.disabled = !checkbox.checked;
    });
});

function togglePassword(inputId) {
    const passwordInput = document.getElementById(inputId);
    if (!passwordInput) {
        console.error(`Element with id '${inputId}' not found.`);
        return;
    }
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
    } else {
        passwordInput.type = "password";
    }
}
