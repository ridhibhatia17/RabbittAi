import { useState, useRef } from "react";
import { analyzeSales } from "./api";

const ALLOWED_TYPES = [
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];
const MAX_SIZE = 5 * 1024 * 1024; // 5 MB

export default function UploadForm() {
  const [file, setFile] = useState(null);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle"); // idle | uploading | processing | success | error
  const [message, setMessage] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  /* ---------- file helpers ---------- */
  function validateFile(f) {
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["csv", "xlsx"].includes(ext)) {
      return "Only .csv and .xlsx files are allowed.";
    }
    if (f.size > MAX_SIZE) {
      return "File exceeds 5 MB limit.";
    }
    return null;
  }

  function handleFileSelect(f) {
    const err = validateFile(f);
    if (err) {
      setMessage(err);
      setStatus("error");
      setFile(null);
      return;
    }
    setFile(f);
    setMessage("");
    setStatus("idle");
  }

  /* ---------- drag & drop ---------- */
  function onDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }
  function onDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }
  function onDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }

  /* ---------- submit ---------- */
  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setMessage("Please select a file.");
      setStatus("error");
      return;
    }
    if (!email) {
      setMessage("Please enter a recipient email.");
      setStatus("error");
      return;
    }

    try {
      setStatus("uploading");
      setMessage("");

      // After upload completes, the backend processes with AI + sends email
      setStatus("processing");
      const data = await analyzeSales(file, email);

      setStatus("success");
      setMessage(data.message || "Sales summary generated and sent!");
    } catch (err) {
      setStatus("error");
      setMessage(err.message);
    }
  }

  /* ---------- render ---------- */
  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      {/* Drop zone */}
      <div
        className={`drop-zone ${dragActive ? "drag-active" : ""} ${file ? "has-file" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          hidden
          onChange={(e) => {
            if (e.target.files[0]) handleFileSelect(e.target.files[0]);
          }}
        />
        {file ? (
          <p className="file-name">
            <span className="icon">📄</span> {file.name}
          </p>
        ) : (
          <>
            <span className="icon upload-icon">⬆️</span>
            <p>Drag &amp; drop a <strong>.csv</strong> or <strong>.xlsx</strong> file here</p>
            <p className="hint">or click to browse (max 5 MB)</p>
          </>
        )}
      </div>

      {/* Email */}
      <label className="email-label" htmlFor="email">
        Recipient Email
      </label>
      <input
        id="email"
        className="email-input"
        type="email"
        placeholder="e.g. manager@company.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      {/* Submit */}
      <button
        className="submit-btn"
        type="submit"
        disabled={status === "uploading" || status === "processing"}
      >
        {status === "uploading"
          ? "Uploading…"
          : status === "processing"
            ? "Analyzing & Sending…"
            : "Analyze & Send Report"}
      </button>

      {/* Progress / messages */}
      {(status === "uploading" || status === "processing") && (
        <div className="progress-bar">
          <div className="progress-fill" />
        </div>
      )}

      {status === "success" && (
        <div className="msg msg-success">✅ {message}</div>
      )}
      {status === "error" && (
        <div className="msg msg-error">❌ {message}</div>
      )}
    </form>
  );
}
