import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(form.email, form.password);
      if (user.role === "superadmin" || !user.company) {
        navigate("/admin/dashboard");
      } else {
        navigate(`/admin/${user.company.company_code}/employees`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Admin Login</h2>
        <p style={styles.subtitle}>Face Attendance SaaS</p>
        {error && <div style={styles.error}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              style={styles.input}
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <button style={styles.button} type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f0f2f5" },
  card: { background: "#fff", padding: "2rem", borderRadius: "8px", boxShadow: "0 2px 16px rgba(0,0,0,0.1)", width: "360px" },
  title: { margin: "0 0 0.25rem", fontSize: "1.5rem", fontWeight: 700 },
  subtitle: { margin: "0 0 1.5rem", color: "#888", fontSize: "0.9rem" },
  error: { background: "#fff0f0", color: "#d32f2f", padding: "0.75rem", borderRadius: "4px", marginBottom: "1rem", fontSize: "0.9rem" },
  field: { marginBottom: "1rem" },
  label: { display: "block", marginBottom: "0.4rem", fontWeight: 500, fontSize: "0.9rem" },
  input: { width: "100%", padding: "0.6rem 0.75rem", border: "1px solid #ddd", borderRadius: "4px", fontSize: "0.95rem", boxSizing: "border-box" },
  button: { width: "100%", padding: "0.75rem", background: "#1976d2", color: "#fff", border: "none", borderRadius: "4px", fontSize: "1rem", fontWeight: 600, cursor: "pointer" },
};
