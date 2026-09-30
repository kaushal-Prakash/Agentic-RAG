const API_BASE_URL = "http://127.0.0.1:8000";
const loginForm = document.getElementById("loginForm");
const loginButton = document.getElementById("loginButton");
const messageBox = document.getElementById("message");

function showMessage(message, type) {
    messageBox.textContent = message;
    messageBox.className = `message ${type}`;
}

function clearMessage() {
    messageBox.textContent = "";
    messageBox.className = "message";
}

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    clearMessage();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    if (!username || !password) {
        showMessage("Please enter your username and password.", "error");
        return;
    }
    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        const data = await response.json();
        if (!response.ok) {
            showMessage(data.detail || "Login failed.", "error");
            return;
        }
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("username", data.username);
        localStorage.setItem("name", data.name);
        showMessage("Login successful. Redirecting...", "success");
        setTimeout(function () {
            window.location.href = "chat.html";
        }, 500);
    } catch (error) {
        console.error("Login error:", error);
        showMessage("Unable to connect to the server.", "error");
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }
});