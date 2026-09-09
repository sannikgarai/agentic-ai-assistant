
import React, { useRef, useState } from "react";

function FileUpload({
  onFileSelect,
  multiple = false,
  accept = ".pdf,.png,.jpg,.jpeg,.webp",
}) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const processFiles = (files) => {
    if (!files || files.length === 0) return;

    const selectedFiles = Array.from(files);

    if (multiple) {
      onFileSelect?.(selectedFiles);
    } else {
      onFileSelect?.(selectedFiles[0]);
    }
  };

  const handleInputChange = (e) => {
    processFiles(e.target.files);

    // Allow selecting the same file again.
    e.target.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    setDragging(false);

    processFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();

    setDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();

    setDragging(false);
  };

  const openFilePicker = () => {
    if (!inputRef.current) return;

    inputRef.current.click();
  };

  return (
    <div
      className={`file-upload ${dragging ? "dragging" : ""}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={openFilePicker}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          openFilePicker();
        }
      }}
      aria-label="Upload document"
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleInputChange}
        onClick={(e) => e.stopPropagation()}
        hidden
      />

      <div className="upload-icon">
        <img
          src="/assets/icons/upload.svg"
          alt=""
          className="upload-icon-image"
        />
      </div>

      <h3>Upload Document</h3>

      <p>
        Drag &amp; drop your file here
        <br />
        or click to browse
      </p>

      <span className="upload-format">
        PDF, PNG, JPG, JPEG, WEBP
      </span>
    </div>
  );
}

export default FileUpload;

