const API_BASE_URL = "http://127.0.0.1:8000";
const registerForm = document.getElementById("registerForm");
const registerButton = document.getElementById("registerButton");
const messageBox = document.getElementById("message");

function showMessage(message, type) {
    messageBox.textContent = message;
    messageBox.className = `message ${type}`;
}

function clearMessage() {
    messageBox.textContent = "";
    messageBox.className = "message";
}

registerForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearMessage();
    const name = document.getElementById("name").value.trim();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    if (!name || !username || !password) {
        showMessage("Please fill in all fields.", "error");
        return;
    }
    registerButton.disabled = true;
    registerButton.textContent = "Creating account...";
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                username: username,
                password: password
            })
        });
        const data = await response.json();
        if (!response.ok) {
            showMessage(data.detail || "Registration failed.", "error");
            return;
        }
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("username", data.username);
        localStorage.setItem("name", data.name);
        showMessage("Registration successful. Redirecting...", "success");
        setTimeout(function () {
            window.location.href = "chat.html";
        }, 800);
    } catch (error) {
        console.error("Registration error:", error);
        showMessage("Unable to connect to the server.", "error");
    } finally {
        registerButton.disabled = false;
        registerButton.textContent = "Register";
    }
});