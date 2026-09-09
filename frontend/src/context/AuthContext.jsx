
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import authService from "../services/authService";

// ==================================================
// Auth Context
// ==================================================

const AuthContext = createContext(null);

// ==================================================
// Auth Provider
// ==================================================

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  // ==================================================
  // Initialize Authentication
  // ==================================================

  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      try {
        const currentSession =
          await authService.getSession();

        if (!mounted) return;

        // TEMPORARY: Get access token for Swagger testing
        console.log(
          "ACCESS TOKEN:",
          currentSession?.access_token
        );

        setSession(currentSession);
        setUser(currentSession?.user || null);
      } catch (error) {
        console.error(
          "Authentication initialization error:",
          error
        );
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    initializeAuth();

    // ==================================================
    // Listen for Supabase Authentication Changes
    // ==================================================

    const {
      data: { subscription },
    } = authService.onAuthStateChange(
      (_event, newSession) => {
        if (!mounted) return;

        setSession(newSession);
        setUser(newSession?.user || null);
        setLoading(false);
      }
    );

    // ==================================================
    // Cleanup
    // ==================================================

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  // ==================================================
  // Register
  // ==================================================

  const register = async (
    email,
    password,
    metadata = {}
  ) => {
    setLoading(true);

    try {
      const data =
        await authService.register(
          email,
          password,
          metadata
        );

      setSession(data?.session || null);
      setUser(data?.user || null);

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(
        "Registration error:",
        error
      );

      return {
        success: false,
        error:
          error?.message ||
          "Registration failed",
      };
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Login
  // ==================================================

  const login = async (
    email,
    password
  ) => {
    setLoading(true);

    try {
      const data =
        await authService.login(
          email,
          password
        );

      setSession(data?.session || null);
      setUser(data?.user || null);

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(
        "Login error:",
        error
      );

      return {
        success: false,
        error:
          error?.message ||
          "Login failed",
      };
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Logout
  // ==================================================

  const logout = async () => {
    setLoading(true);

    try {
      await authService.logout();

      setUser(null);
      setSession(null);

      return {
        success: true,
      };
    } catch (error) {
      console.error(
        "Logout error:",
        error
      );

      return {
        success: false,
        error:
          error?.message ||
          "Logout failed",
      };
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Send OTP
  // ==================================================

  const sendOtp = async (email) => {
    setLoading(true);

    try {
      const data =
        await authService.sendOtp(
          email
        );

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(
        "OTP sending error:",
        error
      );

      return {
        success: false,
        error:
          error?.message ||
          "Failed to send OTP",
      };
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Verify OTP
  // ==================================================

  const verifyOtp = async (
    email,
    token
  ) => {
    setLoading(true);

    try {
      const data =
        await authService.verifyOtp(
          email,
          token
        );

      setSession(data?.session || null);
      setUser(data?.user || null);

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(
        "OTP verification error:",
        error
      );

      return {
        success: false,
        error:
          error?.message ||
          "OTP verification failed",
      };
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Reset Password
  // ==================================================

  const resetPassword = async (email) => {
    setLoading(true);

    try {
      const data =
        await authService.resetPassword(
          email
        );

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error(
        "Password reset error:",
        error
      );

      return {
        success: false,
        error:
          error?.message ||
          "Password reset failed",
      };
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // Context Value
  // ==================================================

  const value = {
    user,
    session,
    loading,
    isAuthenticated: Boolean(user),

    register,
    login,
    logout,

    sendOtp,
    verifyOtp,

    resetPassword,
  };

  // ==================================================
  // Provider
  // ==================================================

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ==================================================
// useAuth Hook
// ==================================================

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}

// ==================================================
// Default Export
// ==================================================

export default AuthContext;

