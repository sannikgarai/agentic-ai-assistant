import React, { useState } from "react";
import VoiceButton from "./VoiceButton";
import FileUpload from "./FileUpload";
import voiceService from "../services/voiceService";
import { useAuth } from "../context/AuthContext";

function ChatInput({ onSend, language = "en" }) {
  const { session } = useAuth();

  const [message, setMessage] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const [isTranscribing, setIsTranscribing] =
    useState(false);

  const [voiceError, setVoiceError] =
    useState("");

  // --------------------------------------------------
  // Send text / file
  // --------------------------------------------------

  const handleSubmit = async (e) => {
    e.preventDefault();

    const text = message.trim();

    if (!text && !selectedFile) {
      return;
    }

    if (!onSend) {
      return;
    }

    // Clear input immediately after submit
    setMessage("");
    setSelectedFile(null);
    setShowUpload(false);

    try {
      await onSend({
        text,
        file: selectedFile,
        audio: null,
      });
    } catch (err) {
      console.error(
        "Chat submit error:",
        err
      );
    }
  };

  // --------------------------------------------------
  // Keyboard
  // --------------------------------------------------

  const handleKeyDown = (e) => {
    if (
      e.key === "Enter" &&
      !e.shiftKey &&
      !isTranscribing
    ) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // --------------------------------------------------
  // Voice recording complete
  // --------------------------------------------------

  const handleVoice = async (audioBlob) => {
    if (!audioBlob) {
      return;
    }

    console.log(
      "========== VOICE RECEIVED =========="
    );

    console.log("Blob:", audioBlob);
    console.log(
      "Is Blob:",
      audioBlob instanceof Blob
    );
    console.log(
      "Size:",
      audioBlob.size
    );
    console.log(
      "Type:",
      audioBlob.type
    );

    console.log(
      "===================================="
    );

    setVoiceError("");
    setIsTranscribing(true);

    try {
      const token =
        session?.access_token || null;

      console.log(
        "Sending audio to transcription API..."
      );

      const result =
        await voiceService.speechToText(
          audioBlob,
          language || "auto",
          token
        );

      console.log(
        "========== TRANSCRIPTION RESULT =========="
      );

      console.log("Result:", result);

      console.log(
        "=========================================="
      );

      const transcript =
        result?.transcript ||
        result?.text ||
        "";

      if (!transcript.trim()) {
        throw new Error(
          result?.message ||
            "Could not understand the voice recording."
        );
      }

      // Put transcription into normal input.
      // Do not submit automatically.
      setMessage((previous) => {
        if (!previous.trim()) {
          return transcript.trim();
        }

        return `${previous.trim()} ${transcript.trim()}`;
      });

      console.log(
        "Transcript inserted into text input:",
        transcript
      );
    } catch (err) {
      console.error(
        "Voice transcription error:",
        err
      );

      setVoiceError(
        err.message ||
          "Unable to convert voice to text."
      );
    } finally {
      setIsTranscribing(false);
    }
  };

  // --------------------------------------------------
  // File selected
  // --------------------------------------------------

  const handleFile = (file) => {
    console.log(
      "Selected file:",
      file
    );

    setSelectedFile(file);
    setShowUpload(false);
  };

  const canSubmit =
    Boolean(message.trim()) ||
    Boolean(selectedFile);

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div className="chat-input-area">

      {showUpload && (
        <div className="chat-upload-panel">
          <FileUpload
            onFileSelect={handleFile}
          />
        </div>
      )}

      {voiceError && (
        <div className="chat-error">
          {voiceError}
        </div>
      )}

      <form
        className="chat-input"
        onSubmit={handleSubmit}
      >

        {/* Upload */}
        <button
          type="button"
          className="chat-action-button"
          onClick={() =>
            setShowUpload(
              (previous) => !previous
            )
          }
          disabled={isTranscribing}
          title="Upload document"
          aria-label="Upload document"
        >
          <img
            src="/assets/icons/upload.svg"
            alt="Upload"
          />
        </button>

        {/* Text input */}
        <textarea
          value={message}
          onChange={(e) =>
            setMessage(e.target.value)
          }
          onKeyDown={handleKeyDown}
          disabled={isTranscribing}
          placeholder={
            isTranscribing
              ? "Converting voice to text..."
              : selectedFile
              ? `Document: ${selectedFile.name}`
              : "Ask about government schemes, eligibility, documents..."
          }
          rows={1}
        />

        {/* Microphone */}
        <div className="chat-voice-wrapper">
          <VoiceButton
            onRecordingComplete={handleVoice}
            disabled={isTranscribing}
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="chat-send-button"
          disabled={
            !canSubmit ||
            isTranscribing
          }
          title="Send"
          aria-label="Send"
        >
          ➤
        </button>

      </form>

      <div className="chat-input-help">
        Press <strong>Enter</strong> to send
        <span>•</span>
        <strong>Shift + Enter</strong> for a new line
      </div>

    </div>
  );
}

export default ChatInput;