
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import voiceService from "../services/voiceService";

export default function useVoice() {
  const [isRecording, setIsRecording] =
    useState(false);

  const [isProcessing, setIsProcessing] =
    useState(false);

  const [transcript, setTranscript] =
    useState("");

  const [error, setError] =
    useState(null);

  const [audioBlob, setAudioBlob] =
    useState(null);

  const [permissionDenied, setPermissionDenied] =
    useState(false);

  const mediaRecorderRef =
    useRef(null);

  const mediaStreamRef =
    useRef(null);

  const audioChunksRef =
    useRef([]);

  // --------------------------------------------------
  // Start recording
  // --------------------------------------------------
  const startRecording = useCallback(
    async () => {
      setError(null);
      setPermissionDenied(false);

      try {
        if (
          !navigator.mediaDevices ||
          !navigator.mediaDevices.getUserMedia
        ) {
          throw new Error(
            "Microphone is not supported by this browser."
          );
        }

        const stream =
          await navigator.mediaDevices.getUserMedia(
            {
              audio: true,
            }
          );

        mediaStreamRef.current = stream;

        const recorder =
          new MediaRecorder(stream);

        mediaRecorderRef.current =
          recorder;

        audioChunksRef.current = [];

        recorder.ondataavailable = (
          event
        ) => {
          if (
            event.data &&
            event.data.size > 0
          ) {
            audioChunksRef.current.push(
              event.data
            );
          }
        };

        recorder.onstop = () => {
          const blob =
            new Blob(
              audioChunksRef.current,
              {
                type:
                  recorder.mimeType ||
                  "audio/webm",
              }
            );

          setAudioBlob(blob);

          // Stop microphone
          if (
            mediaStreamRef.current
          ) {
            mediaStreamRef.current
              .getTracks()
              .forEach((track) =>
                track.stop()
              );

            mediaStreamRef.current = null;
          }
        };

        recorder.onerror = (event) => {
          console.error(
            "MediaRecorder error:",
            event
          );

          setError(
            "Audio recording failed."
          );
        };

        recorder.start();

        setIsRecording(true);
      } catch (err) {
        console.error(
          "Microphone error:",
          err
        );

        if (
          err.name ===
          "NotAllowedError"
        ) {
          setPermissionDenied(true);

          setError(
            "Microphone permission was denied."
          );
        } else {
          setError(
            err.message ||
              "Unable to access microphone."
          );
        }

        setIsRecording(false);
      }
    },
    []
  );

  // --------------------------------------------------
  // Stop recording
  // --------------------------------------------------
  const stopRecording = useCallback(
    () => {
      const recorder =
        mediaRecorderRef.current;

      if (
        recorder &&
        recorder.state !== "inactive"
      ) {
        recorder.stop();
      }

      setIsRecording(false);
    },
    []
  );

  // --------------------------------------------------
  // Toggle recording
  // --------------------------------------------------
  const toggleRecording =
    useCallback(() => {
      if (isRecording) {
        stopRecording();
      } else {
        startRecording();
      }
    }, [
      isRecording,
      startRecording,
      stopRecording,
    ]);

  // --------------------------------------------------
  // Convert recorded audio to text
  // --------------------------------------------------
  const transcribe = useCallback(
    async (
      language = "auto",
      token = null
    ) => {
      if (!audioBlob) {
        setError(
          "No audio recording available."
        );

        return null;
      }

      setIsProcessing(true);
      setError(null);

      try {
        const result =
          await voiceService.speechToText(
            audioBlob,
            language,
            token
          );

        const text =
          result?.text ||
          result?.transcript ||
          "";

        setTranscript(text);

        return {
          ...result,
          text,
        };
      } catch (err) {
        console.error(
          "Speech-to-text error:",
          err
        );

        setError(err.message);

        return null;
      } finally {
        setIsProcessing(false);
      }
    },
    [audioBlob]
  );

  // --------------------------------------------------
  // Direct recording + transcription
  // --------------------------------------------------
  const recordAndTranscribe =
    useCallback(
      async (
        language = "auto",
        token = null
      ) => {
        /*
         * Start recording only.
         *
         * After the user stops recording,
         * call transcribe().
         */
        await startRecording();

        return true;
      },
      [startRecording]
    );

  // --------------------------------------------------
  // Text to speech
  // --------------------------------------------------
  const speak = useCallback(
    async (
      text,
      language = "en",
      token = null
    ) => {
      if (!text?.trim()) {
        return null;
      }

      setError(null);

      try {
        const result =
          await voiceService.textToSpeech(
            text,
            language,
            token
          );

        /*
         * Backend may return:
         *
         * 1. audio URL
         * 2. audio data
         * 3. JSON response
         */

        if (result?.audio_url) {
          const audio =
            new Audio(
              result.audio_url
            );

          await audio.play();

          return result;
        }

        return result;
      } catch (err) {
        console.error(
          "Text-to-speech error:",
          err
        );

        setError(err.message);

        return null;
      }
    },
    []
  );

  // --------------------------------------------------
  // Detect language
  // --------------------------------------------------
  const detectLanguage = useCallback(
    async (
      text,
      token = null
    ) => {
      if (!text?.trim()) {
        return null;
      }

      try {
        return await voiceService.detectLanguage(
          text,
          token
        );
      } catch (err) {
        console.error(
          "Language detection error:",
          err
        );

        setError(err.message);

        return null;
      }
    },
    []
  );

  // --------------------------------------------------
  // Translate
  // --------------------------------------------------
  const translate = useCallback(
    async ({
      text,
      sourceLanguage = "auto",
      targetLanguage = "en",
      token = null,
    }) => {
      if (!text?.trim()) {
        return null;
      }

      try {
        return await voiceService.translate({
          text,
          sourceLanguage,
          targetLanguage,
          token,
        });
      } catch (err) {
        console.error(
          "Translation error:",
          err
        );

        setError(err.message);

        return null;
      }
    },
    []
  );

  // --------------------------------------------------
  // Clear voice data
  // --------------------------------------------------
  const clearVoice = useCallback(
    () => {
      setTranscript("");
      setAudioBlob(null);
      setError(null);
      setIsProcessing(false);
    },
    []
  );

  // --------------------------------------------------
  // Cleanup microphone on component unmount
  // --------------------------------------------------
  useEffect(() => {
    return () => {
      if (
        mediaRecorderRef.current &&
        mediaRecorderRef.current.state !==
          "inactive"
      ) {
        mediaRecorderRef.current.stop();
      }

      if (
        mediaStreamRef.current
      ) {
        mediaStreamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          );
      }
    };
  }, []);

  return {
    // Recording
    isRecording,
    startRecording,
    stopRecording,
    toggleRecording,

    // Processing
    isProcessing,

    // Audio
    audioBlob,

    // Speech-to-text
    transcript,
    transcribe,
    recordAndTranscribe,

    // Text-to-speech
    speak,

    // Language
    detectLanguage,
    translate,

    // State
    error,
    permissionDenied,

    // Reset
    clearVoice,
  };
}
