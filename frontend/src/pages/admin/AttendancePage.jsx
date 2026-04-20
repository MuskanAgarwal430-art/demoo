import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import apiClient from "../../services/apiClient";
import { API } from "../../config/api";

export default function AttendancePage() {
  const { companyCode } = useParams();
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [filters, setFilters] = useState({ date: new Date().toISOString().split("T")[0], employee_code: "" });
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.date) params.date = filters.date;
      if (filters.employee_code) params.employee_code = filters.employee_code;

      const [recRes, sumRes] = await Promise.all([
        apiClient.get(API.ATTENDANCE(companyCode), { params }),
        apiClient.get(API.ATTENDANCE_SUMMARY(companyCode), { params: { date: filters.date } }),
      ]);
      setRecords(recRes.data.results || []);
      setSummary(sumRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filters]);

  const exportExcel = () => {
    const url = `${API.ATTENDANCE_EXPORT(companyCode)}?start_date=${filters.date}&end_date=${filters.date}`;
    window.open(url, "_blank");
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2>Attendance — {companyCode}</h2>
        <button style={styles.btn} onClick={exportExcel}>⬇ Export Excel</button>
      </div>

      {summary && (
        <div style={styles.summaryRow}>
          {[
            { label: "Total", value: summary.total_employees, color: "#1976d2" },
            { label: "Present", value: summary.present, color: "#2e7d32" },
            { label: "Late", value: summary.late, color: "#f57c00" },
            { label: "Absent", value: summary.absent, color: "#d32f2f" },
            { label: "Half Day", value: summary.half_day, color: "#7b1fa2" },
          ].map((s) => (
            <div key={s.label} style={{ ...styles.summaryCard, borderTop: `3px solid ${s.color}` }}>
              <div style={{ ...styles.summaryValue, color: s.color }}>{s.value}</div>
              <div style={styles.summaryLabel}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div style={styles.filters}>
        <input type="date" style={styles.input} value={filters.date} onChange={(e) => setFilters({ ...filters, date: e.target.value })} />
        <input style={styles.input} placeholder="Employee code" value={filters.employee_code} onChange={(e) => setFilters({ ...filters, employee_code: e.target.value })} />
      </div>

      {loading ? <p>Loading...</p> : (
        <table style={styles.table}>
          <thead>
            <tr style={styles.thead}>
              {["Employee", "Name", "Check In", "Check Out", "Duration", "Status", "Confidence"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id} style={styles.tr}>
                <td style={styles.td}>{r.employee_code}</td>
                <td style={styles.td}>{r.employee_name}</td>
                <td style={styles.td}>{r.check_in ? new Date(r.check_in).toLocaleTimeString() : "—"}</td>
                <td style={styles.td}>{r.check_out ? new Date(r.check_out).toLocaleTimeString() : "—"}</td>
                <td style={styles.td}>{r.work_duration || "—"}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, ...statusStyle(r.status) }}>{r.status}</span>
                </td>
                <td style={styles.td}>{r.check_in_confidence ? `${(r.check_in_confidence * 100).toFixed(1)}%` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const statusStyle = (s) => ({
  background: s === "present" ? "#e8f5e9" : s === "late" ? "#fff3e0" : s === "absent" ? "#ffebee" : "#f3e5f5",
  color: s === "present" ? "#2e7d32" : s === "late" ? "#e65100" : s === "absent" ? "#c62828" : "#6a1b9a",
});

const styles = {
  page: { padding: "2rem" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" },
  btn: { padding: "0.5rem 1rem", background: "#1976d2", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600 },
  summaryRow: { display: "flex", gap: "1rem", marginBottom: "1.5rem" },
  summaryCard: { background: "#fff", padding: "1rem 1.5rem", borderRadius: "8px", boxShadow: "0 1px 4px rgba(0,0,0,0.07)", flex: 1, textAlign: "center" },
  summaryValue: { fontSize: "2rem", fontWeight: 700 },
  summaryLabel: { fontSize: "0.85rem", color: "#888", marginTop: "0.25rem" },
  filters: { display: "flex", gap: "1rem", marginBottom: "1rem" },
  input: { padding: "0.5rem 0.75rem", border: "1px solid #ddd", borderRadius: "4px", fontSize: "0.9rem" },
  table: { width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: "8px", overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.07)" },
  thead: { background: "#1976d2" },
  th: { color: "#fff", padding: "0.75rem 1rem", textAlign: "left", fontWeight: 600, fontSize: "0.9rem" },
  tr: { borderBottom: "1px solid #f0f0f0" },
  td: { padding: "0.75rem 1rem", fontSize: "0.9rem" },
  badge: { padding: "0.2rem 0.6rem", borderRadius: "12px", fontSize: "0.8rem", fontWeight: 600 },
};
