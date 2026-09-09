
import api from "./api";

const voiceService = {
  /**
   * Send audio to backend for speech-to-text
   */
  async speechToText(
    audioBlob,
    language = "auto",
    token = null
  ) {
    const formData = new FormData();

    formData.append(
      "audio",
      audioBlob,
      "recording.webm"
    );

    formData.append(
      "language",
      language
    );

    return api.upload(
      "/api/voice/transcribe",
      formData,
      {
        token,
      }
    );
  },

  /**
   * Convert text to speech
   */
  async textToSpeech(
    text,
    language = "en",
    token = null
  ) {
    return api.post(
      "/api/voice/speak",
      {
        text,
        language,
      },
      {
        token,
      }
    );
  },

  /**
   * Detect language
   */
  async detectLanguage(
    text,
    token = null
  ) {
    return api.post(
      "/api/voice/detect-language",
      {
        text,
      },
      {
        token,
      }
    );
  },

  /**
   * Translate text
   */
  async translate({
    text,
    sourceLanguage = "auto",
    targetLanguage = "en",
    token = null,
  }) {
    return api.post(
      "/api/voice/translate",
      {
        text,
        source_language: sourceLanguage,
        target_language: targetLanguage,
      },
      {
        token,
      }
    );
  },
};

export default voiceService;

