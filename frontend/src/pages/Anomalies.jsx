import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  ShieldAlert, RefreshCw, Cpu, CheckCircle, 
  AlertTriangle, ArrowRight, ShieldCheck, ShieldAlert as ShieldAlertIcon
} from 'lucide-react';

export default function Anomalies({ currency = 'INR' }) {

  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState(null);

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const data = await analyticsAPI.getAnomalies();
      setAnomalies(data);
    } catch (err) {
      console.error("Failed to load anomalies:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const handleRetrain = async () => {
    setTraining(true);
    setTrainMessage(null);
    try {
      const response = await analyticsAPI.trainModel();
      setTrainMessage({
        type: 'success',
        text: `Model retrained successfully. Contamination rate: ${(response.contamination_rate * 100).toFixed(1)}%. All transaction histories re-scored.`
      });
      fetchAnomalies(); // Refresh scored list
    } catch (err) {
      setTrainMessage({
        type: 'error',
        text: err.response?.data?.detail || "Model training failed. Ensure database has at least 20 transactions."
      });
    } finally {
      setTraining(false);
    }
  };

  const getRiskLevel = (score) => {
    if (score >= 0.8) return { label: 'CRITICAL', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' };
    if (score >= 0.5) return { label: 'WARNING', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' };
    return { label: 'LOW RISK', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' };
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Cpu color="#10b981" /> Threat Intelligence
          </h1>
          <p style={{ color: '#9ca3af', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Real-time anomaly detection scanning and Isolation Forest configuration controls.
          </p>
        </div>
      </div>

      {/* Retrain Control Panel Card */}
      <div className="card" style={styles.controlCard}>
        <div style={styles.controlText}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: '#f3f4f6' }}>
            Isolation Forest Engine Calibration
          </h3>
          <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginTop: '0.25rem', maxWidth: '600px' }}>
            Flagging criteria uses unsupervised learning to identify out-of-distribution spending profiles based on amount, frequency, hour of transaction, and category risk factors.
          </p>
        </div>
        <div>
          <button 
            className="btn btn-primary" 
            onClick={handleRetrain} 
            disabled={training}
            style={{ minWidth: '180px' }}
          >
            {training ? (
              <>
                <RefreshCw className="animate-spin" size={16} /> Tuning Boundaries...
              </>
            ) : (
              <>
                <Cpu size={16} /> Calibrate ML Engine
              </>
            )}
          </button>
        </div>
      </div>

      {/* Calibration Messages */}
      {trainMessage && (
        <div 
          style={{ 
            ...styles.messageContainer, 
            backgroundColor: trainMessage.type === 'success' ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
            borderColor: trainMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
          }}
        >
          {trainMessage.type === 'success' ? (
            <CheckCircle size={20} color="#10b981" />
          ) : (
            <AlertTriangle size={20} color="#ef4444" />
          )}
          <span style={{ fontSize: '0.9rem', color: '#f3f4f6' }}>{trainMessage.text}</span>
        </div>
      )}

      {/* Anomalies List */}
      <div className="card">
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600', color: '#f3f4f6' }}>
            Flagged Transactions ({anomalies.length})
          </h3>
          <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginTop: '0.1rem' }}>
            Review flagged records and verify integrity with customers.
          </p>
        </div>

        {loading ? (
          <div style={styles.loader}>
            <RefreshCw className="animate-spin" size={24} color="#10b981" />
            <span style={{ marginLeft: '0.75rem', color: '#9ca3af' }}>Re-evaluating decisions...</span>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>DATE</th>
                  <th>MERCHANT</th>
                  <th>CATEGORY</th>
                  <th>ANOMALY THRESHOLD</th>
                  <th>RISK LAYER</th>
                  <th>AMOUNT</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.map((tx) => {
                  const risk = getRiskLevel(tx.fraud_score);
                  return (
                    <tr key={tx.id}>
                      <td>
                        {new Date(tx.transaction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td style={{ fontWeight: '500' }}>{tx.merchant}</td>
                      <td>
                        <span className="badge" style={{ backgroundColor: 'rgba(36, 47, 71, 0.4)', color: '#f3f4f6' }}>
                          {tx.category}
                        </span>
                      </td>
                      <td>
                        <div style={styles.progressBarWrapper}>
                          <div style={{ ...styles.progressBar, width: `${tx.fraud_score * 100}%`, backgroundColor: risk.color }}></div>
                          <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', fontWeight: '600', color: '#f3f4f6' }}>
                            {(tx.fraud_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="badge" style={{ backgroundColor: risk.bg, color: risk.color }}>
                          {risk.label}
                        </span>
                      </td>
                      <td style={{ fontWeight: '600', color: '#ef4444' }}>
                        -{formatCurrency(tx.amount, currency)}
                      </td>
                    </tr>
                  );
                })}
                {anomalies.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', color: '#9ca3af', padding: '3.5rem' }}>
                      <div style={styles.safeContainer}>
                        <ShieldCheck size={36} color="#10b981" />
                        <h4 style={{ color: '#f3f4f6', marginTop: '0.75rem' }}>No Threat Profiles Detected</h4>
                        <p style={{ color: '#6b7280', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                          All transactions fall within standard boundaries of operations.
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  controlCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '2rem',
    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05), rgba(18, 24, 38, 0.7))',
  },
  controlText: {
    display: 'flex',
    flexDirection: 'column',
  },
  messageContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '1rem',
    borderRadius: '12px',
    border: '1px solid',
  },
  loader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '3rem',
  },
  progressBarWrapper: {
    display: 'flex',
    alignItems: 'center',
    width: '180px',
  },
  progressBar: {
    height: '6px',
    borderRadius: '3px',
    transition: 'width 0.4s ease-out',
  },
  safeContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
};
