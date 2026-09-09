
const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

async function request(endpoint, options = {}) {
  const {
    method = "GET",
    body,
    token,
    headers = {},
  } = options;

  const requestHeaders = {
    ...headers,
  };

  // Set JSON content type automatically
  if (
    body &&
    !(body instanceof FormData)
  ) {
    requestHeaders["Content-Type"] =
      "application/json";
  }

  // Send Supabase access token to backend
  if (token) {
    requestHeaders.Authorization =
      `Bearer ${token}`;
  }

  const url = `${API_URL}${endpoint}`;

  // Temporary debugging
  console.log("========== API REQUEST ==========");
  console.log("URL:", url);
  console.log("Method:", method);
  console.log(
    "Token exists:",
    Boolean(token)
  );
  console.log("Body:", body);
  console.log("=================================");

  try {
    const response = await fetch(url, {
      method,
      headers: requestHeaders,
      body:
        body instanceof FormData
          ? body
          : body
            ? JSON.stringify(body)
            : undefined,
    });

    console.log("========== API RESPONSE ==========");
    console.log("Status:", response.status);
    console.log("OK:", response.ok);
    console.log("==================================");

    let data = null;

    const contentType =
      response.headers.get("content-type");

    if (
      contentType &&
      contentType.includes(
        "application/json"
      )
    ) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    console.log("Response data:", data);

    if (!response.ok) {
      const message =
        typeof data === "object" &&
        data?.detail
          ? data.detail
          : "API request failed";

      throw new Error(message);
    }

    return data;
  } catch (error) {
    console.error(
      "========== API ERROR =========="
    );
    console.error(error);
    console.error(
      "================================"
    );

    throw error;
  }
}

export const api = {
  // GET request
  get(endpoint, options = {}) {
    return request(endpoint, {
      ...options,
      method: "GET",
    });
  },

  // POST request
  post(endpoint, body, options = {}) {
    return request(endpoint, {
      ...options,
      method: "POST",
      body,
    });
  },

  // PUT request
  put(endpoint, body, options = {}) {
    return request(endpoint, {
      ...options,
      method: "PUT",
      body,
    });
  },

  // PATCH request
  patch(endpoint, body, options = {}) {
    return request(endpoint, {
      ...options,
      method: "PATCH",
      body,
    });
  },

  // DELETE request
  delete(endpoint, options = {}) {
    return request(endpoint, {
      ...options,
      method: "DELETE",
    });
  },

  // File upload
  upload(endpoint, formData, options = {}) {
    return request(endpoint, {
      ...options,
      method: "POST",
      body: formData,
    });
  },
};

export { API_URL };

export default api;

