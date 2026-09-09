import api from "./api";

const buildChatFormData = ({
  message = "",
  conversationId = null,
  language = "en",
  file = null,
}) => {
  const formData = new FormData();

  formData.append(
    "message",
    message || ""
  );

  if (conversationId) {
    formData.append(
      "conversation_id",
      conversationId
    );
  }

  formData.append(
    "language",
    language || "en"
  );

  if (file) {
    formData.append(
      "file",
      file,
      file.name
    );
  }

  return formData;
};

const chatService = {
  // ------------------------------------------------------
  // Send a normal text message
  // ------------------------------------------------------

  async sendMessage({
    message = "",
    conversationId = null,
    language = "en",
    token = null,
  }) {
    const formData = buildChatFormData({
      message,
      conversationId,
      language,
      file: null,
    });

    return api.upload(
      "/api/chat/",
      formData,
      {
        token,
      }
    );
  },

  // ------------------------------------------------------
  // Get all conversations
  // ------------------------------------------------------

  async getConversations(token = null) {
    return api.get(
      "/api/history/",
      {
        token,
      }
    );
  },

  // ------------------------------------------------------
  // Get one conversation and its messages
  // ------------------------------------------------------

  async getMessages(
    conversationId,
    token = null
  ) {
    return api.get(
      `/api/history/${conversationId}`,
      {
        token,
      }
    );
  },

  // ------------------------------------------------------
  // Delete conversation
  // ------------------------------------------------------

  async deleteConversation(
    conversationId,
    token = null
  ) {
    return api.delete(
      `/api/history/${conversationId}`,
      {
        token,
      }
    );
  },

  // ------------------------------------------------------
  // Send text and/or image
  // ------------------------------------------------------

  async sendWithContext({
    message = "",
    conversationId = null,
    language = "en",
    documentIds = [],
    file = null,
    token = null,
  }) {
    const formData = buildChatFormData({
      message,
      conversationId,
      language,
      file,
    });

    return api.upload(
      "/api/chat/",
      formData,
      {
        token,
      }
    );
  },
};

export default chatService;