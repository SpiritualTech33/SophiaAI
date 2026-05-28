/* =========================================================================
   auth.js — login + register form handling.

   One module serves both pages. The form's data-mode attribute
   ("login" | "register") selects the endpoint. On success the JWT is
   stored and the user is sent to /chat. On failure the API's error
   message is shown inline and the offending field regains focus.
   ========================================================================= */

import { setToken } from "/static/js/cosmos.js";

const form = document.getElementById("auth-form");
const errorBox = document.getElementById("error");
const submitBtn = document.getElementById("submit");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");

const ENDPOINTS = {
  login: "/auth/login",
  register: "/auth/register",
};

/* Password show/hide toggle. */
const toggle = form.querySelector("[data-toggle='password']");
if (toggle) {
  toggle.addEventListener("click", () => {
    const showing = passwordInput.type === "text";
    passwordInput.type = showing ? "password" : "text";
    toggle.textContent = showing ? "Show" : "Hide";
    toggle.setAttribute("aria-label", showing ? "Show password" : "Hide password");
  });
}

function showError(message) {
  errorBox.textContent = message;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");

  const mode = form.dataset.mode;
  const url = ENDPOINTS[mode];
  const email = emailInput.value.trim();
  const password = passwordInput.value;

  if (!email || !password) {
    showError("Email and password are required.");
    (!email ? emailInput : passwordInput).focus();
    return;
  }

  const label = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = "Opening the portal…";

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showError(data.detail || "Something went wrong. Please try again.");
      submitBtn.disabled = false;
      submitBtn.textContent = label;
      emailInput.focus();
      return;
    }

    const data = await response.json();
    setToken(data.access_token);
    window.location.replace("/chat");
  } catch (err) {
    showError("Network error. Please check your connection and try again.");
    submitBtn.disabled = false;
    submitBtn.textContent = label;
  }
});
