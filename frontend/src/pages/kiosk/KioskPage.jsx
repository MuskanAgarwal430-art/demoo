import React, { useState, useRef, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import Webcam from "react-webcam";
import axios from "axios";
import { API } from "../../config/api";

const STATUS_CONFIG = {
  check_in:       { color: "#2e7d32", bg: "#e8f5e9", icon: "✅", message: "Checked In" },
  check_out:      { color: "#1565c0", bg: "#e3f2fd", icon: "👋", message: "Checked Out" },
  already_marked: { color: "#f57c00", bg: "#fff3e0", icon: "⚠️", message: "Already Marked" },
  not_recognized: { color: "#d32f2f", bg: "#ffebee", icon: "❓", message: "Not Recognized" },
  spoof_detected: { color: "#d32f2f", bg: "#ffebee", icon: "🚫", message: "Spoof Detected" },
  poor_quality:   { color: "#f57c00", bg: "#fff3e0", icon: "📷", message: "Poor Image Quality" },
  no_face_detected: { color: "#d32f2f", bg: "#ffebee", icon: "👤", message: "No Face Detected" },
  scanning:       { color: "#1565c0", bg: "#e3f2fd", icon: "🔍", message: "Scanning..." },
  idle:           { color: "#555",    bg: "transparent", icon: "", message: "" },
};

const RESULT_DISPLAY_DURATION = 4000;  // ms to show result before resetting
const AUTO_SCAN_INTERVAL = 2500;       // ms between auto-scan attempts

export default function KioskPage() {
  const { companyCode } = useParams();
  const webcamRef = useRef(null);

  const [kioskConfig, setKioskConfig] = useState(null);
  const [scanStatus, setScanStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [autoScan, setAutoScan] = useState(false);
  const resetTimer = useRef(null);
  const scanTimer = useRef(null);

  // Load kiosk config on mount
  useEffect(() => {
    axios.get(API.KIOSK_CONFIG(companyCode))
      .then((r) => setKioskConfig(r.data))
      .catch(() => {});
  }, [companyCode]);

  const resetToIdle = useCallback(() => {
    setScanStatus("idle");
    setResult(null);
    setIsProcessing(false);
  }, []);

  const scan = useCallback(async () => {
    if (isProcessing || !webcamRef.current) return;

    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) return;

    setIsProcessing(true);
    setScanStatus("scanning");
    setResult(null);
    clearTimeout(resetTimer.current);

    try {
      const res = await axios.post(API.KIOSK_RECOGNIZE(companyCode), {
        face_image: screenshot,
      });
      const data = res.data;
      setScanStatus(data.status || "idle");
      setResult(data);
    } catch (err) {
      const errStatus = err.response?.data?.status || "not_recognized";
      setScanStatus(errStatus);
      setResult(err.response?.data || { status: errStatus, detail: "Recognition failed." });
    } finally {
      setIsProcessing(false);
      resetTimer.current = setTimeout(resetToIdle, RESULT_DISPLAY_DURATION);
    }
  }, [companyCode, isProcessing, resetToIdle]);

  // Auto-scan loop
  useEffect(() => {
    if (autoScan) {
      scanTimer.current = setInterval(() => {
        if (!isProcessing) scan();
      }, AUTO_SCAN_INTERVAL);
    } else {
      clearInterval(scanTimer.current);
    }
    return () => clearInterval(scanTimer.current);
  }, [autoScan, isProcessing, scan]);

  // Cleanup on unmount
  useEffect(() => () => {
    clearTimeout(resetTimer.current);
    clearInterval(scanTimer.current);
  }, []);

  const cfg = STATUS_CONFIG[scanStatus] || STATUS_CONFIG.idle;

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.logo}>Face Attendance</h1>
          {kioskConfig && (
            <span style={styles.companyName}>{kioskConfig.company_name}</span>
          )}
        </div>
        <div style={styles.clock}>
          <Clock />
        </div>
      </div>

      {/* Main content */}
      <div style={styles.main}>
        {/* Camera box */}
        <div style={{ ...styles.cameraBox, borderColor: cfg.color !== "#555" ? cfg.color : "#333" }}>
          <Webcam
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            width={480}
            height={360}
            style={styles.webcam}
            videoConstraints={{ facingMode: "user", width: 640, height: 480 }}
            screenshotQuality={0.92}
          />

          {/* Scanning overlay */}
          {scanStatus === "scanning" && (
            <div style={styles.scanOverlay}>
              <div style={styles.scanLine} />
            </div>
          )}
        </div>

        {/* Result panel */}
        <div style={{ ...styles.resultPanel, background: cfg.bg, borderColor: cfg.color }}>
          {scanStatus === "idle" ? (
            <div style={styles.idleText}>
              <div style={styles.idleIcon}>👁️</div>
              <p>Look at the camera to mark attendance</p>
              <p style={styles.idleHint}>Press <b>Scan</b> or enable <b>Auto Scan</b></p>
              {kioskConfig && (
                <div style={styles.timingInfo}>
                  <span>Check-in: {kioskConfig.check_in_start} – {kioskConfig.check_in_end}</span>
                </div>
              )}
            </div>
          ) : (
            <div style={styles.resultContent}>
              <div style={styles.resultIcon}>{cfg.icon}</div>
              <div style={{ ...styles.resultStatus, color: cfg.color }}>{cfg.message}</div>

              {result?.employee && (
                <div style={styles.employeeInfo}>
                  <div style={styles.employeeName}>{result.employee.name}</div>
                  {result.employee.department && (
                    <div style={styles.employeeDept}>{result.employee.department}</div>
                  )}
                  {result.time && (
                    <div style={styles.resultTime}>
                      {new Date(result.time).toLocaleTimeString()}
                    </div>
                  )}
                  {result.confidence && (
                    <div style={styles.confidence}>
                      Confidence: {(result.confidence * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              )}

              {result?.detail && !result?.employee && (
                <p style={{ color: cfg.color, fontSize: "0.9rem", marginTop: "0.5rem" }}>
                  {result.detail}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div style={styles.controls}>
        <button
          style={{ ...styles.scanBtn, opacity: isProcessing ? 0.6 : 1 }}
          onClick={scan}
          disabled={isProcessing}
        >
          {isProcessing ? "Scanning..." : "📷 Scan Face"}
        </button>

        <button
          style={{ ...styles.autoBtn, background: autoScan ? "#d32f2f" : "#388e3c" }}
          onClick={() => setAutoScan((v) => !v)}
        >
          {autoScan ? "⏹ Stop Auto Scan" : "▶ Auto Scan"}
        </button>
      </div>
    </div>
  );
}

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <div>
      <div style={{ fontSize: "1.8rem", fontWeight: 700, letterSpacing: "2px" }}>
        {time.toLocaleTimeString()}
      </div>
      <div style={{ fontSize: "0.9rem", color: "#aaa", textAlign: "right" }}>
        {time.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#0d1117",
    color: "#fff",
    display: "flex",
    flexDirection: "column",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "1rem 2rem",
    borderBottom: "1px solid #21262d",
    background: "#161b22",
  },
  headerLeft: { display: "flex", alignItems: "center", gap: "1rem" },
  logo: { fontSize: "1.3rem", fontWeight: 700, color: "#58a6ff" },
  companyName: { fontSize: "0.95rem", color: "#8b949e", background: "#21262d", padding: "0.25rem 0.75rem", borderRadius: "12px" },
  clock: { textAlign: "right" },
  main: {
    flex: 1,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: "2rem",
    padding: "2rem",
    flexWrap: "wrap",
  },
  cameraBox: {
    position: "relative",
    borderRadius: "12px",
    border: "3px solid",
    overflow: "hidden",
    boxShadow: "0 0 40px rgba(88, 166, 255, 0.15)",
    transition: "border-color 0.3s",
  },
  webcam: { display: "block" },
  scanOverlay: {
    position: "absolute",
    top: 0, left: 0, right: 0, bottom: 0,
    background: "rgba(88, 166, 255, 0.05)",
    display: "flex",
    alignItems: "center",
  },
  scanLine: {
    width: "100%",
    height: "2px",
    background: "linear-gradient(to right, transparent, #58a6ff, transparent)",
    animation: "scan 1.5s ease-in-out infinite",
  },
  resultPanel: {
    width: "320px",
    minHeight: "360px",
    borderRadius: "12px",
    border: "2px solid",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "2rem",
    transition: "all 0.3s",
  },
  idleText: { textAlign: "center", color: "#8b949e" },
  idleIcon: { fontSize: "3rem", marginBottom: "1rem" },
  idleHint: { fontSize: "0.85rem", marginTop: "0.5rem", color: "#6e7681" },
  timingInfo: { marginTop: "1rem", fontSize: "0.8rem", background: "#21262d", padding: "0.5rem 1rem", borderRadius: "8px", color: "#8b949e" },
  resultContent: { textAlign: "center", color: "#0d1117" },
  resultIcon: { fontSize: "3.5rem", marginBottom: "0.75rem" },
  resultStatus: { fontSize: "1.3rem", fontWeight: 700, marginBottom: "1rem" },
  employeeInfo: { background: "rgba(0,0,0,0.08)", borderRadius: "8px", padding: "1rem" },
  employeeName: { fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.25rem" },
  employeeDept: { fontSize: "0.9rem", color: "#555", marginBottom: "0.5rem" },
  resultTime: { fontSize: "1rem", fontWeight: 600, marginTop: "0.5rem" },
  confidence: { fontSize: "0.8rem", color: "#777", marginTop: "0.25rem" },
  controls: {
    display: "flex",
    justifyContent: "center",
    gap: "1rem",
    padding: "1.5rem",
    borderTop: "1px solid #21262d",
    background: "#161b22",
  },
  scanBtn: {
    padding: "0.75rem 2.5rem",
    background: "#1f6feb",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "1rem",
    fontWeight: 600,
    cursor: "pointer",
    transition: "opacity 0.2s",
  },
  autoBtn: {
    padding: "0.75rem 2rem",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "1rem",
    fontWeight: 600,
    cursor: "pointer",
  },
};
