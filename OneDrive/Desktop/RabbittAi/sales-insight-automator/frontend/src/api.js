const API_BASE =
  import.meta.env.VITE_API_URL ||
  (window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "https://sales-insight-backend-k3gq.onrender.com");

/**
 * Upload a sales file and recipient email to the backend.
 * Returns the JSON response from the API.
 */
export async function analyzeSales(file, recipientEmail, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("recipient_email", recipientEmail);

  if (onProgress) onProgress("uploading");

  const res = await fetch(`${API_BASE}/analyze-sales`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Something went wrong");
  }

  return data;
}
