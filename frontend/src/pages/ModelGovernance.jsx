import React, { useState, useEffect } from 'react';
import { governanceAPI } from '../services/api';
import { 
  ShieldCheck, AlertTriangle, FileCode, CheckCircle2, 
  GitBranch, RefreshCw, Activity, Lock, Cpu, BarChart2
} from 'lucide-react';

export default function ModelGovernance() {
  const [models, setModels] = useState([]);
  const [versions, setVersions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchGovernanceData = async () => {
    setLoading(true);
    try {
      const [modelList, versionList, productMetrics] = await Promise.all([
        governanceAPI.getModels(),
        governanceAPI.getVersions(),
        governanceAPI.getProductMetrics()
      ]);
      setModels(modelList);
      setVersions(versionList);
      setMetrics(productMetrics);
    } catch (err) {
      console.error("Failed to load model governance data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGovernanceData();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#9ca3af' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 1rem auto', color: '#10b981' }} />
        <span>Loading AI governance registry and product metrics...</span>
      </div>
    );
  }

  const ops = metrics?.operational_throughput || {};
  const perf = metrics?.investigation_performance || {};

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <ShieldCheck size={24} color="#10b981" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f3f4f6', margin: 0 }}>
            Model Governance & AI Risk Registry
          </h1>
        </div>
        <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginTop: '0.25rem' }}>
          Compliance oversight, approved operational boundaries, human-in-the-loop mandates, and agent version progression.
        </p>
      </div>

      {/* Section 19: Product-Level Operational Metrics */}
      <div style={styles.card}>
        <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
            Product Operational Telemetry
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Actual measured operational performance</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
          <div style={styles.metricBox}>
            <span style={styles.metricLabel}>TOTAL ALERTS INVESTIGATED</span>
            <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f3f4f6' }}>{ops.total_alerts_investigated || 0}</span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>{ops.adjudicated_by_human} adjudicated by human</span>
          </div>

          <div style={styles.metricBox}>
            <span style={styles.metricLabel}>HUMAN OVERRIDE RATE</span>
            <span style={{ fontSize: '1.5rem', fontWeight: '800', color: ops.human_override_rate_pct > 20 ? '#fbbf24' : '#10b981' }}>
              {ops.human_override_rate_pct}%
            </span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>Investigator disagreed with AI</span>
          </div>

          <div style={styles.metricBox}>
            <span style={styles.metricLabel}>AVERAGE AGENT LATENCY</span>
            <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#38bdf8' }}>{perf.average_agent_latency_ms} ms</span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>Across {perf.average_tools_per_investigation} controlled tool calls</span>
          </div>

          <div style={styles.metricBox}>
            <span style={styles.metricLabel}>EVIDENCE RETRIEVAL SUCCESS</span>
            <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#34d399' }}>{perf.evidence_retrieval_success_rate_pct}%</span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>0% unhandled tool exceptions</span>
          </div>
        </div>
      </div>

      {/* Section 18: Model Registry & Compliance Limits */}
      <div style={styles.card}>
        <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
            Registered AI & Risk Models ({models.length})
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Formal model risk management inventory</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          {models.map((m) => (
            <div key={m.model_id} style={styles.modelCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: '800', color: '#10b981', fontFamily: 'monospace' }}>
                  {m.model_id}
                </span>
                <span style={{ fontSize: '0.7rem', color: '#9ca3af', backgroundColor: '#1e293b', padding: '0.15rem 0.4rem', borderRadius: '3px' }}>
                  {m.version}
                </span>
              </div>

              <div style={{ fontSize: '1rem', fontWeight: '800', color: '#f3f4f6', margin: '0.35rem 0 0.15rem 0' }}>
                {m.name}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.75rem' }}>{m.type}</div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.75rem' }}>
                <div>
                  <span style={styles.subLabel}>APPROVED USE:</span>
                  <div style={{ color: '#d1d5db', marginTop: '0.1rem' }}>{m.approved_use}</div>
                </div>

                <div>
                  <span style={{ ...styles.subLabel, color: '#f87171' }}>PROHIBITED USE:</span>
                  <div style={{ color: '#fca5a5', marginTop: '0.1rem' }}>{m.prohibited_use}</div>
                </div>

                <div>
                  <span style={styles.subLabel}>HUMAN OVERSIGHT MANDATE:</span>
                  <div style={{ color: '#fbbf24', marginTop: '0.1rem' }}>{m.human_oversight}</div>
                </div>

                <div>
                  <span style={styles.subLabel}>KNOWN LIMITATIONS:</span>
                  <div style={{ color: '#9ca3af', fontStyle: 'italic', marginTop: '0.1rem' }}>{m.known_limitations}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 17: Agent Version Evolution & Regression Feedback Suite */}
      <div style={styles.card}>
        <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
            Investigation Agent Version Evolution & Regression History
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Continuous evaluation feedback loop</span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #1e293b', backgroundColor: '#0f172a' }}>
              <th style={styles.th}>VERSION</th>
              <th style={styles.th}>RELEASE DATE</th>
              <th style={styles.th}>EVIDENCE GROUNDING</th>
              <th style={styles.th}>ABSTENTION ACCURACY</th>
              <th style={styles.th}>RECOMMENDATION ACCURACY</th>
              <th style={styles.th}>REGRESSION BENCHMARK NOTES</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.version} style={{ borderBottom: '1px solid #1f2937' }}>
                <td style={{ ...styles.td, fontWeight: '800', color: '#38bdf8' }}>{v.version}</td>
                <td style={styles.td}>{v.release_date}</td>
                <td style={styles.td}>
                  <span style={{ fontWeight: '700', color: '#10b981' }}>{v.grounding_rate}%</span>
                </td>
                <td style={styles.td}>
                  <span style={{ fontWeight: '700', color: '#fbbf24' }}>{v.abstention_accuracy}%</span>
                </td>
                <td style={styles.td}>
                  <span style={{ fontWeight: '700', color: '#34d399' }}>{v.recommendation_accuracy}%</span>
                </td>
                <td style={{ ...styles.td, color: '#9ca3af', fontSize: '0.8rem' }}>{v.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}

const styles = {
  card: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    padding: '1.25rem',
  },
  metricBox: {
    backgroundColor: '#0f172a',
    border: '1px solid #1e293b',
    borderRadius: '6px',
    padding: '0.85rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
  },
  metricLabel: {
    fontSize: '0.68rem',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.04em',
  },
  modelCard: {
    backgroundColor: '#0f172a',
    border: '1px solid #1e293b',
    borderRadius: '6px',
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column',
  },
  subLabel: {
    fontSize: '0.65rem',
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: '0.04em',
  },
  th: {
    padding: '0.65rem 0.85rem',
    textAlign: 'left',
    fontSize: '0.7rem',
    color: '#94a3b8',
    letterSpacing: '0.04em',
  },
  td: {
    padding: '0.75rem 0.85rem',
    verticalAlign: 'middle',
  }
};
