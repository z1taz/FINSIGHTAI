import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  Users, Activity, ShieldAlert, DollarSign, 
  RefreshCw, CheckCircle2, ShieldCheck, Clock
} from 'lucide-react';

export default function AdminPortal({ currency = 'INR' }) {
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [usersData, statsData] = await Promise.all([
        adminAPI.getUsers(),
        adminAPI.getStats()
      ]);
      setUsers(usersData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load admin telemetry:", err);
      setError("Failed to load creator admin data. Ensure you have admin privileges.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div>
          <div style={styles.badge}>
            <ShieldCheck size={14} color="#10b981" /> Creator Admin Control
          </div>
          <h1 style={styles.title}>Application Telemetry & User Registry</h1>
          <p style={styles.subtitle}>
            Monitor active users, user transaction volume, and system-wide fraud detection activity.
          </p>
        </div>
        <button onClick={fetchData} style={styles.refreshBtn} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Refreshing...' : 'Refresh Telemetry'}
        </button>
      </header>

      {error && (
        <div style={styles.errorBanner}>
          <ShieldAlert size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Registered Users</span>
              <div style={{ ...styles.iconBox, backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                <Users size={18} color="#10b981" />
              </div>
            </div>
            <div style={styles.statValue}>{stats.total_users}</div>
            <div style={styles.statSubtext}>Active registered accounts</div>
          </div>

          <div style={styles.statCard}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Total Transactions Logged</span>
              <div style={{ ...styles.iconBox, backgroundColor: 'rgba(59, 130, 246, 0.1)' }}>
                <Activity size={18} color="#3b82f6" />
              </div>
            </div>
            <div style={styles.statValue}>{stats.total_transactions.toLocaleString()}</div>
            <div style={styles.statSubtext}>Across all user accounts</div>
          </div>

          <div style={styles.statCard}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>Flagged Anomaly Alerts</span>
              <div style={{ ...styles.iconBox, backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                <ShieldAlert size={18} color="#ef4444" />
              </div>
            </div>
            <div style={{ ...styles.statValue, color: '#ef4444' }}>{stats.total_flagged_anomalies}</div>
            <div style={styles.statSubtext}>Detected by Isolation Forest AI</div>
          </div>

          <div style={styles.statCard}>
            <div style={styles.statHeader}>
              <span style={styles.statLabel}>System Volume</span>
              <div style={{ ...styles.iconBox, backgroundColor: 'rgba(245, 158, 11, 0.1)' }}>
                <DollarSign size={18} color="#f59e0b" />
              </div>
            </div>
            <div style={styles.statValue}>{formatCurrency(stats.total_system_volume, currency)}</div>
            <div style={styles.statSubtext}>Total transaction processing value</div>
          </div>
        </div>
      )}

      {/* Users Table Card */}
      <div style={styles.tableCard}>
        <div style={styles.tableHeader}>
          <h2 style={styles.tableTitle}>Registered Accounts Registry ({users.length})</h2>
          <span style={styles.tableSub}>Live view of all users registered in the system</span>
        </div>

        <div style={styles.tableWrapper}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>ID</th>
                <th style={styles.th}>User / Email</th>
                <th style={styles.th}>Role</th>
                <th style={styles.th}>Monthly Income</th>
                <th style={styles.th}>Total Transactions</th>
                <th style={styles.th}>Last Login</th>
                <th style={styles.th}>Joined Date</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={styles.tr}>
                  <td style={styles.td}>
                    <span style={styles.idBadge}>#{u.id}</span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.userNameText}>{u.full_name}</div>
                    <div style={styles.userEmailText}>{u.email}</div>
                  </td>
                  <td style={styles.td}>
                    {u.is_admin ? (
                      <span style={styles.adminBadge}>
                        <ShieldCheck size={12} /> Creator / Admin
                      </span>
                    ) : (
                      <span style={styles.userRoleBadge}>User</span>
                    )}
                  </td>
                  <td style={styles.td}>
                    <span style={styles.incomeText}>
                      {formatCurrency(u.monthly_income, currency)}/mo
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span style={styles.txCountBadge}>
                      {u.total_transactions.toLocaleString()} txs
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.timeCell}>
                      <Clock size={12} color="#9ca3af" />
                      <span>
                        {u.last_login_at
                          ? new Date(u.last_login_at).toLocaleString()
                          : 'Just now (active session)'}
                      </span>
                    </div>
                  </td>
                  <td style={styles.td}>
                    <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    padding: '2rem',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '2rem',
    flexWrap: 'wrap',
    gap: '1rem',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.4rem',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    color: '#10b981',
    fontSize: '0.75rem',
    fontWeight: '600',
    padding: '0.25rem 0.6rem',
    borderRadius: '20px',
    marginBottom: '0.5rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: '700',
    color: '#f3f4f6',
    margin: 0,
  },
  subtitle: {
    color: '#9ca3af',
    fontSize: '0.95rem',
    marginTop: '0.25rem',
  },
  refreshBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-color)',
    color: '#f3f4f6',
    padding: '0.6rem 1.2rem',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: '500',
    fontSize: '0.9rem',
    transition: 'all 0.2s',
  },
  errorBanner: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    color: '#ef4444',
    padding: '1rem',
    borderRadius: '10px',
    marginBottom: '1.5rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '1.25rem',
    marginBottom: '2rem',
  },
  statCard: {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-color)',
    borderRadius: '14px',
    padding: '1.25rem',
  },
  statHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  statLabel: {
    fontSize: '0.85rem',
    color: '#9ca3af',
    fontWeight: '500',
  },
  iconBox: {
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  statValue: {
    fontSize: '1.75rem',
    fontWeight: '700',
    color: '#f3f4f6',
  },
  statSubtext: {
    fontSize: '0.75rem',
    color: '#6b7280',
    marginTop: '0.25rem',
  },
  tableCard: {
    backgroundColor: 'var(--bg-secondary)',
    border: '1px solid var(--border-color)',
    borderRadius: '16px',
    overflow: 'hidden',
  },
  tableHeader: {
    padding: '1.25rem 1.5rem',
    borderBottom: '1px solid var(--border-color)',
  },
  tableTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    color: '#f3f4f6',
    margin: 0,
  },
  tableSub: {
    fontSize: '0.85rem',
    color: '#9ca3af',
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
  },
  th: {
    padding: '0.85rem 1.5rem',
    fontSize: '0.75rem',
    fontWeight: '600',
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    borderBottom: '1px solid var(--border-color)',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  },
  tr: {
    borderBottom: '1px solid var(--border-color)',
    transition: 'background-color 0.15s',
  },
  td: {
    padding: '1rem 1.5rem',
    verticalAlign: 'middle',
  },
  idBadge: {
    fontFamily: 'monospace',
    fontSize: '0.8rem',
    color: '#6b7280',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: '0.2rem 0.5rem',
    borderRadius: '6px',
  },
  userNameText: {
    fontWeight: '600',
    color: '#f3f4f6',
    fontSize: '0.9rem',
  },
  userEmailText: {
    fontSize: '0.8rem',
    color: '#9ca3af',
  },
  adminBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.3rem',
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    color: '#10b981',
    fontSize: '0.75rem',
    fontWeight: '600',
    padding: '0.2rem 0.6rem',
    borderRadius: '20px',
  },
  userRoleBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    color: '#9ca3af',
    fontSize: '0.75rem',
    fontWeight: '500',
    padding: '0.2rem 0.6rem',
    borderRadius: '20px',
  },
  incomeText: {
    fontWeight: '600',
    color: '#10b981',
    fontSize: '0.85rem',
  },
  txCountBadge: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    color: '#3b82f6',
    fontSize: '0.8rem',
    fontWeight: '500',
    padding: '0.2rem 0.5rem',
    borderRadius: '6px',
  },
  timeCell: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    fontSize: '0.8rem',
    color: '#9ca3af',
  },
};
