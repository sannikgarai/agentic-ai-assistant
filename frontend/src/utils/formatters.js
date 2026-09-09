
// ============================================================
// formatters.js
// Utility functions used throughout the frontend
// ============================================================


// ------------------------------------------------------------
// Format date
// Example:
// formatDate("2026-09-01T10:30:00")
// → "01 Sep 2026"
// ------------------------------------------------------------
export function formatDate(date) {
  if (!date) return "";

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "";
  }

  return parsedDate.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}


// ------------------------------------------------------------
// Format date + time
// Example:
// → "01 Sep 2026, 10:30 AM"
// ------------------------------------------------------------
export function formatDateTime(date) {
  if (!date) return "";

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "";
  }

  return parsedDate.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}


// ------------------------------------------------------------
// Format time only
// Example:
// → "10:30 AM"
// ------------------------------------------------------------
export function formatTime(date) {
  if (!date) return "";

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "";
  }

  return parsedDate.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}


// ------------------------------------------------------------
// Format relative time
//
// Examples:
// Just now
// 5 minutes ago
// 2 hours ago
// 3 days ago
// ------------------------------------------------------------
export function formatRelativeTime(date) {
  if (!date) return "";

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "";
  }

  const now = Date.now();
  const difference =
    now - parsedDate.getTime();

  const seconds = Math.floor(
    difference / 1000
  );

  const minutes = Math.floor(
    seconds / 60
  );

  const hours = Math.floor(
    minutes / 60
  );

  const days = Math.floor(
    hours / 24
  );

  if (seconds < 10) {
    return "Just now";
  }

  if (seconds < 60) {
    return `${seconds} seconds ago`;
  }

  if (minutes < 60) {
    return `${minutes} ${
      minutes === 1 ? "minute" : "minutes"
    } ago`;
  }

  if (hours < 24) {
    return `${hours} ${
      hours === 1 ? "hour" : "hours"
    } ago`;
  }

  if (days < 7) {
    return `${days} ${
      days === 1 ? "day" : "days"
    } ago`;
  }

  return formatDate(date);
}


// ------------------------------------------------------------
// Format file size
//
// Example:
// 1024 → 1 KB
// 1048576 → 1 MB
// ------------------------------------------------------------
export function formatFileSize(bytes) {
  if (
    bytes === null ||
    bytes === undefined ||
    Number.isNaN(Number(bytes))
  ) {
    return "0 Bytes";
  }

  const size = Number(bytes);

  if (size === 0) {
    return "0 Bytes";
  }

  const units = [
    "Bytes",
    "KB",
    "MB",
    "GB",
    "TB",
  ];

  const index = Math.floor(
    Math.log(size) / Math.log(1024)
  );

  const safeIndex = Math.min(
    index,
    units.length - 1
  );

  const value =
    size / Math.pow(1024, safeIndex);

  return `${value.toFixed(
    safeIndex === 0 ? 0 : 2
  )} ${units[safeIndex]}`;
}


// ------------------------------------------------------------
// Format duration
//
// Input: seconds
// Example:
// 65 → "01:05"
// 3665 → "01:01:05"
// ------------------------------------------------------------
export function formatDuration(seconds) {
  if (
    seconds === null ||
    seconds === undefined ||
    Number.isNaN(Number(seconds))
  ) {
    return "00:00";
  }

  const totalSeconds = Math.max(
    0,
    Math.floor(Number(seconds))
  );

  const hours = Math.floor(
    totalSeconds / 3600
  );

  const minutes = Math.floor(
    (totalSeconds % 3600) / 60
  );

  const remainingSeconds =
    totalSeconds % 60;

  const mm = String(minutes).padStart(
    2,
    "0"
  );

  const ss = String(
    remainingSeconds
  ).padStart(2, "0");

  if (hours > 0) {
    const hh = String(hours).padStart(
      2,
      "0"
    );

    return `${hh}:${mm}:${ss}`;
  }

  return `${mm}:${ss}`;
}


// ------------------------------------------------------------
// Truncate long text
//
// Example:
// truncateText("Hello World", 5)
// → "Hello..."
// ------------------------------------------------------------
export function truncateText(
  text,
  maxLength = 100
) {
  if (text === null || text === undefined) {
    return "";
  }

  const value = String(text);

  if (value.length <= maxLength) {
    return value;
  }

  return `${value.substring(
    0,
    maxLength
  )}...`;
}


// ------------------------------------------------------------
// Capitalize first letter
//
// Example:
// "pending" → "Pending"
// ------------------------------------------------------------
export function capitalize(text) {
  if (!text) return "";

  const value = String(text);

  return (
    value.charAt(0).toUpperCase() +
    value.slice(1)
  );
}


// ------------------------------------------------------------
// Convert snake_case / kebab-case to readable text
//
// Example:
// "in_progress" → "In Progress"
// "document-upload" → "Document Upload"
// ------------------------------------------------------------
export function formatLabel(text) {
  if (!text) return "";

  return String(text)
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );
}


// ------------------------------------------------------------
// Format application status
// ------------------------------------------------------------
export function formatApplicationStatus(
  status
) {
  if (!status) return "Unknown";

  const statusMap = {
    pending: "Pending",
    processing: "Processing",
    in_progress: "In Progress",
    submitted: "Submitted",
    approved: "Approved",
    rejected: "Rejected",
    completed: "Completed",
    failed: "Failed",
    cancelled: "Cancelled",
  };

  const normalized =
    String(status).toLowerCase();

  return (
    statusMap[normalized] ||
    formatLabel(normalized)
  );
}


// ------------------------------------------------------------
// Format task status
// ------------------------------------------------------------
export function formatTaskStatus(status) {
  if (!status) return "Unknown";

  const statusMap = {
    pending: "Pending",
    running: "Running",
    in_progress: "In Progress",
    completed: "Completed",
    failed: "Failed",
    skipped: "Skipped",
  };

  const normalized =
    String(status).toLowerCase();

  return (
    statusMap[normalized] ||
    formatLabel(normalized)
  );
}


// ------------------------------------------------------------
// Format verification result
// ------------------------------------------------------------
export function formatVerificationStatus(
  status
) {
  if (!status) return "Unknown";

  const statusMap = {
    verified: "Verified",
    passed: "Verified",
    valid: "Valid",
    mismatch: "Mismatch Found",
    mismatched: "Mismatch Found",
    failed: "Verification Failed",
    pending: "Pending Verification",
    not_verified: "Not Verified",
  };

  const normalized =
    String(status).toLowerCase();

  return (
    statusMap[normalized] ||
    formatLabel(normalized)
  );
}


// ------------------------------------------------------------
// Get status type
//
// Useful for CSS classes
//
// Returns:
// success
// warning
// error
// info
// neutral
// ------------------------------------------------------------
export function getStatusType(status) {
  if (!status) return "neutral";

  const normalized =
    String(status).toLowerCase();

  const successStatuses = [
    "approved",
    "completed",
    "success",
    "successful",
    "verified",
    "passed",
    "valid",
    "submitted",
  ];

  const warningStatuses = [
    "pending",
    "processing",
    "running",
    "in_progress",
  ];

  const errorStatuses = [
    "failed",
    "rejected",
    "cancelled",
    "mismatch",
    "mismatched",
    "error",
  ];

  if (
    successStatuses.includes(normalized)
  ) {
    return "success";
  }

  if (
    warningStatuses.includes(normalized)
  ) {
    return "warning";
  }

  if (
    errorStatuses.includes(normalized)
  ) {
    return "error";
  }

  return "info";
}


// ------------------------------------------------------------
// Format language name
// ------------------------------------------------------------
export function formatLanguage(
  language
) {
  if (!language) return "Unknown";

  const languages = {
    en: "English",
    bn: "বাংলা",
    hi: "हिन्दी",
    or: "ଓଡ଼ିଆ",
    ori: "ଓଡ଼ିଆ",
    as: "অসমীয়া",
    asm: "অসমীয়া",
    ta: "தமிழ்",
    te: "తెలుగు",
    mr: "मराठी",
    gu: "ગુજરાતી",
    pa: "ਪੰਜਾਬੀ",
    ml: "മലയാളം",
    kn: "ಕನ್ನಡ",
    ur: "اردو",
  };

  const normalized =
    String(language).toLowerCase();

  return (
    languages[normalized] ||
    language
  );
}


// ------------------------------------------------------------
// Format message role
// ------------------------------------------------------------
export function formatMessageRole(role) {
  if (!role) return "Unknown";

  const roles = {
    user: "You",
    assistant: "AI Assistant",
    system: "System",
    tool: "Tool",
  };

  return (
    roles[String(role).toLowerCase()] ||
    capitalize(role)
  );
}


// ------------------------------------------------------------
// Clean message text
//
// Removes unnecessary whitespace.
// ------------------------------------------------------------
export function cleanText(text) {
  if (
    text === null ||
    text === undefined
  ) {
    return "";
  }

  return String(text)
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}


// ------------------------------------------------------------
// Format percentage
//
// Example:
// 0.95 → "95%"
// 95 → "95%"
// ------------------------------------------------------------
export function formatPercentage(
  value,
  decimals = 0
) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "0%";
  }

  let number = Number(value);

  // If value is between 0 and 1,
  // treat it as a decimal percentage.
  if (number >= 0 && number <= 1) {
    number *= 100;
  }

  return `${number.toFixed(decimals)}%`;
}


// ------------------------------------------------------------
// Format currency
//
// Default: Indian Rupee
// Example:
// 50000 → ₹50,000
// ------------------------------------------------------------
export function formatCurrency(
  amount,
  currency = "INR"
) {
  if (
    amount === null ||
    amount === undefined ||
    Number.isNaN(Number(amount))
  ) {
    return "₹0";
  }

  return new Intl.NumberFormat(
    "en-IN",
    {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }
  ).format(Number(amount));
}


// ------------------------------------------------------------
// Get file extension
//
// Example:
// "document.pdf" → "pdf"
// ------------------------------------------------------------
export function getFileExtension(
  filename
) {
  if (!filename) return "";

  const value = String(filename);

  const parts = value.split(".");

  if (parts.length < 2) {
    return "";
  }

  return parts[
    parts.length - 1
  ].toLowerCase();
}


// ------------------------------------------------------------
// Get file name without extension
//
// Example:
// "document.pdf" → "document"
// ------------------------------------------------------------
export function getFileName(
  filename
) {
  if (!filename) return "";

  const value = String(filename);

  const lastSlash = Math.max(
    value.lastIndexOf("/"),
    value.lastIndexOf("\\")
  );

  const name =
    lastSlash >= 0
      ? value.substring(lastSlash + 1)
      : value;

  const extensionIndex =
    name.lastIndexOf(".");

  if (
    extensionIndex > 0
  ) {
    return name.substring(
      0,
      extensionIndex
    );
  }

  return name;
}


// ------------------------------------------------------------
// Get initials
//
// Example:
// "Sannik Garai" → "SG"
// ------------------------------------------------------------
export function getInitials(
  name,
  maxInitials = 2
) {
  if (!name) return "";

  const words = String(name)
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  return words
    .slice(0, maxInitials)
    .map((word) =>
      word.charAt(0).toUpperCase()
    )
    .join("");
}


// ------------------------------------------------------------
// Format API error
// ------------------------------------------------------------
export function formatError(error) {
  if (!error) {
    return "Something went wrong.";
  }

  if (typeof error === "string") {
    return error;
  }

  if (error.message) {
    return error.message;
  }

  if (error.detail) {
    return Array.isArray(error.detail)
      ? error.detail
          .map((item) =>
            item.msg || String(item)
          )
          .join(", ")
      : String(error.detail);
  }

  return "Something went wrong.";
}


// ------------------------------------------------------------
// Format source citation
//
// Used by RAG source citation component.
// ------------------------------------------------------------
export function formatCitation(source) {
  if (!source) {
    return {
      title: "Unknown Source",
      page: null,
      document: null,
    };
  }

  return {
    title:
      source.title ||
      source.name ||
      source.filename ||
      "Government Document",

    page:
      source.page ||
      source.page_number ||
      null,

    document:
      source.document ||
      source.filename ||
      source.source ||
      null,
  };
}


// ------------------------------------------------------------
// Default export
// ------------------------------------------------------------
const formatters = {
  formatDate,
  formatDateTime,
  formatTime,
  formatRelativeTime,

  formatFileSize,
  formatDuration,

  truncateText,
  capitalize,
  formatLabel,

  formatApplicationStatus,
  formatTaskStatus,
  formatVerificationStatus,
  getStatusType,

  formatLanguage,
  formatMessageRole,

  cleanText,
  formatPercentage,
  formatCurrency,

  getFileExtension,
  getFileName,
  getInitials,

  formatError,
  formatCitation,
};

export default formatters;
