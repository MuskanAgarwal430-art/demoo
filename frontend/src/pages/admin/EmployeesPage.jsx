import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import apiClient from "../../services/apiClient";
import { API } from "../../config/api";

export default function EmployeesPage() {
  const { companyCode } = useParams();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ employee_code: "", first_name: "", last_name: "", email: "", phone: "", department: "", designation: "", role: "staff" });
  const [error, setError] = useState("");

  const fetchEmployees = async () => {
    try {
      const res = await apiClient.get(API.EMPLOYEES(companyCode), { params: { search } });
      setEmployees(res.data);
    } catch (e) {
      setError("Failed to load employees.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEmployees(); }, [companyCode, search]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post(API.EMPLOYEES(companyCode), form);
      setShowForm(false);
      setForm({ employee_code: "", first_name: "", last_name: "", email: "", phone: "", department: "", designation: "", role: "staff" });
      fetchEmployees();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to create employee.");
    }
  };

  const handleDelete = async (empCode) => {
    if (!window.confirm("Delete this employee?")) return;
    await apiClient.delete(API.EMPLOYEE(companyCode, empCode));
    fetchEmployees();
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2>Employees — {companyCode}</h2>
        <div style={{ display: "flex", gap: "1rem" }}>
          <input style={styles.search} placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <button style={styles.btn} onClick={() => setShowForm(true)}>+ Add Employee</button>
        </div>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {showForm && (
        <div style={styles.formCard}>
          <h3>New Employee</h3>
          <form onSubmit={handleCreate} style={styles.form}>
            {["employee_code", "first_name", "last_name", "email", "phone", "department", "designation"].map((f) => (
              <input key={f} style={styles.input} placeholder={f.replace("_", " ")} value={form[f]} onChange={(e) => setForm({ ...form, [f]: e.target.value })} />
            ))}
            <select style={styles.input} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="staff">Staff</option>
              <option value="manager">Manager</option>
            </select>
            <div style={{ display: "flex", gap: "1rem" }}>
              <button style={styles.btn} type="submit">Save</button>
              <button style={styles.btnSecondary} type="button" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? <p>Loading...</p> : (
        <table style={styles.table}>
          <thead>
            <tr style={styles.thead}>
              {["Code", "Name", "Dept", "Role", "Status", "Face", "Actions"].map((h) => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {employees.map((emp) => (
              <tr key={emp.employee_code} style={styles.tr}>
                <td style={styles.td}>{emp.employee_code}</td>
                <td style={styles.td}>{emp.full_name}</td>
                <td style={styles.td}>{emp.department}</td>
                <td style={styles.td}>{emp.role}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: emp.status === "active" ? "#e8f5e9" : "#fbe9e7", color: emp.status === "active" ? "#2e7d32" : "#bf360c" }}>
                    {emp.status}
                  </span>
                </td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: emp.face_enrolled ? "#e3f2fd" : "#f5f5f5", color: emp.face_enrolled ? "#1565c0" : "#757575" }}>
                    {emp.face_enrolled ? `Enrolled (${emp.image_count})` : "Not enrolled"}
                  </span>
                </td>
                <td style={styles.td}>
                  <Link to={`/admin/${companyCode}/employees/${emp.employee_code}/enroll`} style={styles.link}>Enroll</Link>
                  {" | "}
                  <button style={styles.linkBtn} onClick={() => handleDelete(emp.employee_code)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const styles = {
  page: { padding: "2rem" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" },
  search: { padding: "0.5rem 0.75rem", border: "1px solid #ddd", borderRadius: "4px", fontSize: "0.9rem", width: "220px" },
  btn: { padding: "0.5rem 1rem", background: "#1976d2", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600 },
  btnSecondary: { padding: "0.5rem 1rem", background: "#eee", color: "#333", border: "none", borderRadius: "4px", cursor: "pointer" },
  error: { background: "#fff0f0", color: "#d32f2f", padding: "0.75rem", borderRadius: "4px", marginBottom: "1rem" },
  formCard: { background: "#f9f9f9", border: "1px solid #eee", borderRadius: "8px", padding: "1.5rem", marginBottom: "1.5rem" },
  form: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" },
  input: { padding: "0.5rem 0.75rem", border: "1px solid #ddd", borderRadius: "4px", fontSize: "0.9rem" },
  table: { width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: "8px", overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.07)" },
  thead: { background: "#1976d2" },
  th: { color: "#fff", padding: "0.75rem 1rem", textAlign: "left", fontWeight: 600, fontSize: "0.9rem" },
  tr: { borderBottom: "1px solid #f0f0f0" },
  td: { padding: "0.75rem 1rem", fontSize: "0.9rem" },
  badge: { padding: "0.2rem 0.6rem", borderRadius: "12px", fontSize: "0.8rem", fontWeight: 600 },
  link: { color: "#1976d2", textDecoration: "none", fontWeight: 500 },
  linkBtn: { background: "none", border: "none", color: "#d32f2f", cursor: "pointer", fontWeight: 500, padding: 0 },
};
