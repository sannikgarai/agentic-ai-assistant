
import React from "react";

const IMAGE_TYPES = [
  "image/png",
  "image/jpeg",
  "image/webp",
];

function ChatWindow({ messages = [] }) {
  return (
    <div className="chat-window">

      {messages.length === 0 ? (
        <div className="chat-empty">

          <div className="empty-ai-icon">
            <img
              src="/assets/logo.png"
              alt="AI Assistant"
            />
          </div>

          <h2>How can I help you?</h2>

          <p>
            Ask me about government schemes, documents,
            eligibility, applications, or any other information.
          </p>

          <div className="suggestion-grid">

            <div className="suggestion-card">
              <img
                src="/assets/icons/document.svg"
                alt=""
              />
              <span>Find government schemes</span>
            </div>

            <div className="suggestion-card">
              <img
                src="/assets/icons/document.svg"
                alt=""
              />
              <span>Check required documents</span>
            </div>

            <div className="suggestion-card">
              <span className="suggestion-symbol">
                🔎
              </span>
              <span>Check eligibility</span>
            </div>

            <div className="suggestion-card">
              <span className="suggestion-symbol">
                📝
              </span>
              <span>Help with applications</span>
            </div>

          </div>

        </div>
      ) : (
        <div className="messages-list">

          {messages.map((message, index) => (
            <div
              key={message.id || index}
              className={`message ${
                message.role === "user"
                  ? "user-message"
                  : "assistant-message"
              }`}
            >

              <div className="message-content">

                {/* =========================================
                    PNG / JPG / JPEG / WEBP
                ========================================== */}

                {IMAGE_TYPES.includes(
                  message.file_type
                ) &&
                  message.image_url && (
                    <img
                      src={message.image_url}
                      alt={
                        message.file_name ||
                        "Uploaded image"
                      }
                      className="chat-message-image"
                    />
                  )}

                {/* =========================================
                    PDF
                ========================================== */}

                {message.file_type ===
                  "application/pdf" &&
                  message.file_url && (
                    <a
                      href={message.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="chat-pdf-card"
                    >

                      <div className="chat-pdf-icon">
                        📄
                      </div>

                      <div className="chat-pdf-info">

                        <strong>
                          {message.file_name ||
                            "Uploaded PDF"}
                        </strong>

                        <span>
                          PDF
                          {message.file_size
                            ? ` • ${(
                                message.file_size /
                                (1024 * 1024)
                              ).toFixed(2)} MB`
                            : ""}
                        </span>

                      </div>

                    </a>
                  )}

                {/* =========================================
                    Text message
                ========================================== */}

                {message.content && (
                  <div className="chat-message-text">
                    {message.content}
                  </div>
                )}

              </div>

            </div>
          ))}

        </div>
      )}

    </div>
  );
}

export default ChatWindow;
