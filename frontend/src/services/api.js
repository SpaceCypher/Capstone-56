const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace(/\/$/, "");

function normalizeDetail(payload) {
  if (!payload || typeof payload !== "object") {
    return "";
  }

  const detail = payload.detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return "";
        }
        const fieldPath = Array.isArray(item.loc) ? item.loc.join(".") : "request";
        const message = typeof item.msg === "string" ? item.msg : "Invalid input";
        return `${fieldPath}: ${message}`;
      })
      .filter(Boolean);

    return messages.join(" | ");
  }

  return "";
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail = normalizeDetail(payload);
    } catch {
      const message = await response.text();
      detail = message || "";
    }

    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      const retryHint = retryAfter ? ` Please retry in about ${retryAfter} seconds.` : " Please retry shortly.";
      const error = new Error(`AI provider is busy right now.${retryHint}`);
      error.status = response.status;
      throw error;
    }

    const error = new Error(detail || `API request failed with status ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export function fetchQuestion(conceptId, topic) {
  const query = new URLSearchParams();
  if (conceptId) {
    query.set("concept_id", conceptId);
  }
  if (topic) {
    query.set("topic", topic);
  }
  return request(`/learning/question?${query.toString()}`);
}

export function fetchQuestionSet(conceptId, topic, count = 3) {
  const query = new URLSearchParams();
  if (conceptId) {
    query.set("concept_id", conceptId);
  }
  if (topic) {
    query.set("topic", topic);
  }
  query.set("count", String(count));
  return request(`/learning/questions?${query.toString()}`);
}

export function submitAttempt(payload) {
  return request("/learning/attempt", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchDashboard(userId) {
  return request(`/learning/dashboard/${encodeURIComponent(userId)}`);
}

export function signupUser(payload) {
  return request("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function generateDiagnosticQuestions(topic, userId) {
  return request("/diagnostic/generate", {
    method: "POST",
    body: JSON.stringify({ topic, user_id: userId }),
  });
}

export function analyzeDiagnosticResponses(topic, responses, userId) {
  return request("/diagnostic/analyze", {
    method: "POST",
    body: JSON.stringify({ topic, responses, user_id: userId }),
  });
}

export function saveUserProgress(payload) {
  return request("/user/progress", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getUserTopics(userId) {
  return request(`/user/topics/${encodeURIComponent(userId)}`);
}

export function getUserTopicDetails(userId, topic) {
  return request(`/user/topic/${encodeURIComponent(userId)}/${encodeURIComponent(topic)}`);
}

export function deleteUserTopic(userId, topic) {
  return request(`/user/topic/${encodeURIComponent(userId)}/${encodeURIComponent(topic)}`, {
    method: "DELETE",
  });
}
