import React from "react";

function Sidebar({ activePage = "Chat", onClose }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h3>Assistant</h3>

        <button
          className="close-button"
          onClick={onClose}
          aria-label="Close sidebar"
          type="button"
        >
          ×
        </button>
      </div>

      <nav className="sidebar-menu">
        <button
          type="button"
          className={`sidebar-item ${
            activePage === "Chat" ? "active" : ""
          }`}
        >
          <span className="sidebar-icon">💬</span>
          <span>Chat</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="ai-status">
          <span className="status-dot"></span>

          <div>
            <strong>AI Assistant</strong>
            <small>Ready to help</small>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;