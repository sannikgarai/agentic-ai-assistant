
import React from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";

import { useAuth } from "./context/AuthContext";

// ==================================================
// Protected Route
// ==================================================

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-loading">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// ==================================================
// Public Route
// ==================================================

function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-loading">
        <p>Loading...</p>
      </div>
    );
  }

  // If already logged in, go directly to Chat.
  if (user) {
    return <Navigate to="/chat" replace />;
  }

  return children;
}

// ==================================================
// App
// ==================================================

function App() {
  return (
    <BrowserRouter>
      <Routes>

        {/* =========================================
            First Page → Login
        ========================================= */}
        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        {/* =========================================
            Login
        ========================================= */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />

        {/* =========================================
            Register
        ========================================= */}
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* =========================================
            Chat — Only Protected Page
        ========================================= */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          }
        />

        {/* =========================================
            All Other Routes → Chat if logged in,
            otherwise → Login
        ========================================= */}
        <Route
          path="*"
          element={<Navigate to="/chat" replace />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default App;
