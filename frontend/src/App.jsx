import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Anomalies from './pages/Anomalies';
import AdminPortal from './pages/AdminPortal';
import CasesQueue from './pages/CasesQueue';
import CaseInvestigation from './pages/CaseInvestigation';
import NetworkIntelligence from './pages/NetworkIntelligence';
import PolicySimulation from './pages/PolicySimulation';
import EvaluationDashboard from './pages/EvaluationDashboard';
import ModelGovernance from './pages/ModelGovernance';
import Login from './pages/Login';
import Signup from './pages/Signup';
import { authAPI } from './services/api';
import { CURRENCIES, formatCurrency } from './utils/currency';
import { 
  TrendingUp, LayoutDashboard, CreditCard, ShieldAlert, 
  LogOut, User as UserIcon, RefreshCw, ShieldCheck, DollarSign, Edit3, X,
  Briefcase, Layers, Sliders, Activity
} from 'lucide-react';

// Protected Layout component that embeds Sidebar and Navbar Header
function ProtectedLayout({ children, user, handleLogout, currency, setCurrency, onUserUpdated }) {
  const location = useLocation();
  const [showIncomeModal, setShowIncomeModal] = useState(false);
  const [newIncome, setNewIncome] = useState(user?.monthly_income || 400000);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (user?.monthly_income) {
      setNewIncome(user.monthly_income);
    }
  }, [user]);

  const handleIncomeSubmit = async (e) => {
    e.preventDefault();
    setUpdating(true);
    try {
      const updated = await authAPI.updateProfile({ monthly_income: parseFloat(newIncome) });
      onUserUpdated(updated);
      setShowIncomeModal(false);
    } catch (err) {
      alert("Failed to update monthly income");
    } finally {
      setUpdating(false);
    }
  };

  const isCasesActive = location.pathname.startsWith('/cases');

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarBrand}>
          <TrendingUp size={24} color="#10b981" />
          <span style={styles.brandText}>FinSight <span style={{ color: '#10b981' }}>AI</span></span>
        </div>

        <nav style={styles.navMenu}>
          {/* Primary Risk Operations Workflow: Cases */}
          <Link 
            to="/cases" 
            style={{
              ...styles.navLink,
              ...(isCasesActive ? styles.navLinkActiveCases : styles.casesNavLink)
            }}
          >
            <Briefcase size={18} color={isCasesActive ? '#10b981' : '#34d399'} />
            <span style={{ fontWeight: '700' }}>Cases Queue</span>
            <span style={styles.queueTag}>Active</span>
          </Link>

          {/* Network Intelligence */}
          <Link 
            to="/network" 
            style={{
              ...styles.navLink,
              ...(location.pathname === '/network' ? styles.navLinkActive : {})
            }}
          >
            <Layers size={18} />
            <span>Network Graph</span>
          </Link>

          {/* Policy Simulation */}
          <Link 
            to="/policies" 
            style={{
              ...styles.navLink,
              ...(location.pathname === '/policies' ? styles.navLinkActive : {})
            }}
          >
            <Sliders size={18} />
            <span>Policy Simulation</span>
          </Link>

          {/* Evaluation Suite */}
          <Link 
            to="/evaluation" 
            style={{
              ...styles.navLink,
              ...(location.pathname === '/evaluation' ? styles.navLinkActive : {})
            }}
          >
            <Activity size={18} />
            <span>Evaluation Suite</span>
          </Link>

          {/* Model Governance */}
          <Link 
            to="/governance" 
            style={{
              ...styles.navLink,
              ...(location.pathname === '/governance' ? styles.navLinkActive : {})
            }}
          >
            <ShieldCheck size={18} />
            <span>AI Governance</span>
          </Link>

          <div style={{ height: '1px', backgroundColor: 'var(--border-color)', margin: '0.4rem 0' }}></div>

          <Link 
            to="/transactions" 
            style={{
              ...styles.navLink,
              ...(location.pathname === '/transactions' ? styles.navLinkActive : {})
            }}
          >
            <CreditCard size={18} />
            <span>Transactions</span>
          </Link>

          <Link 
            to="/" 
            style={{
              ...styles.navLink,
              ...(location.pathname === '/' ? styles.navLinkActive : {})
            }}
          >
            <LayoutDashboard size={18} />
            <span>Analytics Dashboard</span>
          </Link>

          {/* Admin Navigation */}
          {user?.is_admin && (
            <Link 
              to="/admin" 
              style={{
                ...styles.navLink,
                ...(location.pathname === '/admin' ? styles.navLinkActiveAdmin : styles.adminNavLink)
              }}
            >
              <ShieldCheck size={18} color="#10b981" />
              <span>Creator Admin</span>
              <span style={styles.adminTag}>Pro</span>
            </Link>
          )}
        </nav>

        {/* User Card & Log Out */}
        <div style={styles.sidebarFooter}>
          {user && (
            <div style={styles.userCard}>
              <div style={styles.avatar}>
                <UserIcon size={16} color="#10b981" />
              </div>
              <div style={styles.userInfo}>
                <div style={styles.userName}>{user.full_name}</div>
                <div style={styles.userEmail}>{user.email}</div>
              </div>
            </div>
          )}
          <button onClick={handleLogout} style={styles.logoutBtn}>
            <LogOut size={16} /> Log Out
          </button>
        </div>
      </aside>

      {/* Main Content Area with Header Controls */}
      <div style={{ flex: 1, marginLeft: '260px', display: 'flex', flexDirection: 'column' }}>
        {/* Top Navbar */}
        <header style={styles.topHeader}>
          <div style={styles.topHeaderLeft}>
            <span style={styles.statusIndicator}></span>
            <span style={{ fontSize: '0.85rem', color: '#9ca3af', fontWeight: '500' }}>
              FinSight AI Risk Operations Workstation
            </span>
          </div>

          <div style={styles.topHeaderRight}>
            {/* Monthly Income Button */}
            <button onClick={() => setShowIncomeModal(true)} style={styles.incomeBtn} title="Set Baseline Monthly Income">
              <span style={{ color: '#10b981', fontWeight: 'bold' }}>₹</span>
              <span>Baseline: {formatCurrency(user?.monthly_income || 400000, currency)}</span>
              <Edit3 size={12} color="#9ca3af" />
            </button>

            {/* Currency Selector Dropdown */}
            <div style={styles.currencyWrapper}>
              <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Currency:</span>
              <select 
                value={currency} 
                onChange={(e) => setCurrency(e.target.value)}
                style={styles.currencySelect}
              >
                {CURRENCIES.map((c) => (
                  <option key={c.code} value={c.code}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </header>

        <main className="main-content" style={{ flex: 1 }}>
          {children}
        </main>
      </div>

      {/* Edit Income Modal */}
      {showIncomeModal && createPortal(
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <div style={styles.modalHeader}>
              <h3 style={styles.modalTitle}>Set Monthly Income Baseline</h3>
              <button onClick={() => setShowIncomeModal(false)} style={styles.closeBtn}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleIncomeSubmit} style={{ marginTop: '1rem' }}>
              <label style={styles.label}>Monthly Income (₹ INR):</label>
              <input
                type="number"
                step="5000"
                min="0"
                placeholder="e.g. 400000"
                value={newIncome}
                onChange={(e) => setNewIncome(e.target.value)}
                style={styles.input}
                required
              />
              <p style={styles.helpText}>
                The income baseline is evaluated by the risk engine to calculate income-ratio thresholds (INC-04) and out-of-profile spend deviations.
              </p>
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowIncomeModal(false)} style={styles.cancelBtn}>
                  Cancel
                </button>
                <button type="submit" disabled={updating} style={styles.saveBtn}>
                  {updating ? 'Saving...' : 'Save Baseline'}
                </button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

// Route protector checks authentication token
function RequireAuth({ children, user, loading, handleLogout, currency, setCurrency, onUserUpdated }) {
  const token = localStorage.getItem('token');
  
  if (loading) {
    return (
      <div style={styles.loadingScreen}>
        <RefreshCw className="animate-spin" size={32} color="#10b981" />
        <span style={{ marginTop: '1rem', color: '#9ca3af' }}>Syncing risk telemetry...</span>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <ProtectedLayout 
      user={user} 
      handleLogout={handleLogout} 
      currency={currency} 
      setCurrency={setCurrency}
      onUserUpdated={onUserUpdated}
    >
      {children}
    </ProtectedLayout>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currency, setCurrency] = useState(localStorage.getItem('currency') || 'INR');

  useEffect(() => {
    localStorage.setItem('currency', currency);
  }, [currency]);

  const fetchUser = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      const data = await authAPI.getMe();
      setUser(data);
    } catch (err) {
      console.error("Authentication expired:", err);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        
        {/* Cases Queue (Primary Operations Screen) */}
        <Route 
          path="/cases" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <CasesQueue currency={currency} />
            </RequireAuth>
          } 
        />

        {/* Case Investigation Workstation */}
        <Route 
          path="/cases/:id" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <CaseInvestigation currency={currency} />
            </RequireAuth>
          } 
        />

        {/* Network Intelligence */}
        <Route 
          path="/network" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <NetworkIntelligence />
            </RequireAuth>
          } 
        />

        {/* Policy Simulation */}
        <Route 
          path="/policies" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <PolicySimulation currency={currency} />
            </RequireAuth>
          } 
        />

        {/* Evaluation Suite */}
        <Route 
          path="/evaluation" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <EvaluationDashboard />
            </RequireAuth>
          } 
        />

        {/* Model Governance */}
        <Route 
          path="/governance" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <ModelGovernance />
            </RequireAuth>
          } 
        />

        {/* Transactions */}
        <Route 
          path="/transactions" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <Transactions currency={currency} />
            </RequireAuth>
          } 
        />

        {/* Dashboard */}
        <Route 
          path="/" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <Dashboard currency={currency} user={user} />
            </RequireAuth>
          } 
        />

        {/* Threat Intelligence */}
        <Route 
          path="/anomalies" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <Anomalies currency={currency} />
            </RequireAuth>
          } 
        />

        {/* Admin Portal */}
        <Route 
          path="/admin" 
          element={
            <RequireAuth 
              user={user} 
              loading={loading} 
              handleLogout={handleLogout}
              currency={currency}
              setCurrency={setCurrency}
              onUserUpdated={(updated) => setUser(updated)}
            >
              <AdminPortal currency={currency} />
            </RequireAuth>
          } 
        />
        
        {/* Redirect everything else to /cases */}
        <Route path="*" element={<Navigate to="/cases" replace />} />
      </Routes>
    </Router>
  );
}

const styles = {
  loadingScreen: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: 'var(--bg-primary)',
  },
  sidebar: {
    width: '260px',
    backgroundColor: 'var(--bg-secondary)',
    borderRight: '1px solid var(--border-color)',
    display: 'flex',
    flexDirection: 'column',
    padding: '1.75rem',
    position: 'fixed',
    top: 0,
    bottom: 0,
    left: 0,
    zIndex: 10,
  },
  sidebarBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '2rem',
  },
  brandText: {
    fontFamily: 'var(--font-display)',
    fontWeight: '700',
    fontSize: '1.25rem',
    letterSpacing: '-0.02em',
    color: '#f3f4f6',
  },
  navMenu: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.35rem',
    flex: 1,
    overflowY: 'auto',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.85rem',
    padding: '0.7rem 0.9rem',
    borderRadius: '8px',
    color: '#9ca3af',
    textDecoration: 'none',
    fontWeight: '500',
    fontSize: '0.9rem',
    transition: 'var(--transition-smooth)',
  },
  navLinkActive: {
    backgroundColor: 'var(--primary-glow)',
    color: 'var(--primary)',
    borderLeft: '3px solid var(--primary)',
    borderTopLeftRadius: '0px',
    borderBottomLeftRadius: '0px',
  },
  casesNavLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.85rem',
    padding: '0.75rem 0.9rem',
    borderRadius: '8px',
    color: '#e5e7eb',
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
    textDecoration: 'none',
    fontWeight: '600',
    fontSize: '0.9rem',
    marginBottom: '0.25rem',
  },
  navLinkActiveCases: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.85rem',
    padding: '0.75rem 0.9rem',
    borderRadius: '8px',
    color: '#10b981',
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    border: '1px solid #10b981',
    textDecoration: 'none',
    fontWeight: '700',
    fontSize: '0.9rem',
    marginBottom: '0.25rem',
  },
  queueTag: {
    marginLeft: 'auto',
    fontSize: '0.62rem',
    fontWeight: '800',
    backgroundColor: '#10b981',
    color: '#000',
    padding: '0.12rem 0.4rem',
    borderRadius: '4px',
    textTransform: 'uppercase',
  },
  sidebarFooter: {
    borderTop: '1px solid var(--border-color)',
    paddingTop: '1.25rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.85rem',
  },
  userCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: '8px',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userInfo: {
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
  },
  userName: {
    fontSize: '0.85rem',
    fontWeight: '600',
    color: '#f3f4f6',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userEmail: {
    fontSize: '0.75rem',
    color: '#6b7280',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  adminNavLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.85rem',
    padding: '0.7rem 0.9rem',
    borderRadius: '8px',
    color: '#10b981',
    backgroundColor: 'rgba(16, 185, 129, 0.05)',
    textDecoration: 'none',
    fontWeight: '500',
    fontSize: '0.9rem',
    transition: 'var(--transition-smooth)',
    marginTop: '0.25rem',
  },
  navLinkActiveAdmin: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    color: '#10b981',
    borderLeft: '3px solid #10b981',
    borderTopLeftRadius: '0px',
    borderBottomLeftRadius: '0px',
  },
  adminTag: {
    marginLeft: 'auto',
    fontSize: '0.62rem',
    fontWeight: '700',
    backgroundColor: '#10b981',
    color: '#000',
    padding: '0.12rem 0.4rem',
    borderRadius: '4px',
    textTransform: 'uppercase',
  },
  topHeader: {
    height: '60px',
    backgroundColor: 'var(--bg-secondary)',
    borderBottom: '1px solid var(--border-color)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 2rem',
    position: 'sticky',
    top: 0,
    zIndex: 9,
  },
  topHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  statusIndicator: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#10b981',
    boxShadow: '0 0 8px #10b981',
  },
  topHeaderRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.25rem',
  },
  incomeBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    backgroundColor: 'rgba(16, 185, 129, 0.08)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
    color: '#f3f4f6',
    padding: '0.4rem 0.8rem',
    borderRadius: '8px',
    fontSize: '0.85rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
  currencyWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  currencySelect: {
    backgroundColor: 'var(--bg-primary)',
    color: '#f3f4f6',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    padding: '0.35rem 0.6rem',
    fontSize: '0.85rem',
    fontWeight: '600',
    cursor: 'pointer',
    outline: 'none',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 99999,
    backdropFilter: 'blur(6px)',
  },
  modalContent: {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-color)',
    borderRadius: '16px',
    padding: '1.75rem',
    width: '90%',
    maxWidth: '450px',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: '1.2rem',
    fontWeight: '700',
    color: '#f3f4f6',
    margin: 0,
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#9ca3af',
    cursor: 'pointer',
  },
  label: {
    display: 'block',
    fontSize: '0.85rem',
    fontWeight: '500',
    color: '#9ca3af',
    marginBottom: '0.5rem',
  },
  input: {
    width: '100%',
    padding: '0.75rem 1rem',
    backgroundColor: 'var(--bg-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: '10px',
    color: '#f3f4f6',
    fontSize: '1rem',
    fontWeight: '600',
    outline: 'none',
    boxSizing: 'border-box',
  },
  helpText: {
    fontSize: '0.8rem',
    color: '#6b7280',
    marginTop: '0.5rem',
    lineHeight: 1.4,
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '0.75rem',
    marginTop: '1.5rem',
  },
  cancelBtn: {
    backgroundColor: 'transparent',
    border: '1px solid var(--border-color)',
    color: '#9ca3af',
    padding: '0.6rem 1.25rem',
    borderRadius: '10px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  saveBtn: {
    backgroundColor: '#10b981',
    border: 'none',
    color: '#000',
    padding: '0.6rem 1.25rem',
    borderRadius: '10px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  logoutBtn: {
    background: 'none',
    border: 'none',
    color: '#9ca3af',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.85rem',
    fontWeight: '500',
    padding: '0.5rem 0',
    transition: 'color 0.2s',
    textAlign: 'left',
  },
};
