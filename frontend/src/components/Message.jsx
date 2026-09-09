
import React from "react";

function Message({ message }) {
  const isUser = message?.role === "user";

  return (
    <div className={`message-row ${isUser ? "user-message" : "ai-message"}`}>
      <div className="message-avatar">
        {isUser ? "U" : "AI"}
      </div>

      <div className="message-content">
        <div className="message-header">
          <strong>{isUser ? "You" : "Assistant"}</strong>

          {message?.timestamp && (
            <span className="message-time">
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          )}
        </div>

        <div className="message-bubble">
          {message?.content || ""}
        </div>

        {message?.sources?.length > 0 && (
          <div className="message-sources">
            <strong>Sources:</strong>

            {message.sources.map((source, index) => (
              <div key={index} className="source-item">
                📄 {source.title || `Source ${index + 1}`}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Message;

