import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { casesAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  ShieldAlert, ShieldCheck, AlertTriangle, ArrowRight, Search, 
  Filter, RefreshCw, CheckCircle2, Clock, Users, Activity, FileText
} from 'lucide-react';

export default function CasesQueue({ currency = 'INR' }) {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchQueueData = async () => {
    setLoading(true);
    try {
      const [casesData, statsData] = await Promise.all([
        casesAPI.listCases({
          page,
          limit: 20,
          status: statusFilter || undefined,
          risk_level: riskFilter || undefined,
          search: searchTerm || undefined
        }),
        casesAPI.getStats()
      ]);
      setCases(casesData.items || []);
      setTotalPages(casesData.pages || 1);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to fetch cases queue:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueData();
  }, [page, statusFilter, riskFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchQueueData();
  };

  const getRiskBadge = (level, score) => {
    let bg = 'rgba(59, 130, 246, 0.15)';
    let color = '#60a5fa';
    let border = 'rgba(59, 130, 246, 0.3)';

    if (level === 'CRITICAL' || score >= 75) {
      bg = 'rgba(239, 68, 68, 0.15)';
      color = '#f87171';
      border = 'rgba(239, 68, 68, 0.3)';
    } else if (level === 'HIGH' || score >= 50) {
      bg = 'rgba(245, 158, 11, 0.15)';
      color = '#fbbf24';
      border = 'rgba(245, 158, 11, 0.3)';
    } else if (level === 'MEDIUM') {
      bg = 'rgba(234, 179, 8, 0.15)';
      color = '#facc15';
      border = 'rgba(234, 179, 8, 0.3)';
    }

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: '0.2rem 0.6rem',
        borderRadius: '4px',
        fontSize: '0.75rem',
        fontWeight: '700',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
        letterSpacing: '0.04em'
      }}>
        <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: color }}></span>
        {level} ({Math.round(score)})
      </span>
    );
  };

  const getStatusBadge = (status) => {
    const map = {
      'NEW': { label: 'NEW ALERT', bg: 'rgba(59, 130, 246, 0.1)', color: '#93c5fd' },
      'INVESTIGATING': { label: 'IN PROGRESS', bg: 'rgba(168, 85, 247, 0.1)', color: '#c084fc' },
      'AI_REVIEWED': { label: 'AI REVIEWED', bg: 'rgba(20, 184, 166, 0.1)', color: '#2dd4bf' },
      'PENDING_HUMAN_DECISION': { label: 'PENDING DECISION', bg: 'rgba(245, 158, 11, 0.1)', color: '#fbbf24' },
      'ESCALATED': { label: 'ESCALATED', bg: 'rgba(239, 68, 68, 0.1)', color: '#f87171' },
      'CONFIRMED_FRAUD': { label: 'CONFIRMED FRAUD', bg: 'rgba(220, 38, 38, 0.2)', color: '#ef4444' },
      'FALSE_POSITIVE': { label: 'FALSE POSITIVE', bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399' },
      'CLOSED': { label: 'CLOSED', bg: 'rgba(107, 114, 128, 0.15)', color: '#9ca3af' }
    };
    const s = map[status] || { label: status, bg: 'rgba(107, 114, 128, 0.1)', color: '#9ca3af' };
    return (
      <span style={{
        padding: '0.2rem 0.5rem',
        borderRadius: '4px',
        fontSize: '0.7rem',
        fontWeight: '600',
        backgroundColor: s.bg,
        color: s.color,
        textTransform: 'uppercase'
      }}>
        {s.label}
      </span>
    );
  };

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <ShieldAlert size={24} color="#10b981" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: '700', color: '#f3f4f6', margin: 0, letterSpacing: '-0.02em' }}>
              Fraud Investigation Cases
            </h1>
          </div>
          <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Internal risk-operations queue. Adjudicate suspicious transactions, inspect evidence trails, and record binding decisions.
          </p>
        </div>
        
        <button 
          onClick={fetchQueueData} 
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 0.85rem',
            backgroundColor: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '6px',
            color: '#d1d5db',
            fontSize: '0.85rem',
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh Queue
        </button>
      </div>

      {/* Metrics Row */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
          <div style={styles.metricCard}>
            <div style={styles.metricLabel}>OPEN ALERTS QUEUE</div>
            <div style={styles.metricValue}>{stats.new_alerts + stats.pending_human_decision}</div>
            <div style={styles.metricSub}>{stats.new_alerts} unreviewed, {stats.pending_human_decision} pending decision</div>
          </div>
          <div style={styles.metricCard}>
            <div style={styles.metricLabel}>CONFIRMED FRAUD</div>
            <div style={{ ...styles.metricValue, color: '#ef4444' }}>{stats.confirmed_fraud}</div>
            <div style={styles.metricSub}>True positive adjudications</div>
          </div>
          <div style={styles.metricCard}>
            <div style={styles.metricLabel}>FALSE POSITIVE RATE</div>
            <div style={{ ...styles.metricValue, color: '#34d399' }}>{stats.false_positive_rate_pct}%</div>
            <div style={styles.metricSub}>{stats.false_positives} false alarms cleared</div>
          </div>
          <div style={styles.metricCard}>
            <div style={styles.metricLabel}>AVERAGE QUEUE RISK</div>
            <div style={{ ...styles.metricValue, color: '#fbbf24' }}>{stats.average_risk_score} / 100</div>
            <div style={styles.metricSub}>Calculated composite severity</div>
          </div>
        </div>
      )}

      {/* Filters & Search Toolbar */}
      <div style={styles.filterToolbar}>
        {/* Status Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {[
            { id: '', label: 'All Cases' },
            { id: 'NEW', label: 'New Alerts' },
            { id: 'AI_REVIEWED', label: 'AI Reviewed' },
            { id: 'PENDING_HUMAN_DECISION', label: 'Pending Human Decision' },
            { id: 'CONFIRMED_FRAUD', label: 'Confirmed Fraud' },
            { id: 'FALSE_POSITIVE', label: 'False Positives' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setStatusFilter(tab.id); setPage(1); }}
              style={{
                padding: '0.4rem 0.8rem',
                borderRadius: '6px',
                fontSize: '0.8rem',
                fontWeight: '600',
                border: '1px solid',
                borderColor: statusFilter === tab.id ? '#10b981' : '#374151',
                backgroundColor: statusFilter === tab.id ? 'rgba(16, 185, 129, 0.15)' : '#111827',
                color: statusFilter === tab.id ? '#10b981' : '#9ca3af',
                cursor: 'pointer'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="#9ca3af" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input 
              type="text"
              placeholder="Search case #, merchant, customer..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={styles.searchInput}
            />
          </div>
          <button type="submit" style={styles.searchBtn}>Search</button>
        </form>
      </div>

      {/* Cases Queue Table */}
      <div style={styles.tableCard}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
            <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 0.75rem auto', color: '#10b981' }} />
            Loading investigation cases...
          </div>
        ) : cases.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
            <CheckCircle2 size={32} color="#10b981" style={{ margin: '0 auto 0.75rem auto' }} />
            <h3 style={{ color: '#f3f4f6', margin: '0 0 0.5rem 0' }}>Queue Clean</h3>
            <p style={{ margin: 0, fontSize: '0.85rem' }}>No active cases match current queue filters.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={styles.tableHeadRow}>
                <th style={styles.th}>CASE ID</th>
                <th style={styles.th}>RISK SEVERITY</th>
                <th style={styles.th}>CUSTOMER</th>
                <th style={styles.th}>MERCHANT & CATEGORY</th>
                <th style={styles.th}>AMOUNT</th>
                <th style={styles.th}>TRIGGERED SIGNALS</th>
                <th style={styles.th}>STATUS</th>
                <th style={styles.th}>AI RECOMMENDATION</th>
                <th style={{ ...styles.th, textAlign: 'right' }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr 
                  key={c.id} 
                  style={styles.tableRow}
                  onClick={() => navigate(`/cases/${c.id}`)}
                >
                  <td style={{ ...styles.td, fontFamily: 'monospace', fontWeight: '700', color: '#f3f4f6' }}>
                    {c.case_number}
                  </td>
                  <td style={styles.td}>
                    {getRiskBadge(c.risk_level, c.risk_score)}
                  </td>
                  <td style={styles.td}>
                    <div style={{ fontWeight: '600', color: '#f3f4f6' }}>{c.customer_name || 'Customer'}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>UID: #{c.user_id}</div>
                  </td>
                  <td style={styles.td}>
                    <div style={{ fontWeight: '500', color: '#e5e7eb' }}>{c.merchant}</div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{c.category}</div>
                  </td>
                  <td style={{ ...styles.td, fontWeight: '700', color: '#f3f4f6' }}>
                    {formatCurrency(c.amount, currency)}
                  </td>
                  <td style={styles.td}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem', maxWidth: '220px' }}>
                      {(c.risk_factors || []).slice(0, 2).map((rf, idx) => (
                        <span key={idx} style={styles.signalPill}>
                          +{Math.round(rf.points)} {rf.factor.split(' ')[0]}
                        </span>
                      ))}
                      {(c.risk_factors || []).length > 2 && (
                        <span style={styles.signalMore}>+{c.risk_factors.length - 2} more</span>
                      )}
                    </div>
                  </td>
                  <td style={styles.td}>
                    {getStatusBadge(c.status)}
                  </td>
                  <td style={styles.td}>
                    {c.ai_recommendation ? (
                      <span style={{ 
                        fontSize: '0.75rem', 
                        fontWeight: '700',
                        color: c.ai_recommendation === 'CONFIRM_FRAUD' ? '#ef4444' : (c.ai_recommendation === 'FALSE_POSITIVE' ? '#34d399' : '#fbbf24')
                      }}>
                        {c.ai_recommendation}
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: '#6b7280', fontStyle: 'italic' }}>Pending AI Run</span>
                    )}
                  </td>
                  <td style={{ ...styles.td, textAlign: 'right' }}>
                    <button 
                      style={styles.investigateBtn}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/cases/${c.id}`);
                      }}
                    >
                      Investigate <ArrowRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const styles = {
  metricCard: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    padding: '1rem 1.25rem',
  },
  metricLabel: {
    fontSize: '0.7rem',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.05em',
  },
  metricValue: {
    fontSize: '1.6rem',
    fontWeight: '800',
    color: '#f3f4f6',
    margin: '0.25rem 0',
  },
  metricSub: {
    fontSize: '0.75rem',
    color: '#6b7280',
  },
  filterToolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  searchInput: {
    backgroundColor: '#111827',
    border: '1px solid #374151',
    borderRadius: '6px',
    padding: '0.45rem 0.75rem 0.45rem 2rem',
    fontSize: '0.85rem',
    color: '#f3f4f6',
    outline: 'none',
    width: '260px',
  },
  searchBtn: {
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '6px',
    padding: '0.45rem 0.85rem',
    color: '#d1d5db',
    fontSize: '0.85rem',
    fontWeight: '600',
    cursor: 'pointer',
  },
  tableCard: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    overflow: 'hidden',
  },
  tableHeadRow: {
    backgroundColor: '#0f172a',
    borderBottom: '1px solid #1e293b',
  },
  th: {
    padding: '0.75rem 1rem',
    fontWeight: '700',
    fontSize: '0.7rem',
    color: '#94a3b8',
    letterSpacing: '0.05em',
  },
  tableRow: {
    borderBottom: '1px solid #1f2937',
    cursor: 'pointer',
    transition: 'background-color 0.15s ease',
  },
  td: {
    padding: '0.85rem 1rem',
    verticalAlign: 'middle',
  },
  signalPill: {
    backgroundColor: '#1e293b',
    color: '#cbd5e1',
    padding: '0.15rem 0.35rem',
    borderRadius: '3px',
    fontSize: '0.7rem',
    fontWeight: '600',
    border: '1px solid #334155',
  },
  signalMore: {
    fontSize: '0.7rem',
    color: '#64748b',
    alignSelf: 'center',
  },
  investigateBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    color: '#10b981',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    borderRadius: '4px',
    padding: '0.35rem 0.7rem',
    fontSize: '0.75rem',
    fontWeight: '600',
    cursor: 'pointer',
  }
};
