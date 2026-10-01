import React, { useState, useEffect } from 'react';
import { policiesAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  Sliders, ShieldCheck, AlertTriangle, FileText, CheckCircle2, 
  RefreshCw, TrendingUp, Users, Clock, Play
} from 'lucide-react';

export default function PolicySimulation({ currency = 'INR' }) {
  const [policies, setPolicies] = useState([]);
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  // Simulation parameters
  const [amountThreshold, setAmountThreshold] = useState(3000);
  const [incomeRatio, setIncomeRatio] = useState(0.50);
  const [flagUnverified, setFlagUnverified] = useState(true);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [pols, simResult] = await Promise.all([
        policiesAPI.getAll(),
        policiesAPI.simulate({
          amount_threshold: amountThreshold,
          income_ratio_threshold: incomeRatio,
          flag_unverified_merchants: flagUnverified
        })
      ]);
      setPolicies(pols);
      setSimulation(simResult);
    } catch (err) {
      console.error("Failed to load policy simulation:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleSimulate = async (e) => {
    if (e) e.preventDefault();
    setSimulating(true);
    try {
      const result = await policiesAPI.simulate({
        amount_threshold: parseFloat(amountThreshold),
        income_ratio_threshold: parseFloat(incomeRatio),
        flag_unverified_merchants: flagUnverified
      });
      setSimulation(result);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  const effects = simulation?.measured_effects || {};

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <Sliders size={24} color="#38bdf8" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f3f4f6', margin: 0 }}>
            Policy Simulation & Threshold Tuning
          </h1>
        </div>
        <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginTop: '0.25rem' }}>
          Evaluate candidate risk threshold adjustments against the dataset. Understand the business trade-off between fraud capture and investigator operational workload.
        </p>
      </div>

      {/* Main 2-Column Split: Left = Simulation Sliders & Trade-off Result; Right = Policy Rules Browser */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.25rem' }}>
        
        {/* Left Column: Interactive Simulation Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          <div style={styles.card}>
            <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
                Candidate Policy Parameters
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Adjust thresholds to simulate operational impact</span>
            </div>

            <form onSubmit={handleSimulate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              
              {/* Amount Threshold Slider */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <label style={styles.sliderLabel}>HIGH-VALUE THRESHOLD:</label>
                  <span style={{ fontWeight: '800', color: '#38bdf8' }}>${amountThreshold.toLocaleString()}</span>
                </div>
                <input 
                  type="range"
                  min="500"
                  max="8000"
                  step="250"
                  value={amountThreshold}
                  onChange={(e) => setAmountThreshold(Number(e.target.value))}
                  style={{ width: '100%', cursor: 'pointer' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#6b7280' }}>
                  <span>$500 (Aggressive Alerts)</span>
                  <span>$8,000 (Conservative)</span>
                </div>
              </div>

              {/* Income Ratio Threshold */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <label style={styles.sliderLabel}>INCOME RATIO THRESHOLD (INC-04):</label>
                  <span style={{ fontWeight: '800', color: '#fbbf24' }}>{Math.round(incomeRatio * 100)}% of monthly baseline</span>
                </div>
                <input 
                  type="range"
                  min="0.2"
                  max="0.9"
                  step="0.05"
                  value={incomeRatio}
                  onChange={(e) => setIncomeRatio(Number(e.target.value))}
                  style={{ width: '100%', cursor: 'pointer' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#6b7280' }}>
                  <span>20% (Strict)</span>
                  <span>90% (Outliers only)</span>
                </div>
              </div>

              {/* Unverified Merchant Toggle */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: '#0f172a', borderRadius: '6px', border: '1px solid #1e293b' }}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: '700', color: '#f3f4f6' }}>Mandate Verification (MV-01)</div>
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Require manual alert on unverified merchant entities</div>
                </div>
                <input 
                  type="checkbox"
                  checked={flagUnverified}
                  onChange={(e) => setFlagUnverified(e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer', accentColor: '#10b981' }}
                />
              </div>

              <button 
                type="submit"
                disabled={simulating}
                style={styles.simBtn}
              >
                {simulating ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                {simulating ? "Simulating on Dataset..." : "Run Policy Simulation"}
              </button>
            </form>
          </div>

          {/* Measured Trade-off Effects */}
          {simulation && (
            <div style={styles.card}>
              <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
                  Measured Business Trade-Offs
                </h3>
                <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Empirical results evaluated on {simulation.simulation_parameters?.dataset_sample_size} synthetic transactions</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={styles.tradeoffBox}>
                  <span style={styles.tradeoffLabel}>FRAUD CAPTURE RATE</span>
                  <span style={{ fontSize: '1.6rem', fontWeight: '800', color: '#10b981' }}>{effects.fraud_catch_rate_pct}%</span>
                  <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>{effects.fraud_cases_captured} / {effects.total_ground_truth_fraud} fraud cases captured</span>
                </div>

                <div style={styles.tradeoffBox}>
                  <span style={styles.tradeoffLabel}>QUEUE WORKLOAD</span>
                  <span style={{ fontSize: '1.6rem', fontWeight: '800', color: '#fbbf24' }}>{effects.estimated_investigator_workload_hours} hrs</span>
                  <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>Estimated ~{effects.recommended_headcount} full-time investigators</span>
                </div>

                <div style={styles.tradeoffBox}>
                  <span style={styles.tradeoffLabel}>ALERTS GENERATED</span>
                  <span style={{ fontSize: '1.6rem', fontWeight: '800', color: '#38bdf8' }}>{effects.alerts_generated}</span>
                  <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>{effects.alert_rate_pct}% of total transaction volume</span>
                </div>

                <div style={styles.tradeoffBox}>
                  <span style={styles.tradeoffLabel}>FALSE POSITIVES</span>
                  <span style={{ fontSize: '1.6rem', fontWeight: '800', color: '#f87171' }}>{effects.false_positive_rate_pct}%</span>
                  <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>{effects.false_positives_generated} unnecessary manual reviews</span>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: '#d1d5db', backgroundColor: '#0f172a', padding: '0.85rem', borderRadius: '6px', border: '1px solid #1e293b', lineHeight: '1.4' }}>
                <strong style={{ color: '#10b981' }}>Product Trade-Off Analysis: </strong> 
                {simulation.trade_off_analysis}
              </div>
            </div>
          )}

        </div>

        {/* Right Column: Institutional Policy Rules Knowledge Base */}
        <div style={styles.card}>
          <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
              Institutional Fraud Policies
            </h3>
            <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Grounded Rule Specifications ({policies.length})</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '680px', overflowY: 'auto' }}>
            {policies.map((p) => (
              <div key={p.policy_id} style={styles.policyCard}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: '800', fontSize: '0.85rem', color: '#38bdf8', fontFamily: 'monospace' }}>
                    {p.policy_id}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#fbbf24', fontWeight: '700', backgroundColor: '#1e293b', padding: '0.1rem 0.4rem', borderRadius: '3px' }}>
                    +{Math.round(p.weight)} pts
                  </span>
                </div>
                <div style={{ fontWeight: '700', color: '#f3f4f6', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                  {p.title}
                </div>
                <p style={{ fontSize: '0.75rem', color: '#9ca3af', margin: '0.35rem 0' }}>
                  {p.rule_summary}
                </p>
                <div style={{ fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic' }}>
                  "{p.text}"
                </div>
              </div>
            ))}
          </div>
        </div>

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
  sliderLabel: {
    fontSize: '0.75rem',
    fontWeight: '700',
    color: '#9ca3af',
  },
  simBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.45rem',
    backgroundColor: '#10b981',
    color: '#000000',
    border: 'none',
    borderRadius: '6px',
    padding: '0.65rem 1rem',
    fontSize: '0.85rem',
    fontWeight: '700',
    cursor: 'pointer',
  },
  tradeoffBox: {
    backgroundColor: '#0f172a',
    border: '1px solid #1e293b',
    borderRadius: '6px',
    padding: '0.85rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
  },
  tradeoffLabel: {
    fontSize: '0.68rem',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.04em',
  },
  policyCard: {
    backgroundColor: '#0f172a',
    border: '1px solid #1e293b',
    borderRadius: '6px',
    padding: '0.85rem',
  }
};
