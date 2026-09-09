import React, { useState } from "react";

import ChatWindow from "../components/ChatWindow";
import ChatInput from "../components/ChatInput";
import LanguageSelector from "../components/LanguageSelector";

import { useChat } from "../context/ChatContext";

function Chat() {
  const {
    messages,
    language,
    changeLanguage,
    sendMessage,
    loading,
    error,
  } = useChat();

  const [voiceError, setVoiceError] =
    useState(null);

  const handleSend = async ({
    text,
    file,
    audio,
  }) => {
    console.log(
      "========== MESSAGE SENT =========="
    );

    console.log("Text:", text);
    console.log("Document:", file);
    console.log("Audio:", audio);
    console.log("Language:", language);

    console.log("=================================");

    setVoiceError(null);

    // --------------------------------------------------
    // Text + Image OR Text only OR Image only
    // --------------------------------------------------

    if (text?.trim() || file) {
      console.log(
        "Sending message with text and/or file"
      );

      await sendMessage(
        text?.trim() || "",
        {
          documentIds: [],
          file: file || null,
        }
      );

      return;
    }

    // --------------------------------------------------
    // Audio should NOT be processed here.
    //
    // ChatInput converts voice -> text first.
    // --------------------------------------------------

    if (audio) {
      console.warn(
        "Audio received in Chat.jsx unexpectedly."
      );
    }
  };

  return (
    <div className="page chat-page">

      <div className="chat-header">

        <div className="chat-header-left">

          <img
            src="/assets/logo.png"
            alt="AI Assistant"
            className="chat-logo"
          />

          <div>
            <h1>AI Assistant</h1>

            <p>
              Ask questions about government
              services and schemes.
            </p>
          </div>

        </div>

        <LanguageSelector
          value={language}
          onChange={changeLanguage}
        />

      </div>

      {error && (
        <div className="chat-error">
          {error}
        </div>
      )}

      {voiceError && (
        <div className="chat-error">
          {voiceError}
        </div>
      )}

      <ChatWindow
        messages={messages}
      />

      <ChatInput
        language={language}
        onSend={handleSend}
      />

      {loading && (
        <div className="chat-loading">
          AI is thinking...
        </div>
      )}

    </div>
  );
}

export default Chat;