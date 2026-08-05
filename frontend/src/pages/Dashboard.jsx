import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsAPI, transactionsAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  AreaChart, Area, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { 
  TrendingUp, TrendingDown, DollarSign, AlertTriangle, 
  ArrowRight, ShieldAlert, Calendar, RefreshCw, Wallet, PiggyBank
} from 'lucide-react';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#374151', '#06b6d4', '#14b8a6'];

export default function Dashboard({ currency = 'INR', user }) {
  const [spendingData, setSpendingData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ balance: 0, income: 0, expense: 0 });

  const monthlyIncome = user?.monthly_income || 5000;

  const fetchData = async () => {
    setLoading(true);
    try {
      const [spending, trend, txs, anomalyList] = await Promise.all([
        analyticsAPI.getSpendingSummary(),
        analyticsAPI.getMonthlyTrend(),
        transactionsAPI.getTransactions({ page: 1, limit: 5 }),
        analyticsAPI.getAnomalies()
      ]);

      setSpendingData(spending);
      setTrendData(trend);
      setRecentTransactions(txs.items);
      setAnomalies(anomalyList);

      // Compute statistics based on trend
      if (trend.length > 0) {
        const latestMonth = trend[trend.length - 1];
        const income = latestMonth.income;
        const expense = latestMonth.expense;
        const balance = income - expense;
        setStats({ balance, income, expense });
      }
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <RefreshCw className="animate-spin" size={32} color="#10b981" />
        <p style={{ marginTop: '1rem', color: '#9ca3af' }}>Gathering financial insights...</p>
      </div>
    );
  }

  const budgetUsedPercent = Math.min(100, Math.round((stats.expense / monthlyIncome) * 100));

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: '700' }}>Dashboard</h1>
          <p style={{ color: '#9ca3af', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Real-time financial analytics and threat detection intelligence.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={fetchData}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Fraud Alert Notification Banner */}
      {anomalies.length > 0 && (
        <div style={styles.alertBanner}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={styles.alertIconWrapper}>
              <ShieldAlert size={20} color="#ef4444" />
            </div>
            <div>
              <h4 style={{ color: '#ef4444', fontWeight: '600' }}>
                Anomaly Detection Alert ({anomalies.length} Flagged)
              </h4>
              <p style={{ color: '#f3f4f6', fontSize: '0.85rem', marginTop: '0.1rem' }}>
                Our ML engine detected suspicious transaction behaviors requiring review.
              </p>
            </div>
          </div>
          <Link to="/anomalies" className="btn btn-danger" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
            Inspect Threats <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* KPI Cards */}
      <div style={styles.kpiGrid}>
        <div className="card" style={styles.kpiCard}>
          <div style={styles.kpiHeader}>
            <span style={{ color: '#9ca3af', fontWeight: '500', fontSize: '0.85rem' }}>MONTHLY INCOME TARGET</span>
            <div style={{ ...styles.kpiIcon, backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
              <PiggyBank size={20} color="#10b981" />
            </div>
          </div>
          <h2 style={{ fontSize: '2rem', marginTop: '0.5rem', color: '#10b981' }}>
            {formatCurrency(monthlyIncome, currency)}
          </h2>
          <span style={{ color: '#9ca3af', fontSize: '0.8rem', display: 'block', marginTop: '0.5rem' }}>
            Base user income baseline
          </span>
        </div>

        <div className="card" style={styles.kpiCard}>
          <div style={styles.kpiHeader}>
            <span style={{ color: '#9ca3af', fontWeight: '500', fontSize: '0.85rem' }}>TOTAL MONTHLY OUTFLOW</span>
            <div style={{ ...styles.kpiIcon, backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
              <TrendingDown size={20} color="#ef4444" />
            </div>
          </div>
          <h2 style={{ fontSize: '2rem', marginTop: '0.5rem' }}>
            {formatCurrency(stats.expense, currency)}
          </h2>
          <div style={{ marginTop: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.25rem' }}>
              <span>Budget Usage</span>
              <span style={{ fontWeight: '600', color: budgetUsedPercent > 90 ? '#ef4444' : '#10b981' }}>{budgetUsedPercent}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${budgetUsedPercent}%`, height: '100%', backgroundColor: budgetUsedPercent > 90 ? '#ef4444' : '#10b981', borderRadius: '3px' }}></div>
            </div>
          </div>
        </div>

        <div className="card" style={styles.kpiCard}>
          <div style={styles.kpiHeader}>
            <span style={{ color: '#9ca3af', fontWeight: '500', fontSize: '0.85rem' }}>NET MONTHLY SAVINGS</span>
            <div style={{ ...styles.kpiIcon, backgroundColor: 'rgba(59, 130, 246, 0.1)' }}>
              <Wallet size={20} color="#3b82f6" />
            </div>
          </div>
          <h2 style={{ fontSize: '2rem', marginTop: '0.5rem', color: (monthlyIncome - stats.expense) >= 0 ? '#3b82f6' : '#ef4444' }}>
            {formatCurrency(monthlyIncome - stats.expense, currency)}
          </h2>
          <span style={{ color: '#3b82f6', fontSize: '0.8rem', display: 'block', marginTop: '0.5rem' }}>
            Net monthly liquidity cushion
          </span>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={styles.chartsGrid}>
        {/* Income vs Expense Line/Area Chart */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h3 style={styles.cardTitle}>Cashflow Trends</h3>
          <div style={{ width: '100%', height: 300 }}>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorExpense" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#242f47" />
                  <XAxis dataKey="month" stroke="#9ca3af" fontSize={12} />
                  <YAxis stroke="#9ca3af" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#121826', borderColor: '#242f47', color: '#f3f4f6' }} />
                  <Legend verticalAlign="top" height={36} />
                  <Area type="monotone" dataKey="income" name="Income" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorIncome)" />
                  <Area type="monotone" dataKey="expense" name="Expense" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorExpense)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={styles.noData}>No cashflow history to render chart.</div>
            )}
          </div>
        </div>

        {/* Category Breakdown Pie Chart */}
        <div className="card">
          <h3 style={styles.cardTitle}>Spending by Category</h3>
          <div style={{ width: '100%', height: 300, position: 'relative' }}>
            {spendingData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={spendingData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="total"
                    nameKey="category"
                  >
                    {spendingData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => formatCurrency(value, currency)} contentStyle={{ backgroundColor: '#121826', borderColor: '#242f47', color: '#f3f4f6' }} />
                  <Legend layout="horizontal" verticalAlign="bottom" align="center" iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div style={styles.noData}>No spending categories available.</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Transactions List */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>Recent Operations</h3>
          <Link to="/transactions" style={{ color: '#10b981', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem', fontWeight: '500' }}>
            View Statement <ArrowRight size={14} />
          </Link>
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>DATE</th>
                <th>MERCHANT</th>
                <th>CATEGORY</th>
                <th>STATUS</th>
                <th style={{ textAlign: 'right' }}>AMOUNT</th>
              </tr>
            </thead>
            <tbody>
              {recentTransactions.map((tx) => (
                <tr key={tx.id}>
                  <td style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Calendar size={14} color="#6b7280" />
                    {new Date(tx.transaction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </td>
                  <td>{tx.merchant}</td>
                  <td>
                    <span className="badge" style={{ backgroundColor: 'rgba(36, 47, 71, 0.4)', color: '#f3f4f6' }}>
                      {tx.category}
                    </span>
                  </td>
                  <td>
                    {tx.is_fraudulent === 1 ? (
                      <span className="badge badge-danger">Anomaly</span>
                    ) : (
                      <span className="badge badge-success">Approved</span>
                    )}
                  </td>
                  <td style={{ fontWeight: '600', textAlign: 'right', color: tx.category === 'Salary' ? '#10b981' : '#f3f4f6' }}>
                    {tx.category === 'Salary' ? '+' : '-'}{formatCurrency(tx.amount, currency)}
                  </td>
                </tr>
              ))}
              {recentTransactions.length === 0 && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: '#9ca3af', padding: '2rem' }}>
                    No recent transaction activities found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


const styles = {
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '60vh',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alertBanner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '12px',
    padding: '1rem 1.25rem',
  },
  alertIconWrapper: {
    display: 'flex',
    padding: '0.5rem',
    borderRadius: '8px',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '1.5rem',
  },
  kpiCard: {
    display: 'flex',
    flexDirection: 'column',
  },
  kpiHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  kpiIcon: {
    display: 'flex',
    padding: '0.5rem',
    borderRadius: '8px',
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1.5rem',
  },
  cardTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    marginBottom: '1.5rem',
  },
  noData: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#6b7280',
    fontSize: '0.9rem',
  },
};
