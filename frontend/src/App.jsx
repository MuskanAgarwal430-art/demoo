import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import LoginPage from "./pages/admin/LoginPage";
import DashboardPage from "./pages/admin/DashboardPage";
import EmployeesPage from "./pages/admin/EmployeesPage";
import EnrollPage from "./pages/admin/EnrollPage";
import AttendancePage from "./pages/admin/AttendancePage";
import KioskPage from "./pages/kiosk/KioskPage";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: "2rem" }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AdminLayout({ children }) {
  const { user, logout } = useAuth();
  const { companyCode } = useParams();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={sidebarStyle}>
        <Link to="/admin/dashboard" style={{ textDecoration: "none" }}>
          <div style={{ fontWeight: 700, fontSize: "1.1rem", marginBottom: "2rem", color: "#fff" }}>
            Face Attendance
          </div>
        </Link>
        <nav>
          {user?.role === "superadmin" && (
            <Link to="/admin/dashboard" style={navLink}>🏢 Companies</Link>
          )}
          {companyCode && companyCode !== "dashboard" && (
            <>
              <Link to={`/admin/${companyCode}/employees`} style={navLink}>👥 Employees</Link>
              <Link to={`/admin/${companyCode}/attendance`} style={navLink}>📋 Attendance</Link>
              <a href={`/kiosk/${companyCode}`} style={navLink} target="_blank" rel="noreferrer">📷 Kiosk ↗</a>
            </>
          )}
          {user?.role !== "superadmin" && user?.company?.company_code && (
            <>
              <Link to={`/admin/${user.company.company_code}/employees`} style={navLink}>👥 Employees</Link>
              <Link to={`/admin/${user.company.company_code}/attendance`} style={navLink}>📋 Attendance</Link>
              <a href={`/kiosk/${user.company.company_code}`} style={navLink} target="_blank" rel="noreferrer">📷 Kiosk ↗</a>
            </>
          )}
        </nav>
        <div style={{ marginTop: "auto", paddingTop: "2rem" }}>
          <div style={{ color: "#c5cae9", fontSize: "0.85rem", marginBottom: "0.25rem" }}>{user?.name}</div>
          <div style={{ color: "#7986cb", fontSize: "0.75rem", marginBottom: "0.75rem" }}>{user?.role}</div>
          <button onClick={logout} style={logoutBtn}>Logout</button>
        </div>
      </aside>
      <main style={{ flex: 1, background: "#f5f6fa", overflowY: "auto" }}>{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/kiosk/:companyCode" element={<KioskPage />} />
          <Route
            path="/admin/dashboard"
            element={<ProtectedRoute><AdminLayout><DashboardPage /></AdminLayout></ProtectedRoute>}
          />
          <Route
            path="/admin/:companyCode/employees"
            element={<ProtectedRoute><AdminLayout><EmployeesPage /></AdminLayout></ProtectedRoute>}
          />
          <Route
            path="/admin/:companyCode/employees/:employeeCode/enroll"
            element={<ProtectedRoute><AdminLayout><EnrollPage /></AdminLayout></ProtectedRoute>}
          />
          <Route
            path="/admin/:companyCode/attendance"
            element={<ProtectedRoute><AdminLayout><AttendancePage /></AdminLayout></ProtectedRoute>}
          />
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

const sidebarStyle = { width: "220px", background: "#1a237e", padding: "1.5rem", display: "flex", flexDirection: "column" };
const navLink = { display: "block", color: "#c5cae9", textDecoration: "none", padding: "0.6rem 0", fontSize: "0.9rem", fontWeight: 500 };
const logoutBtn = { background: "rgba(255,255,255,0.1)", color: "#fff", border: "none", padding: "0.5rem 1rem", borderRadius: "4px", cursor: "pointer", width: "100%" };
