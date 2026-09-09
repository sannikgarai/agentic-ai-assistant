import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Register() {
  const navigate = useNavigate();
  const { register, loading } = useAuth();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");

    const name = formData.name.trim();
    const email = formData.email.trim();
    const password = formData.password;
    const confirmPassword = formData.confirmPassword;

    if (!name || !email || !password || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    const result = await register(email, password, {
      full_name: name,
    });

    if (!result.success) {
      setError(result.error || "Registration failed.");
      return;
    }

    /*
     * If Supabase email confirmation is enabled,
     * the session will be null until the user confirms
     * their email.
     */
    if (!result.data?.session) {
      setSuccess(
        "Registration successful. Please check your email to confirm your account."
      );
      return;
    }

    setSuccess("Registration successful. Redirecting...");

    setTimeout(() => {
      navigate("/chat");
    }, 500);
  };

  return (
    <div style={styles.page}>
      {/* Background Decoration */}
      <div style={styles.backgroundOrb1}></div>
      <div style={styles.backgroundOrb2}></div>
      <div style={styles.backgroundOrb3}></div>

      <div style={styles.container}>
        {/* Left Hero Section */}
        <div style={styles.heroSection}>
          <div style={styles.heroContent}>
            <div style={styles.logoWrapper}>
              <img
                src="/assets/logo.png"
                alt="AI Assistant"
                style={styles.logo}
              />
            </div>

            <h1 style={styles.heroTitle}>
              Start Your
              <span style={styles.gradientText}> AI Journey</span>
            </h1>

            <p style={styles.heroDescription}>
              Create your account and unlock an intelligent assistant designed
              to help you with documents, voice, government services,
              verification, and automated tasks.
            </p>

            <div style={styles.features}>
              <Feature
                icon="✦"
                title="AI Powered"
                description="Intelligent assistance whenever you need it"
              />

              <Feature
                icon="◎"
                title="Multilingual"
                description="Communicate naturally in your language"
              />

              <Feature
                icon="✓"
                title="Secure"
                description="Your account and information stay protected"
              />
            </div>
          </div>
        </div>

        {/* Register Card */}
        <div style={styles.cardWrapper}>
          <div style={styles.card}>
            {/* Header */}
            <div style={styles.cardHeader}>
              <div style={styles.mobileLogoWrapper}>
                <img
                  src="/assets/logo.png"
                  alt="AI Assistant"
                  style={styles.mobileLogo}
                />
              </div>

              <h2 style={styles.title}>Create Account</h2>

              <p style={styles.subtitle}>
                Join your intelligent AI Assistant
              </p>
            </div>

            {/* Error */}
            {error && (
              <div style={styles.errorBox} role="alert">
                <span style={styles.messageIcon}>!</span>
                <span>{error}</span>
              </div>
            )}

            {/* Success */}
            {success && (
              <div style={styles.successBox} role="status">
                <span style={styles.messageIcon}>✓</span>
                <span>{success}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit}>
              {/* Full Name */}
              <div style={styles.formGroup}>
                <label htmlFor="name" style={styles.label}>
                  Full Name
                </label>

                <div style={styles.inputWrapper}>
                  <span style={styles.inputIcon}>♙</span>

                  <input
                    id="name"
                    name="name"
                    type="text"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Enter your full name"
                    autoComplete="name"
                    disabled={loading}
                    required
                    style={styles.input}
                  />
                </div>
              </div>

              {/* Email */}
              <div style={styles.formGroup}>
                <label htmlFor="email" style={styles.label}>
                  Email Address
                </label>

                <div style={styles.inputWrapper}>
                  <span style={styles.inputIcon}>✉</span>

                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Enter your email"
                    autoComplete="email"
                    disabled={loading}
                    required
                    style={styles.input}
                  />
                </div>
              </div>

              {/* Password */}
              <div style={styles.formGroup}>
                <label htmlFor="password" style={styles.label}>
                  Password
                </label>

                <div style={styles.inputWrapper}>
                  <span style={styles.inputIcon}>◆</span>

                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Create a password"
                    autoComplete="new-password"
                    disabled={loading}
                    required
                    style={styles.passwordInput}
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword((prev) => !prev)
                    }
                    disabled={loading}
                    style={styles.eyeButton}
                    aria-label={
                      showPassword ? "Hide password" : "Show password"
                    }
                  >
                    {showPassword ? "◉" : "○"}
                  </button>
                </div>

                <p style={styles.passwordHint}>
                  Minimum 6 characters
                </p>
              </div>

              {/* Confirm Password */}
              <div style={styles.formGroup}>
                <label htmlFor="confirmPassword" style={styles.label}>
                  Confirm Password
                </label>

                <div style={styles.inputWrapper}>
                  <span style={styles.inputIcon}>◆</span>

                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={
                      showConfirmPassword ? "text" : "password"
                    }
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="Confirm your password"
                    autoComplete="new-password"
                    disabled={loading}
                    required
                    style={styles.passwordInput}
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowConfirmPassword((prev) => !prev)
                    }
                    disabled={loading}
                    style={styles.eyeButton}
                    aria-label={
                      showConfirmPassword
                        ? "Hide password"
                        : "Show password"
                    }
                  >
                    {showConfirmPassword ? "◉" : "○"}
                  </button>
                </div>
              </div>

              {/* Register Button */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  ...styles.registerButton,
                  ...(loading
                    ? styles.registerButtonDisabled
                    : {}),
                }}
              >
                {loading ? (
                  <>
                    <span style={styles.spinner}></span>
                    Creating Account...
                  </>
                ) : (
                  <>
                    Create Account
                    <span style={styles.arrow}>→</span>
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div style={styles.divider}>
              <span style={styles.dividerLine}></span>
              <span style={styles.dividerText}>OR</span>
              <span style={styles.dividerLine}></span>
            </div>

            {/* Login */}
            <div style={styles.loginSection}>
              <p style={styles.loginText}>
                Already have an account?
              </p>

              <Link to="/login" style={styles.loginLink}>
                Login
                <span style={styles.loginArrow}>→</span>
              </Link>
            </div>

            {/* Security */}
            <div style={styles.security}>
              <span>🔒</span>
              <span>Secure authentication powered by Supabase</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        © 2026 AI Assistant. Intelligent. Secure. Connected.
      </div>
    </div>
  );
}

/* =========================================================
   Feature Component
========================================================= */

function Feature({ icon, title, description }) {
  return (
    <div style={styles.feature}>
      <div style={styles.featureIcon}>{icon}</div>

      <div>
        <h3 style={styles.featureTitle}>{title}</h3>

        <p style={styles.featureDescription}>{description}</p>
      </div>
    </div>
  );
}

/* =========================================================
   Styles
========================================================= */

const styles = {
  page: {
    minHeight: "100vh",
    width: "100%",
    position: "relative",
    overflow: "hidden",
    background:
      "linear-gradient(135deg, #07111f 0%, #0b1728 45%, #101d35 100%)",
    color: "#ffffff",
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    display: "flex",
    flexDirection: "column",
  },

  backgroundOrb1: {
    position: "absolute",
    width: "420px",
    height: "420px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle, rgba(79, 70, 229, 0.28) 0%, rgba(79, 70, 229, 0) 70%)",
    top: "-180px",
    left: "-120px",
    pointerEvents: "none",
  },

  backgroundOrb2: {
    position: "absolute",
    width: "500px",
    height: "500px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle, rgba(6, 182, 212, 0.20) 0%, rgba(6, 182, 212, 0) 70%)",
    right: "-180px",
    bottom: "-180px",
    pointerEvents: "none",
  },

  backgroundOrb3: {
    position: "absolute",
    width: "300px",
    height: "300px",
    borderRadius: "50%",
    background:
      "radial-gradient(circle, rgba(168, 85, 247, 0.16) 0%, rgba(168, 85, 247, 0) 70%)",
    right: "25%",
    top: "15%",
    pointerEvents: "none",
  },

  container: {
    position: "relative",
    zIndex: 2,
    width: "100%",
    maxWidth: "1180px",
    margin: "auto",
    padding: "35px 24px",
    display: "grid",
    gridTemplateColumns: "1fr 460px",
    alignItems: "center",
    gap: "80px",
    boxSizing: "border-box",
  },

  heroSection: {
    display: "flex",
    alignItems: "center",
  },

  heroContent: {
    maxWidth: "580px",
  },

  logoWrapper: {
    width: "72px",
    height: "72px",
    borderRadius: "20px",
    padding: "10px",
    marginBottom: "27px",
    background: "rgba(255, 255, 255, 0.08)",
    border: "1px solid rgba(255, 255, 255, 0.12)",
    boxShadow: "0 15px 40px rgba(0, 0, 0, 0.25)",
    boxSizing: "border-box",
  },

  logo: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
    borderRadius: "12px",
  },

  heroTitle: {
    fontSize: "50px",
    lineHeight: "1.08",
    letterSpacing: "-2px",
    margin: "0 0 22px",
    fontWeight: 750,
  },

  gradientText: {
    display: "block",
    background:
      "linear-gradient(90deg, #818cf8, #22d3ee, #a78bfa)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },

  heroDescription: {
    fontSize: "16px",
    lineHeight: "1.75",
    color: "#aab7cc",
    margin: "0 0 34px",
    maxWidth: "540px",
  },

  features: {
    display: "flex",
    flexDirection: "column",
    gap: "17px",
  },

  feature: {
    display: "flex",
    alignItems: "center",
    gap: "15px",
  },

  featureIcon: {
    width: "40px",
    height: "40px",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(99, 102, 241, 0.15)",
    border: "1px solid rgba(129, 140, 248, 0.18)",
    color: "#a5b4fc",
    fontSize: "17px",
    flexShrink: 0,
  },

  featureTitle: {
    margin: "0 0 3px",
    fontSize: "14px",
    fontWeight: 650,
  },

  featureDescription: {
    margin: 0,
    fontSize: "12px",
    color: "#78869d",
  },

  cardWrapper: {
    width: "100%",
  },

  card: {
    width: "100%",
    padding: "36px",
    borderRadius: "26px",
    background: "rgba(17, 27, 45, 0.80)",
    border: "1px solid rgba(255, 255, 255, 0.10)",
    boxShadow:
      "0 30px 80px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255,255,255,0.04)",
    backdropFilter: "blur(24px)",
    WebkitBackdropFilter: "blur(24px)",
    boxSizing: "border-box",
  },

  cardHeader: {
    textAlign: "center",
    marginBottom: "26px",
  },

  mobileLogoWrapper: {
    display: "none",
  },

  mobileLogo: {
    width: "50px",
    height: "50px",
    objectFit: "contain",
  },

  title: {
    margin: "0 0 8px",
    fontSize: "29px",
    fontWeight: 700,
    letterSpacing: "-0.6px",
  },

  subtitle: {
    margin: 0,
    fontSize: "13px",
    color: "#8492a8",
    lineHeight: "1.6",
  },

  errorBox: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "11px 13px",
    marginBottom: "18px",
    borderRadius: "12px",
    background: "rgba(239, 68, 68, 0.10)",
    border: "1px solid rgba(239, 68, 68, 0.25)",
    color: "#fca5a5",
    fontSize: "12px",
  },

  successBox: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "11px 13px",
    marginBottom: "18px",
    borderRadius: "12px",
    background: "rgba(34, 197, 94, 0.10)",
    border: "1px solid rgba(34, 197, 94, 0.25)",
    color: "#86efac",
    fontSize: "12px",
  },

  messageIcon: {
    width: "21px",
    height: "21px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(255, 255, 255, 0.08)",
    fontSize: "10px",
    fontWeight: 700,
    flexShrink: 0,
  },

  formGroup: {
    marginBottom: "15px",
  },

  label: {
    display: "block",
    marginBottom: "8px",
    fontSize: "12px",
    fontWeight: 600,
    color: "#d6deeb",
  },

  inputWrapper: {
    display: "flex",
    alignItems: "center",
    height: "48px",
    borderRadius: "12px",
    background: "rgba(5, 12, 24, 0.58)",
    border: "1px solid rgba(255, 255, 255, 0.09)",
    boxSizing: "border-box",
  },

  inputIcon: {
    width: "42px",
    textAlign: "center",
    color: "#66758c",
    fontSize: "13px",
    flexShrink: 0,
  },

  input: {
    width: "100%",
    height: "100%",
    border: "none",
    outline: "none",
    background: "transparent",
    color: "#ffffff",
    fontSize: "13px",
    padding: "0 14px 0 0",
    boxSizing: "border-box",
  },

  passwordInput: {
    width: "100%",
    height: "100%",
    border: "none",
    outline: "none",
    background: "transparent",
    color: "#ffffff",
    fontSize: "13px",
    padding: "0 4px 0 0",
    boxSizing: "border-box",
  },

  eyeButton: {
    border: "none",
    background: "transparent",
    color: "#66758c",
    cursor: "pointer",
    fontSize: "14px",
    width: "42px",
    height: "100%",
    flexShrink: 0,
  },

  passwordHint: {
    margin: "6px 0 0 3px",
    color: "#5e6d83",
    fontSize: "10px",
  },

  registerButton: {
    width: "100%",
    height: "51px",
    marginTop: "5px",
    border: "none",
    borderRadius: "12px",
    background:
      "linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #06b6d4 100%)",
    color: "#ffffff",
    fontSize: "13px",
    fontWeight: 650,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    boxShadow: "0 12px 28px rgba(79, 70, 229, 0.28)",
  },

  registerButtonDisabled: {
    opacity: 0.65,
    cursor: "not-allowed",
  },

  arrow: {
    fontSize: "18px",
    lineHeight: 1,
  },

  spinner: {
    width: "15px",
    height: "15px",
    border: "2px solid rgba(255,255,255,0.35)",
    borderTopColor: "#ffffff",
    borderRadius: "50%",
    display: "inline-block",
  },

  divider: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    margin: "23px 0",
  },

  dividerLine: {
    height: "1px",
    flex: 1,
    background: "rgba(255,255,255,0.08)",
  },

  dividerText: {
    color: "#64748b",
    fontSize: "9px",
    fontWeight: 600,
  },

  loginSection: {
    textAlign: "center",
  },

  loginText: {
    display: "inline",
    margin: 0,
    color: "#7f8da3",
    fontSize: "12px",
  },

  loginLink: {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    marginLeft: "6px",
    color: "#a5b4fc",
    textDecoration: "none",
    fontSize: "12px",
    fontWeight: 600,
  },

  loginArrow: {
    fontSize: "15px",
  },

  security: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: "6px",
    marginTop: "22px",
    color: "#58667b",
    fontSize: "9px",
  },

  footer: {
    position: "relative",
    zIndex: 2,
    textAlign: "center",
    padding: "0 20px 18px",
    color: "#526078",
    fontSize: "9px",
  },
};

export default Register;