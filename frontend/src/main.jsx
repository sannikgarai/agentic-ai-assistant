
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App.jsx";
import "./index.css";

import { AuthProvider } from "./context/AuthContext";
import { ChatProvider } from "./context/ChatContext";


// ============================================================
// React Application Entry Point
// ============================================================

ReactDOM.createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>

    {/* Authentication State */}
    <AuthProvider>

      {/* Chat / Conversation State */}
      <ChatProvider>

        {/* Main Application */}
        <App />

      </ChatProvider>

    </AuthProvider>

  </React.StrictMode>
);
