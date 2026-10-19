"use strict";

(function initializeApp() {
	const API_CONFIG = {
		baseUrl: "http://localhost:4000",
		endpoints: {
			startSession: "/api/set-session",
			chat: "/api/ans"
		},
		timeoutMs: 30000
	};

	const state = {
		videoId: null,
		sessionId: null,
		isSessionActive: false,
		isStartingSession: false,
		isSendingMessage: false
	};

	const elements = {
		sessionForm: document.getElementById("session-form"),
		youtubeUrlInput: document.getElementById("youtube-url"),
		startSessionBtn: document.getElementById("start-session-btn"),
		sessionFeedback: document.getElementById("session-feedback"),
		sessionState: document.getElementById("session-state"),
		videoId: document.getElementById("video-id"),
		chatBadge: document.getElementById("chat-badge"),
		chatMessages: document.getElementById("chat-messages"),
		chatForm: document.getElementById("chat-form"),
		chatInput: document.getElementById("chat-input"),
		sendBtn: document.getElementById("send-btn")
	};

	bindEvents();
	bootstrapUI();

	function bindEvents() {
		elements.sessionForm.addEventListener("submit", onStartSession);
		elements.chatForm.addEventListener("submit", onSendMessage);
	}

	function bootstrapUI() {
		renderSystemMessage("Enter a YouTube URL to start a session.");
		updateSessionUI();
		updateChatAvailability();
	}

	async function onStartSession(event) {
		event.preventDefault();

		if (state.isStartingSession) {
			return;
		}

		const youtubeUrl = elements.youtubeUrlInput.value.trim();
		if (!isValidYouTubeUrl(youtubeUrl)) {
			setSessionFeedback("Please enter a valid YouTube URL.", "error");
			return;
		}

		setSessionLoading(true);
		setSessionFeedback("Starting session...", "");

		try {
			const payload = await requestStartSession(youtubeUrl);
			const videoId = payload.videoId || payload.video_id || payload.id || null;
			const sessionId = payload.sessionId || payload.session_id || null;

			if (!videoId) {
				throw new Error("Backend did not return a video ID.");
			}

			state.videoId = String(videoId);
			state.sessionId = sessionId ? String(sessionId) : null;
			state.isSessionActive = true;

			updateSessionUI();
			updateChatAvailability();

			setSessionFeedback("Session started successfully.", "success");
			renderSystemMessage(`Session started for video ID: ${state.videoId}`);
		} catch (error) {
			state.videoId = null;
			state.sessionId = null;
			state.isSessionActive = false;

			updateSessionUI();
			updateChatAvailability();

			const message = error instanceof Error ? error.message : "Failed to start session.";
			setSessionFeedback(message, "error");
			renderSystemMessage(`Session error: ${message}`);
		} finally {
			setSessionLoading(false);
		}
	}

	async function onSendMessage(event) {
		event.preventDefault();

		if (!state.isSessionActive || state.isSendingMessage) {
			return;
		}

		const message = elements.chatInput.value.trim();
		if (!message) {
			return;
		}

		elements.chatInput.value = "";
		renderMessage("user", message);
		setChatLoading(true);

		try {
			const payload = await requestChatResponse(message);
			const reply = extractChatReply(payload);
			renderMessage("assistant", String(reply));
		} catch (error) {
			const messageText = error instanceof Error ? error.message : "Failed to send message.";
			renderSystemMessage(`Chat error: ${messageText}`);
		} finally {
			setChatLoading(false);
			elements.chatInput.focus();
		}
	}

	async function requestStartSession(youtubeUrl) {
		const endpoint = buildUrl(API_CONFIG.endpoints.startSession, {
			url: youtubeUrl
		});
		return requestJson(endpoint);
	}

	async function requestChatResponse(message) {
		const endpoint = buildUrl(API_CONFIG.endpoints.chat, {
			video_id: state.videoId,
			query: message
		});
		return requestJson(endpoint);
	}

	function buildUrl(path, queryParams) {
		const url = new URL(`${API_CONFIG.baseUrl}${path}`);
		Object.entries(queryParams).forEach(([key, value]) => {
			if (value !== null && value !== undefined && value !== "") {
				url.searchParams.set(key, String(value));
			}
		});
		return url.toString();
	}

	function extractChatReply(payload) {
		if (!payload || typeof payload !== "object") {
			return "No response text was returned.";
		}

		const data = payload.data;
		if (typeof data === "string") {
			return data || "No response text was returned.";
		}

		if (data && typeof data === "object") {
			return data.response || data.answer || data.message || data.reply || JSON.stringify(data, null, 2);
		}

		return payload.response || payload.answer || payload.message || payload.reply || "No response text was returned.";
	}

	async function requestJson(url, options) {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeoutMs);

		try {
			const response = await fetch(url, {
				...options,
				signal: controller.signal
			});

			let payload = {};
			try {
				payload = await response.json();
			} catch (parseError) {
				payload = {};
			}

			if (!response.ok) {
				const serverMessage = payload.error || payload.message || `Request failed with status ${response.status}`;
				throw new Error(serverMessage);
			}

			return payload;
		} catch (error) {
			if (error instanceof Error && error.name === "AbortError") {
				throw new Error("Request timed out. Please try again.");
			}
			throw error;
		} finally {
			clearTimeout(timeoutId);
		}
	}

	function updateSessionUI() {
		elements.sessionState.textContent = state.isSessionActive ? "Active" : "Not Started";
		elements.videoId.textContent = state.videoId || "-";
	}

	function updateChatAvailability() {
		const isEnabled = state.isSessionActive && !state.isStartingSession;
		elements.chatInput.disabled = !isEnabled;
		elements.sendBtn.disabled = !isEnabled || state.isSendingMessage;
		elements.chatBadge.textContent = isEnabled ? "Session live" : "Session required";
		elements.chatBadge.classList.toggle("is-active", isEnabled);
	}

	function setSessionLoading(isLoading) {
		state.isStartingSession = isLoading;
		elements.startSessionBtn.disabled = isLoading;
		elements.startSessionBtn.textContent = isLoading ? "Starting..." : "Start";
		updateChatAvailability();
	}

	function setChatLoading(isLoading) {
		state.isSendingMessage = isLoading;
		elements.sendBtn.disabled = isLoading || !state.isSessionActive;
		elements.sendBtn.textContent = isLoading ? "Sending..." : "Send";
	}

	function setSessionFeedback(message, type) {
		elements.sessionFeedback.textContent = message;
		elements.sessionFeedback.classList.remove("error", "success");
		if (type) {
			elements.sessionFeedback.classList.add(type);
		}
	}

	function renderSystemMessage(message) {
		renderMessage("system", message);
	}

	function renderMessage(role, content) {
		const messageElement = document.createElement("article");
		messageElement.className = `chat-message ${role}`;
		messageElement.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");

		elements.chatMessages.appendChild(messageElement);
		elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
	}

	function escapeHtml(value) {
		return value
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/\"/g, "&quot;")
			.replace(/'/g, "&#39;");
	}

	function isValidYouTubeUrl(url) {
		if (!url) {
			return false;
		}

		try {
			const parsed = new URL(url);
			const host = parsed.hostname.toLowerCase();
			return host.includes("youtube.com") || host.includes("youtu.be");
		} catch (error) {
			return false;
		}
	}
})();
