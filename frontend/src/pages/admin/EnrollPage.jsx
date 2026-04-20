import React, { useState, useRef, useEffect } from "react";
import { useParams } from "react-router-dom";
import Webcam from "react-webcam";
import apiClient from "../../services/apiClient";
import { API } from "../../config/api";

export default function EnrollPage() {
  const { companyCode, employeeCode } = useParams();
  const webcamRef = useRef(null);
  const [images, setImages] = useState([]);
  const [captured, setCaptured] = useState([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [employeeInfo, setEmployeeInfo] = useState(null);

  useEffect(() => {
    apiClient.get(API.EMPLOYEE(companyCode, employeeCode))
      .then((r) => setEmployeeInfo(r.data));
    loadImages();
  }, []);

  const loadImages = async () => {
    const res = await apiClient.get(API.FACE_LIST(companyCode), { params: { employee_code: employeeCode } });
    setImages(res.data.images || []);
  };

  const capturePhoto = () => {
    const screenshot = webcamRef.current?.getScreenshot();
    if (screenshot) setCaptured((prev) => [...prev, screenshot]);
  };

  const uploadCaptured = async () => {
    if (captured.length === 0) return;
    setLoading(true);
    setStatus("Uploading...");
    try {
      const formData = new FormData();
      formData.append("employee_code", employeeCode);
      for (let i = 0; i < captured.length; i++) {
        const blob = await fetch(captured[i]).then((r) => r.blob());
        formData.append("images", blob, `capture_${i}.jpg`);
      }
      await apiClient.post(API.FACE_CAPTURE(companyCode), formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setCaptured([]);
      setStatus(`${captured.length} image(s) uploaded.`);
      loadImages();
    } catch (e) {
      setStatus("Upload failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  const approve = async () => {
    setLoading(true);
    try {
      await apiClient.post(API.FACE_APPROVE(companyCode), { employee_code: employeeCode });
      setStatus("Images approved.");
    } catch (e) {
      setStatus(e.response?.data?.detail || "Approval failed.");
    } finally {
      setLoading(false);
    }
  };

  const train = async () => {
    setLoading(true);
    setStatus("Training...");
    try {
      const res = await apiClient.post(API.FACE_TRAIN(companyCode), { employee_code: employeeCode });
      setStatus(`Training complete. ${res.data.embeddings_stored} embeddings stored.`);
    } catch (e) {
      setStatus(e.response?.data?.detail || "Training failed.");
    } finally {
      setLoading(false);
    }
  };

  const deleteAll = async () => {
    if (!window.confirm("Delete all images?")) return;
    await apiClient.post(API.FACE_DELETE_ALL(companyCode), { employee_code: employeeCode });
    setImages([]);
    setStatus("All images deleted.");
  };

  return (
    <div style={styles.page}>
      <h2>Face Enrollment — {employeeCode}</h2>
      {employeeInfo && (
        <p style={{ color: "#555" }}>{employeeInfo.full_name} · {employeeInfo.department}</p>
      )}

      {status && <div style={styles.status}>{status}</div>}

      <div style={styles.grid}>
        {/* Webcam capture */}
        <div style={styles.card}>
          <h3>Capture Photos</h3>
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            width={320}
            height={240}
            style={styles.webcam}
            videoConstraints={{ facingMode: "user" }}
          />
          <div style={styles.row}>
            <button style={styles.btn} onClick={capturePhoto}>📷 Capture</button>
            <button style={{ ...styles.btn, background: "#388e3c" }} onClick={uploadCaptured} disabled={captured.length === 0 || loading}>
              Upload ({captured.length})
            </button>
          </div>
          {captured.length > 0 && (
            <div style={styles.thumbnails}>
              {captured.map((img, i) => (
                <img key={i} src={img} alt="" style={styles.thumb} />
              ))}
            </div>
          )}
        </div>

        {/* Enrolled images */}
        <div style={styles.card}>
          <h3>Enrolled Images ({images.length})</h3>
          {images.length === 0 ? (
            <p style={{ color: "#aaa" }}>No images yet.</p>
          ) : (
            <div style={styles.thumbnails}>
              {images.map((img) => (
                <img key={img.image_id} src={img.url} alt="" style={styles.thumb} />
              ))}
            </div>
          )}
          {images.length > 0 && (
            <div style={styles.row}>
              <button style={{ ...styles.btn, background: "#f57c00" }} onClick={approve} disabled={loading}>
                ✓ Approve
              </button>
              <button style={{ ...styles.btn, background: "#7b1fa2" }} onClick={train} disabled={loading}>
                🧠 Train
              </button>
              <button style={{ ...styles.btn, background: "#d32f2f" }} onClick={deleteAll} disabled={loading}>
                🗑 Delete All
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: { padding: "2rem" },
  status: { background: "#e3f2fd", color: "#1565c0", padding: "0.75rem", borderRadius: "4px", marginBottom: "1rem" },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" },
  card: { background: "#fff", border: "1px solid #eee", borderRadius: "8px", padding: "1.5rem", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" },
  webcam: { borderRadius: "8px", display: "block", marginBottom: "1rem" },
  row: { display: "flex", gap: "0.75rem", marginTop: "1rem", flexWrap: "wrap" },
  btn: { padding: "0.5rem 1rem", background: "#1976d2", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600 },
  thumbnails: { display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.75rem" },
  thumb: { width: "80px", height: "80px", objectFit: "cover", borderRadius: "4px", border: "1px solid #ddd" },
};
