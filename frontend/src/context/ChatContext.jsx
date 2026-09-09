
import React, {
  createContext,
  useContext,
  useState,
} from "react";

import chatService from "../services/chatService";
import { useAuth } from "./AuthContext";
import supabase from "../lib/supabase";

const ChatContext = createContext(null);

// ==================================================
// Supabase Storage configuration
// ==================================================

const STORAGE_BUCKET = "documents";

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
];

// ==================================================
// Upload file to Supabase Storage
// ==================================================

const uploadFileToSupabase = async (
  file,
  userId
) => {
  if (!file) {
    return null;
  }

  if (!userId) {
    throw new Error(
      "User authentication is required to upload files."
    );
  }

  // --------------------------------------------------
  // Validate file type
  // --------------------------------------------------

  if (
    !ALLOWED_FILE_TYPES.includes(
      file.type
    )
  ) {
    throw new Error(
      "Only PDF, PNG, JPG, JPEG, and WEBP files are allowed."
    );
  }

  // --------------------------------------------------
  // Validate file size
  // --------------------------------------------------

  if (file.size > MAX_FILE_SIZE) {
    throw new Error(
      "File size must be 10 MB or less."
    );
  }

  // --------------------------------------------------
  // Create safe file name
  // --------------------------------------------------

  const safeFileName =
    file.name.replace(
      /[^a-zA-Z0-9._-]/g,
      "_"
    );

  // --------------------------------------------------
  // Create unique storage path
  // --------------------------------------------------

  const filePath =
    `${userId}/${Date.now()}-${safeFileName}`;

  // --------------------------------------------------
  // Upload to Supabase Storage
  // --------------------------------------------------

  const {
    error,
  } = await supabase.storage
    .from(STORAGE_BUCKET)
    .upload(
      filePath,
      file,
      {
        cacheControl: "3600",
        upsert: false,
        contentType:
          file.type ||
          "application/octet-stream",
      }
    );

  if (error) {
    console.error(
      "Supabase Storage upload error:",
      error
    );

    throw new Error(
      error.message ||
        "Failed to upload file to Supabase Storage."
    );
  }

  return {
    bucket: STORAGE_BUCKET,
    path: filePath,
    file_name: file.name,
    file_type: file.type,
    file_size: file.size,
  };
};

// ==================================================
// Chat Provider
// ==================================================

export function ChatProvider({
  children,
}) {
  const { session, user } =
    useAuth();

  const [messages, setMessages] =
    useState([]);

  const [
    conversations,
    setConversations,
  ] = useState([]);

  const [
    currentConversationId,
    setCurrentConversationId,
  ] = useState(null);

  const [language, setLanguage] =
    useState("en");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);

  // --------------------------------------------------
  // Get Supabase access token
  // --------------------------------------------------

  const getToken = () => {
    const token =
      session?.access_token || null;

    console.log(
      "Token exists:",
      Boolean(token)
    );

    return token;
  };

  // --------------------------------------------------
  // Load conversation history
  // --------------------------------------------------

  const loadConversations =
    async () => {
      if (!user) {
        return [];
      }

      setError(null);

      try {
        const data =
          await chatService.getConversations(
            getToken()
          );

        const list = Array.isArray(data)
          ? data
          : data?.conversations || [];

        setConversations(list);

        return list;
      } catch (err) {
        console.error(
          "Load conversations error:",
          err
        );

        setError(err.message);

        return [];
      }
    };

  // --------------------------------------------------
  // Open existing conversation
  // --------------------------------------------------

  const openConversation =
    async (conversationId) => {
      if (!conversationId) {
        return [];
      }

      setLoading(true);
      setError(null);

      try {
        const data =
          await chatService.getMessages(
            conversationId,
            getToken()
          );

        const list = Array.isArray(data)
          ? data
          : data?.messages || [];

        setCurrentConversationId(
          conversationId
        );

        setMessages(list);

        return list;
      } catch (err) {
        console.error(
          "Open conversation error:",
          err
        );

        setError(err.message);

        return [];
      } finally {
        setLoading(false);
      }
    };

  // --------------------------------------------------
  // Send text / image / PDF
  // --------------------------------------------------

  const sendMessage = async (
    text,
    options = {}
  ) => {
    const cleanText =
      text?.trim() || "";

    const file =
      options.file || null;

    // Nothing to send
    if (!cleanText && !file) {
      return null;
    }

    setLoading(true);
    setError(null);

    console.log(
      "========== CHAT SEND =========="
    );

    console.log(
      "Message:",
      cleanText
    );

    console.log(
      "File:",
      file
    );

    console.log(
      "Conversation ID:",
      currentConversationId
    );

    console.log(
      "Language:",
      language
    );

    console.log(
      "User exists:",
      Boolean(user)
    );

    console.log(
      "Session exists:",
      Boolean(session)
    );

    console.log(
      "Token exists:",
      Boolean(session?.access_token)
    );

    console.log(
      "==============================="
    );

    // --------------------------------------------------
    // Create immediate user message
    // --------------------------------------------------

    const temporaryUserMessage = {
      id: `temp-user-${Date.now()}`,
      role: "user",
      content: cleanText,
      language,
      created_at:
        new Date().toISOString(),
    };

    // --------------------------------------------------
    // File information and preview
    // --------------------------------------------------

    if (file) {
      temporaryUserMessage.file_name =
        file.name;

      temporaryUserMessage.file_type =
        file.type;

      temporaryUserMessage.file_size =
        file.size;

      // ------------------------------------------------
      // PNG / JPG / JPEG / WEBP preview
      // ------------------------------------------------

      if (
        [
          "image/png",
          "image/jpeg",
          "image/webp",
        ].includes(file.type)
      ) {
        temporaryUserMessage.image_url =
          URL.createObjectURL(file);
      }

      // ------------------------------------------------
      // PDF preview/open URL
      // ------------------------------------------------

      if (
        file.type ===
        "application/pdf"
      ) {
        temporaryUserMessage.file_url =
          URL.createObjectURL(file);
      }
    }

    setMessages((prev) => [
      ...prev,
      temporaryUserMessage,
    ]);

    try {
      // --------------------------------------------------
      // Upload file to Supabase Storage
      // --------------------------------------------------

      let storageFile = null;

      if (file) {
        storageFile =
          await uploadFileToSupabase(
            file,
            user?.id
          );

        console.log(
          "File uploaded to Supabase Storage:",
          storageFile
        );
      }

      // --------------------------------------------------
      // Send message to backend
      // --------------------------------------------------

      console.log(
        "Calling chatService.sendWithContext..."
      );

      const response =
        await chatService.sendWithContext({
          message: cleanText,
          conversationId:
            currentConversationId,
          language,
          documentIds:
            options.documentIds || [],
          file,
          token: getToken(),
        });

      console.log(
        "Chat API response:",
        response
      );

      const assistantContent =
        typeof response?.message ===
        "string"
          ? response.message
          : response?.message
              ?.content ||
            response?.answer ||
            response?.response ||
            "No response received.";

      // --------------------------------------------------
      // Update conversation ID
      // --------------------------------------------------

      if (
        response?.conversation_id
      ) {
        setCurrentConversationId(
          response.conversation_id
        );
      }

      // --------------------------------------------------
      // Create assistant message
      // --------------------------------------------------

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: assistantContent,
        language:
          response?.language ||
          language,
        sources:
          response?.sources || [],
        tasks:
          response?.tasks || [],
        verification:
          response?.verification ||
          null,
        metadata: {
          ...(response?.metadata || {}),
          ...(storageFile
            ? {
                storage: storageFile,
              }
            : {}),
        },
        created_at:
          new Date().toISOString(),
      };

      setMessages((prev) => [
        ...prev,
        assistantMessage,
      ]);

      return response;
    } catch (err) {
      console.error(
        "========== CHAT ERROR =========="
      );

      console.error(err);

      console.error(
        "================================"
      );

      setError(err.message);

      const errorMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content:
          err.message ||
          "Sorry, something went wrong while processing your request.",
        error: true,
        created_at:
          new Date().toISOString(),
      };

      setMessages((prev) => [
        ...prev,
        errorMessage,
      ]);

      return null;
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // Change language
  // --------------------------------------------------

  const changeLanguage =
    (newLanguage) => {
      setLanguage(newLanguage);
    };

  // --------------------------------------------------
  // Clear current chat
  // --------------------------------------------------

  const clearChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setError(null);
  };

  // --------------------------------------------------
  // Delete conversation
  // --------------------------------------------------

  const deleteConversation =
    async (conversationId) => {
      if (!conversationId) {
        return false;
      }

      setError(null);

      try {
        await chatService.deleteConversation(
          conversationId,
          getToken()
        );

        setConversations((prev) =>
          prev.filter(
            (item) =>
              item.id !== conversationId
          )
        );

        if (
          currentConversationId ===
          conversationId
        ) {
          setCurrentConversationId(
            null
          );

          setMessages([]);
        }

        return true;
      } catch (err) {
        console.error(
          "Delete conversation error:",
          err
        );

        setError(err.message);

        return false;
      }
    };

  // --------------------------------------------------
  // Context value
  // --------------------------------------------------

  const value = {
    messages,
    conversations,
    currentConversationId,
    language,
    loading,
    error,

    sendMessage,
    loadConversations,
    openConversation,
    changeLanguage,
    clearChat,
    deleteConversation,
  };

  return (
    <ChatContext.Provider
      value={value}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context =
    useContext(ChatContext);

  if (!context) {
    throw new Error(
      "useChat must be used inside ChatProvider"
    );
  }

  return context;
}

export default ChatContext;
