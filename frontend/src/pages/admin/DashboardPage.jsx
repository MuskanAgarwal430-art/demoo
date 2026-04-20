import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import apiClient from "../../services/apiClient";
import { API } from "../../config/api";
import { useAuth } from "../../context/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    company_code: "", name: "", email: "", phone: "",
    plan: "free", max_employees: 100,
    check_in_start: "09:00:00", check_in_end: "10:00:00", work_hours: 8,
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => { fetchCompanies(); }, []);

  const fetchCompanies = async () => {
    try {
      const res = await apiClient.get(API.COMPANIES);
      setCompanies(res.data.results || res.data);
    } catch (e) {
      setError("Failed to load companies.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    try {
      await apiClient.post(API.COMPANIES, form);
      setSuccess(`Company "${form.name}" created successfully.`);
      setShowForm(false);
      setForm({ company_code: "", name: "", email: "", phone: "", plan: "free", max_employees: 100, check_in_start: "09:00:00", check_in_end: "10:00:00", work_hours: 8 });
      fetchCompanies();
    } catch (e) {
      setError(e.response?.data?.detail || JSON.stringify(e.response?.data) || "Failed to create company.");
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h2 style={{ margin: 0 }}>Dashboard</h2>
          <p style={{ color: "#888", margin: "0.25rem 0 0" }}>Welcome, {user?.name}</p>
        </div>
        {user?.role === "superadmin" && (
          <button style={styles.btn} onClick={() => setShowForm(true)}>+ New Company</button>
        )}
      </div>

      {error && <div style={styles.error}>{error}</div>}
      {success && <div style={styles.success}>{success}</div>}

      {showForm && (
        <div style={styles.formCard}>
          <h3 style={{ marginTop: 0 }}>Create Company</h3>
          <form onSubmit={handleCreate} style={styles.form}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Company Code *</label>
              <input style={styles.input} placeholder="e.g. ACME" value={form.company_code}
                onChange={(e) => setForm({ ...form, company_code: e.target.value.toUpperCase() })} required />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Company Name *</label>
              <input style={styles.input} placeholder="Acme Corp" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email</label>
              <input style={styles.input} type="email" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Phone</label>
              <input style={styles.input} value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Plan</label>
              <select style={styles.input} value={form.plan} onChange={(e) => setForm({ ...form, plan: e.target.value })}>
                <option value="free">Free</option>
                <option value="pro">Pro</option>
                <option value="business">Business</option>
              </select>
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Max Employees</label>
              <input style={styles.input} type="number" value={form.max_employees}
                onChange={(e) => setForm({ ...form, max_employees: e.target.value })} />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Check-in Start</label>
              <input style={styles.input} type="time" value={form.check_in_start}
                onChange={(e) => setForm({ ...form, check_in_start: e.target.value })} />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Check-in End</label>
              <input style={styles.input} type="time" value={form.check_in_end}
                onChange={(e) => setForm({ ...form, check_in_end: e.target.value })} />
            </div>
            <div style={{ gridColumn: "1 / -1", display: "flex", gap: "1rem", marginTop: "0.5rem" }}>
              <button style={styles.btn} type="submit">Create</button>
              <button style={styles.btnSecondary} type="button" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? <p>Loading...</p> : (
        <div style={styles.grid}>
          {companies.length === 0 ? (
            <p style={{ color: "#888" }}>No companies yet. Create one above.</p>
          ) : (
            companies.map((c) => (
              <div key={c.company_code} style={styles.card}>
                <div style={styles.cardHeader}>
                  <span style={styles.cardCode}>{c.company_code}</span>
                  <span style={{ ...styles.planBadge, background: c.plan === "business" ? "#e8f5e9" : c.plan === "pro" ? "#e3f2fd" : "#f5f5f5" }}>
                    {c.plan}
                  </span>
                </div>
                <h3 style={styles.cardName}>{c.name}</h3>
                <p style={styles.cardMeta}>{c.email || "No email"}</p>
                <p style={styles.cardMeta}>Max employees: {c.max_employees}</p>
                <p style={styles.cardMeta}>Check-in: {c.check_in_start} – {c.check_in_end}</p>
                <div style={styles.cardActions}>
                  <Link to={`/admin/${c.company_code}/employees`} style={styles.actionLink}>Employees</Link>
                  <Link to={`/admin/${c.company_code}/attendance`} style={styles.actionLink}>Attendance</Link>
                  <a href={`/kiosk/${c.company_code}`} target="_blank" rel="noreferrer" style={{ ...styles.actionLink, color: "#2e7d32" }}>Kiosk ↗</a>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  page: { padding: "2rem" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" },
  btn: { padding: "0.5rem 1.25rem", background: "#1976d2", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600 },
  btnSecondary: { padding: "0.5rem 1.25rem", background: "#eee", color: "#333", border: "none", borderRadius: "4px", cursor: "pointer" },
  error: { background: "#fff0f0", color: "#d32f2f", padding: "0.75rem", borderRadius: "4px", marginBottom: "1rem" },
  success: { background: "#e8f5e9", color: "#2e7d32", padding: "0.75rem", borderRadius: "4px", marginBottom: "1rem" },
  formCard: { background: "#f9f9f9", border: "1px solid #eee", borderRadius: "8px", padding: "1.5rem", marginBottom: "1.5rem" },
  form: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" },
  formGroup: { display: "flex", flexDirection: "column", gap: "0.3rem" },
  label: { fontSize: "0.85rem", fontWeight: 500, color: "#555" },
  input: { padding: "0.5rem 0.75rem", border: "1px solid #ddd", borderRadius: "4px", fontSize: "0.9rem" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.25rem" },
  card: { background: "#fff", borderRadius: "8px", padding: "1.25rem", boxShadow: "0 1px 4px rgba(0,0,0,0.08)", border: "1px solid #f0f0f0" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" },
  cardCode: { fontWeight: 700, fontSize: "0.85rem", color: "#1976d2", background: "#e3f2fd", padding: "0.2rem 0.6rem", borderRadius: "4px" },
  planBadge: { fontSize: "0.75rem", padding: "0.2rem 0.6rem", borderRadius: "12px", fontWeight: 600, color: "#555" },
  cardName: { margin: "0 0 0.5rem", fontSize: "1.1rem" },
  cardMeta: { margin: "0.15rem 0", fontSize: "0.85rem", color: "#888" },
  cardActions: { display: "flex", gap: "1rem", marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid #f0f0f0" },
  actionLink: { color: "#1976d2", textDecoration: "none", fontSize: "0.9rem", fontWeight: 500 },
};
