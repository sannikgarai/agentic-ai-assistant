
import React from "react";

function Navbar({ user, onMenuClick }) {
  return (
    <header className="navbar">
      <div className="navbar-left">
        <button
          className="menu-button"
          onClick={onMenuClick}
          aria-label="Open menu"
          type="button"
        >
          ☰
        </button>

        <div className="brand">
          <img
            src="/assets/logo.png"
            alt="Agentic AI Assistant"
            className="navbar-logo"
          />

          <div className="brand-text">
            <h2>Agentic AI Assistant</h2>
            <span>Multilingual Government Assistant</span>
          </div>
        </div>
      </div>

      <div className="navbar-right">
        <span className="status-dot"></span>
        <span className="status-text">Online</span>

        {user && (
          <div className="user-info">
            <div className="user-avatar">
              <img
                src="/assets/icons/user.svg"
                alt="User"
                className="user-icon"
              />
            </div>

            <span>{user.email}</span>
          </div>
        )}
      </div>
    </header>
  );
}

export default Navbar;

