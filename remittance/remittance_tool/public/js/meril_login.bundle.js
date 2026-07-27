// Meril Unified Portal — Sign In page behavior

document.addEventListener("DOMContentLoaded", () => {
	const form = document.getElementById("login-form");
	const usernameInput = document.getElementById("login_email");
	const passwordInput = document.getElementById("login_password");
	const signInBtn = document.getElementById("btn-signin");
	const alertBox = document.getElementById("login-alert");
	const toggleBtn = document.querySelector(".toggle-password");
	const forgotLink = document.getElementById("forgot-password");

	function showAlert(message, type = "error") {
		alertBox.textContent = message;
		alertBox.classList.toggle("login-alert--success", type === "success");
		alertBox.hidden = false;
	}

	function clearAlert() {
		alertBox.hidden = true;
	}

	function setBusy(busy, label) {
		signInBtn.disabled = busy;
		signInBtn.textContent = label;
	}

	// show / hide password
	toggleBtn.addEventListener("click", () => {
		const hidden = passwordInput.type === "password";
		passwordInput.type = hidden ? "text" : "password";
		toggleBtn.querySelector(".icon-eye-off").style.display = hidden ? "none" : "";
		toggleBtn.querySelector(".icon-eye").style.display = hidden ? "" : "none";
		toggleBtn.setAttribute("aria-label", hidden ? "Hide password" : "Show password");
	});

	// sign in
	form.addEventListener("submit", async (e) => {
		e.preventDefault();
		clearAlert();

		const usr = usernameInput.value.trim();
		const pwd = passwordInput.value;

		if (!usr || !pwd) {
			showAlert("Please enter both username and password.");
			return;
		}

		setBusy(true, "Signing In...");
		try {
			const response = await fetch("/api/method/login", {
				method: "POST",
				headers: {
					"Content-Type": "application/x-www-form-urlencoded",
					Accept: "application/json",
				},
				body: new URLSearchParams({ usr, pwd }),
			});

			if (response.ok) {
				const data = await response.json();
				const redirectTo = new URLSearchParams(window.location.search).get("redirect-to");
				window.location.replace(redirectTo || data.home_page || "/app");
				return;
			}

			if (response.status === 401) {
				showAlert("Invalid username or password.");
			} else if (response.status === 417) {
				showAlert("Too many failed attempts. Please try again later.");
			} else {
				const data = await response.json().catch(() => ({}));
				showAlert(data.message || "Unable to sign in. Please try again.");
			}
		} catch (err) {
			showAlert("Network error. Please check your connection and try again.");
		} finally {
			setBusy(false, "Sign In");
		}
	});

	// forgot password — sends reset email for the entered username
	forgotLink.addEventListener("click", async (e) => {
		e.preventDefault();
		clearAlert();

		const user = usernameInput.value.trim();
		if (!user) {
			showAlert("Enter your email or username first, then click Forgot Password.");
			usernameInput.focus();
			return;
		}

		try {
			const response = await fetch(
				"/api/method/frappe.core.doctype.user.user.reset_password",
				{
					method: "POST",
					headers: {
						"Content-Type": "application/x-www-form-urlencoded",
						Accept: "application/json",
					},
					body: new URLSearchParams({ user }),
				}
			);

			if (response.ok) {
				showAlert("Password reset instructions have been sent to your email.", "success");
			} else if (response.status === 404) {
				showAlert("No account found with this email or username.");
			} else {
				showAlert("Unable to send reset email. Please try again later.");
			}
		} catch (err) {
			showAlert("Network error. Please check your connection and try again.");
		}
	});
});
