
import { supabase } from "../lib/supabase";

const authService = {
  // ==================================================
  // Get Current Logged-in User
  // ==================================================

  async getCurrentUser() {
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser();

    if (error) {
      throw error;
    }

    return user;
  },

  // ==================================================
  // Get Current Session
  // ==================================================

  async getSession() {
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();

    if (error) {
      throw error;
    }

    return session;
  },

  // ==================================================
  // Register with Email + Password
  // ==================================================

  async register(
    email,
    password,
    metadata = {}
  ) {
    const {
      data,
      error,
    } = await supabase.auth.signUp({
      email,
      password,

      options: {
        data: metadata,
      },
    });

    if (error) {
      throw error;
    }

    return data;
  },

  // ==================================================
  // Login with Email + Password
  // ==================================================

  async login(email, password) {
    const {
      data,
      error,
    } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      throw error;
    }

    return data;
  },

  // ==================================================
  // Logout
  // ==================================================

  async logout() {
    const {
      error,
    } = await supabase.auth.signOut();

    if (error) {
      throw error;
    }

    return true;
  },

  // ==================================================
  // Send Email OTP / Magic Link
  // ==================================================

  async sendOtp(email) {
    const redirectTo = `${window.location.origin}/auth/callback`;

    const {
      data,
      error,
    } = await supabase.auth.signInWithOtp({
      email,

      options: {
        emailRedirectTo: redirectTo,
      },
    });

    if (error) {
      throw error;
    }

    return data;
  },

  // ==================================================
  // Verify Email OTP
  // ==================================================

  async verifyOtp(email, token) {
    const {
      data,
      error,
    } = await supabase.auth.verifyOtp({
      email,
      token,
      type: "email",
    });

    if (error) {
      throw error;
    }

    return data;
  },

  // ==================================================
  // Send Password Reset Email
  // ==================================================

  async resetPassword(email) {
    const redirectTo = `${window.location.origin}/reset-password`;

    const {
      data,
      error,
    } =
      await supabase.auth.resetPasswordForEmail(
        email,
        {
          redirectTo,
        }
      );

    if (error) {
      throw error;
    }

    return data;
  },

  // ==================================================
  // Listen to Authentication Changes
  // ==================================================

  onAuthStateChange(callback) {
    return supabase.auth.onAuthStateChange(
      callback
    );
  },

  // ==================================================
  // Update User
  // ==================================================

  async updateUser(attributes) {
    const {
      data,
      error,
    } = await supabase.auth.updateUser(
      attributes
    );

    if (error) {
      throw error;
    }

    return data;
  },
};

export default authService;

