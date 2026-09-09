import React, {
  useEffect,
  useRef,
  useState,
} from "react";

function VoiceButton({
  onRecordingComplete,
  disabled = false,
}) {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    return () => {
      if (
        mediaRecorderRef.current?.state === "recording"
      ) {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        setError(
          "Microphone is not supported by this browser."
        );
        return;
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      const mediaRecorder =
        new MediaRecorder(stream);

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(
          audioChunksRef.current,
          {
            type:
              mediaRecorder.mimeType ||
              "audio/webm",
          }
        );

        stream
          .getTracks()
          .forEach((track) => track.stop());

        if (onRecordingComplete) {
          onRecordingComplete(audioBlob);
        }
      };

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.start();

      setRecording(true);
    } catch (err) {
      console.error(
        "Microphone error:",
        err
      );

      setError(
        "Microphone permission is required."
      );

      setRecording(false);
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const handleClick = () => {
    if (disabled) return;

    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="voice-button-container">

      <button
        type="button"
        className={`voice-button ${
          recording ? "recording" : ""
        }`}
        onClick={handleClick}
        disabled={disabled}
        title={
          recording
            ? "Stop recording"
            : "Start voice input"
        }
        aria-label={
          recording
            ? "Stop recording"
            : "Start voice input"
        }
      >
        {recording ? (
          "⏹"
        ) : (
          <img
            src="/assets/icons/microphone.svg"
            alt="Microphone"
          />
        )}
      </button>

      {error && (
        <span className="voice-error">
          {error}
        </span>
      )}

    </div>
  );
}

export default VoiceButton;