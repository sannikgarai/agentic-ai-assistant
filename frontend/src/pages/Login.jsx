import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Login() {
  const navigate = useNavigate();
  const { login, loading } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);

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

    const email = formData.email.trim();
    const password = formData.password;

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    const result = await login(email, password);

    if (!result.success) {
      setError(result.error || "Login failed.");
      return;
    }

    setSuccess("Login successful. Redirecting...");

    setTimeout(() => {
      navigate("/chat");
    }, 500);
  };

  return (
    <div style={styles.page}>
      {/* Background decoration */}
      <div style={styles.backgroundOrb1}></div>
      <div style={styles.backgroundOrb2}></div>
      <div style={styles.backgroundOrb3}></div>

      {/* Main Container */}
      <div style={styles.container}>
        {/* Left Side */}
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
              Your Intelligent
              <span style={styles.gradientText}> AI Assistant</span>
            </h1>

            <p style={styles.heroDescription}>
              One powerful assistant for documents, voice, government
              services, verification, and intelligent task automation.
            </p>

            <div style={styles.features}>
              <Feature
                icon="✦"
                title="Intelligent"
                description="AI-powered assistance"
              />

              <Feature
                icon="◉"
                title="Multilingual"
                description="Communicate in your language"
              />

              <Feature
                icon="✓"
                title="Secure"
                description="Your data stays protected"
              />
            </div>
          </div>
        </div>

        {/* Login Card */}
        <div style={styles.cardWrapper}>
          <div style={styles.card}>
            {/* Card Header */}
            <div style={styles.cardHeader}>
              <div style={styles.mobileLogoWrapper}>
                <img
                  src="/assets/logo.png"
                  alt="AI Assistant"
                  style={styles.mobileLogo}
                />
              </div>

              <h2 style={styles.title}>Welcome Back</h2>

              <p style={styles.subtitle}>
                Sign in to continue to your AI Assistant
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
                    placeholder="Enter your password"
                    autoComplete="current-password"
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
                      showPassword
                        ? "Hide password"
                        : "Show password"
                    }
                  >
                    {showPassword ? "◉" : "○"}
                  </button>
                </div>
              </div>

              {/* Login Button */}
              <button
                type="submit"
                disabled={loading}
                style={{
                  ...styles.loginButton,
                  ...(loading
                    ? styles.loginButtonDisabled
                    : {}),
                }}
              >
                {loading ? (
                  <>
                    <span style={styles.spinner}></span>
                    Logging in...
                  </>
                ) : (
                  <>
                    Login
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

            {/* Register */}
            <div style={styles.registerSection}>
              <p style={styles.registerText}>
                Don't have an account?
              </p>

              <Link
                to="/register"
                style={styles.registerLink}
              >
                Create an account
                <span style={styles.registerArrow}>→</span>
              </Link>
            </div>

            {/* Security */}
            <div style={styles.security}>
              <span>🔒</span>
              <span>
                Secure authentication powered by Supabase
              </span>
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

/* ==================================================
   Feature Component
================================================== */

function Feature({ icon, title, description }) {
  return (
    <div style={styles.feature}>
      <div style={styles.featureIcon}>{icon}</div>

      <div>
        <h3 style={styles.featureTitle}>{title}</h3>

        <p style={styles.featureDescription}>
          {description}
        </p>
      </div>
    </div>
  );
}

/* ==================================================
   Styles
================================================== */

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
    padding: "40px 24px",
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
    marginBottom: "28px",
    background: "rgba(255, 255, 255, 0.08)",
    border: "1px solid rgba(255, 255, 255, 0.12)",
    boxShadow:
      "0 15px 40px rgba(0, 0, 0, 0.25)",
    boxSizing: "border-box",
  },

  logo: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
    borderRadius: "12px",
  },

  heroTitle: {
    fontSize: "52px",
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
    fontSize: "17px",
    lineHeight: "1.75",
    color: "#aab7cc",
    margin: "0 0 36px",
    maxWidth: "530px",
  },

  features: {
    display: "flex",
    flexDirection: "column",
    gap: "18px",
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
    background:
      "rgba(99, 102, 241, 0.15)",
    border:
      "1px solid rgba(129, 140, 248, 0.18)",
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
    padding: "38px",
    borderRadius: "26px",
    background:
      "rgba(17, 27, 45, 0.78)",
    border:
      "1px solid rgba(255, 255, 255, 0.10)",
    boxShadow:
      "0 30px 80px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255,255,255,0.04)",
    backdropFilter: "blur(24px)",
    WebkitBackdropFilter: "blur(24px)",
    boxSizing: "border-box",
  },

  cardHeader: {
    textAlign: "center",
    marginBottom: "30px",
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
    margin: "0 0 9px",
    fontSize: "30px",
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
    padding: "12px 14px",
    marginBottom: "20px",
    borderRadius: "12px",
    background:
      "rgba(239, 68, 68, 0.10)",
    border:
      "1px solid rgba(239, 68, 68, 0.25)",
    color: "#fca5a5",
    fontSize: "13px",
  },

  successBox: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "12px 14px",
    marginBottom: "20px",
    borderRadius: "12px",
    background:
      "rgba(34, 197, 94, 0.10)",
    border:
      "1px solid rgba(34, 197, 94, 0.25)",
    color: "#86efac",
    fontSize: "13px",
  },

  messageIcon: {
    width: "22px",
    height: "22px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background:
      "rgba(255, 255, 255, 0.08)",
    fontSize: "11px",
    fontWeight: 700,
    flexShrink: 0,
  },

  formGroup: {
    marginBottom: "20px",
  },

  label: {
    display: "block",
    marginBottom: "9px",
    fontSize: "13px",
    fontWeight: 600,
    color: "#d6deeb",
  },

  inputWrapper: {
    display: "flex",
    alignItems: "center",
    height: "52px",
    borderRadius: "13px",
    background:
      "rgba(5, 12, 24, 0.58)",
    border:
      "1px solid rgba(255, 255, 255, 0.09)",
    transition: "all 0.2s ease",
    boxSizing: "border-box",
  },

  inputIcon: {
    width: "45px",
    textAlign: "center",
    color: "#66758c",
    fontSize: "14px",
    flexShrink: 0,
  },

  input: {
    width: "100%",
    height: "100%",
    border: "none",
    outline: "none",
    background: "transparent",
    color: "#ffffff",
    fontSize: "14px",
    padding: "0 15px 0 0",
    boxSizing: "border-box",
  },

  passwordInput: {
    width: "100%",
    height: "100%",
    border: "none",
    outline: "none",
    background: "transparent",
    color: "#ffffff",
    fontSize: "14px",
    padding: "0 5px 0 0",
    boxSizing: "border-box",
  },

  eyeButton: {
    border: "none",
    background: "transparent",
    color: "#66758c",
    cursor: "pointer",
    fontSize: "15px",
    width: "45px",
    height: "100%",
    flexShrink: 0,
  },

  loginButton: {
    width: "100%",
    height: "53px",
    marginTop: "8px",
    border: "none",
    borderRadius: "13px",
    background:
      "linear-gradient(135deg, #6366f1 0%, #4f46e5 50%, #06b6d4 100%)",
    color: "#ffffff",
    fontSize: "14px",
    fontWeight: 650,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    boxShadow:
      "0 12px 28px rgba(79, 70, 229, 0.28)",
  },

  loginButtonDisabled: {
    opacity: 0.65,
    cursor: "not-allowed",
  },

  arrow: {
    fontSize: "19px",
    lineHeight: 1,
  },

  spinner: {
    width: "16px",
    height: "16px",
    border:
      "2px solid rgba(255,255,255,0.35)",
    borderTopColor: "#ffffff",
    borderRadius: "50%",
    display: "inline-block",
  },

  divider: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    margin: "28px 0",
  },

  dividerLine: {
    height: "1px",
    flex: 1,
    background:
      "rgba(255,255,255,0.08)",
  },

  dividerText: {
    color: "#64748b",
    fontSize: "10px",
    fontWeight: 600,
  },

  registerSection: {
    textAlign: "center",
  },

  registerText: {
    display: "inline",
    margin: 0,
    color: "#7f8da3",
    fontSize: "13px",
  },

  registerLink: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    marginLeft: "6px",
    color: "#a5b4fc",
    textDecoration: "none",
    fontSize: "13px",
    fontWeight: 600,
  },

  registerArrow: {
    fontSize: "16px",
  },

  security: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: "7px",
    marginTop: "27px",
    color: "#58667b",
    fontSize: "10px",
  },

  footer: {
    position: "relative",
    zIndex: 2,
    textAlign: "center",
    padding: "0 20px 20px",
    color: "#526078",
    fontSize: "10px",
  },
};

export default Login;