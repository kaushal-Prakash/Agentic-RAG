const API_BASE_URL = "http://127.0.0.1:8000";
const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const logoutButton = document.getElementById("logoutButton");
const userNameElement = document.getElementById("userName");
const typingIndicator = document.getElementById("typingIndicator");
const statusElement = document.getElementById("status");
const welcomeMessage = document.getElementById("welcomeMessage");
const accessToken = localStorage.getItem("access_token");
if (!accessToken) {
  window.location.replace("login.html");
}
const storedName = localStorage.getItem("name");
const storedUsername = localStorage.getItem("username");
if (storedName) {
  userNameElement.textContent = storedName;
} else if (storedUsername) {
  userNameElement.textContent = storedUsername;
}
function setStatus(message) {
  statusElement.textContent = message;
}
function clearStatus() {
  statusElement.textContent = "";
}
function setTyping(isTyping) {
  if (isTyping) {
    typingIndicator.classList.remove("hidden");
  } else {
    typingIndicator.classList.add("hidden");
  }
}
function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
function addMessage(content, role) {
  if (welcomeMessage) {
    welcomeMessage.remove();
  }
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = content;
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
  scrollToBottom();
}
async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) {
    return;
  }
  if (!accessToken) {
    window.location.replace("login.html");
    return;
  }
  addMessage(message, "user");
  messageInput.value = "";
  autoResizeTextarea();
  sendButton.disabled = true;
  messageInput.disabled = true;
  setTyping(true);
  setStatus("Generating response...");
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ message: message }),
    });
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_id");
      localStorage.removeItem("username");
      localStorage.removeItem("name");
      window.location.replace("login.html");
      return;
    }
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Chat request failed.");
    }
    addMessage(data.response, "assistant");
    clearStatus();
  } catch (error) {
    console.error("Chat error:", error);
    addMessage(`Error: ${error.message}`, "assistant");
    setStatus("Something went wrong.");
  } finally {
    setTyping(false);
    sendButton.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
  }
}
function autoResizeTextarea() {
  messageInput.style.height = "auto";
  const newHeight = Math.min(messageInput.scrollHeight, 160);
  messageInput.style.height = `${newHeight}px`;
}
messageInput.addEventListener("input", autoResizeTextarea);
messageInput.addEventListener("keydown", function (event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    event.stopPropagation();
    sendMessage();
  }
});
sendButton.addEventListener("click", function (event) {
  event.preventDefault();
  sendMessage();
});
logoutButton.addEventListener("click", function () {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
  localStorage.removeItem("name");
  window.location.replace("login.html");
});
