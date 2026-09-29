import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { casesAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  ShieldAlert, ShieldCheck, AlertTriangle, ArrowLeft, RefreshCw, 
  Cpu, CheckCircle2, Clock, Users, Activity, FileText, Smartphone,
  MapPin, CreditCard, ExternalLink, Sparkles, UserCheck, HelpCircle,
  TrendingDown, Check, XCircle, AlertOctagon, Send
} from 'lucide-react';

export default function CaseInvestigation({ currency = 'INR' }) {
  const { id } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [deciding, setDeciding] = useState(false);
  const [notes, setNotes] = useState('');
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);

  const fetchCase = async () => {
    try {
      const data = await casesAPI.getCaseDetail(id);
      setCaseData(data);
      if (data.human_notes) {
        setNotes(data.human_notes);
      }
    } catch (err) {
      console.error("Failed to load case details:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCase();
  }, [id]);

  const handleRunInvestigation = async () => {
    setInvestigating(true);
    setStatusMessage(null);
    try {
      await casesAPI.triggerInvestigation(id);
      setStatusMessage({ type: 'success', text: 'AI Autonomous Investigation completed with live policy & memory grounding.' });
      await fetchCase();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'AI Investigation failed to execute.' });
    } finally {
      setInvestigating(false);
    }
  };

  const handleDecisionSubmit = async (decision) => {
    setDeciding(true);
    setStatusMessage(null);
    try {
      const updated = await casesAPI.submitDecision(id, decision, notes);
      setCaseData(updated);
      setSelectedDecision(null);
      setStatusMessage({ type: 'success', text: `Binding decision [${decision}] recorded permanently in case audit trail.` });
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to submit human decision.' });
    } finally {
      setDeciding(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center', color: '#9ca3af' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 1rem auto', color: '#10b981' }} />
        <span>Loading investigation workstation for Case #{id}...</span>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: '#ef4444' }}>
        <h3>Case Not Found</h3>
        <Link to="/cases" style={{ color: '#10b981', textDecoration: 'underline' }}>Return to Cases Queue</Link>
      </div>
    );
  }

  const tx = caseData.transaction || {};
  const latestRun = caseData.latest_investigation;
  const isResolved = ['CONFIRMED_FRAUD', 'FALSE_POSITIVE'].includes(caseData.status);

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Top Navigation & Status Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button 
            onClick={() => navigate('/cases')}
            style={styles.backBtn}
            title="Return to Queue"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h1 style={{ fontSize: '1.4rem', fontWeight: '800', color: '#f3f4f6', margin: 0, fontFamily: 'monospace' }}>
                {caseData.case_number}
              </h1>
              <span style={{
                padding: '0.25rem 0.65rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: '800',
                backgroundColor: caseData.risk_score >= 75 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                color: caseData.risk_score >= 75 ? '#ef4444' : '#f59e0b',
                border: `1px solid ${caseData.risk_score >= 75 ? '#ef4444' : '#f59e0b'}`
              }}>
                {caseData.risk_level} RISK ({Math.round(caseData.risk_score)} / 100)
              </span>
              <span style={styles.statusPill}>
                STATUS: {caseData.status}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.2rem' }}>
              Created: {new Date(caseData.created_at).toLocaleString()} • System: FinSight Risk Operations Workstation
            </div>
          </div>
        </div>

        {/* Top Right Action: Run or Re-run AI Investigation */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleRunInvestigation}
            disabled={investigating}
            style={{
              ...styles.primaryActionBtn,
              backgroundColor: investigating ? '#374151' : 'rgba(16, 185, 129, 0.15)',
              borderColor: '#10b981',
              color: '#10b981'
            }}
          >
            {investigating ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                Executing Agent Tools...
              </>
            ) : (
              <>
                <Sparkles size={14} />
                {latestRun ? "Re-run AI Investigation" : "Run AI Investigation"}
              </>
            )}
          </button>
        </div>
      </div>

      {statusMessage && (
        <div style={{
          padding: '0.75rem 1rem',
          borderRadius: '6px',
          fontSize: '0.85rem',
          backgroundColor: statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${statusMessage.type === 'success' ? '#10b981' : '#ef4444'}`,
          color: statusMessage.type === 'success' ? '#34d399' : '#f87171',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          {statusMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          {statusMessage.text}
        </div>
      )}

      {/* Primary 3-Column Entity Header (CUSTOMER, TRANSACTION, MERCHANT) */}
      <div style={styles.entityGrid}>
        {/* Customer Box */}
        <div style={styles.entityCard}>
          <div style={styles.entityCardTitle}><Users size={14} color="#10b981" /> CUSTOMER PROFILE</div>
          <div style={styles.entityMainText}>{caseData.customer_name}</div>
          <div style={styles.entityMeta}>User ID: #{caseData.user_id}</div>
          <div style={styles.entitySub}>Primary Locale: {tx.location || 'San Francisco, US'}</div>
        </div>

        {/* Transaction Box */}
        <div style={styles.entityCard}>
          <div style={styles.entityCardTitle}><CreditCard size={14} color="#3b82f6" /> TRANSACTION DETAILS</div>
          <div style={{ ...styles.entityMainText, color: '#f3f4f6' }}>{formatCurrency(tx.amount || 0, currency)}</div>
          <div style={styles.entityMeta}>Timestamp: {tx.transaction_date ? new Date(tx.transaction_date).toLocaleString() : 'N/A'}</div>
          <div style={styles.entitySub}>Card: •••• {tx.card_last4 || '4821'} ({tx.category})</div>
        </div>

        {/* Merchant & Hardware Box */}
        <div style={styles.entityCard}>
          <div style={styles.entityCardTitle}><Smartphone size={14} color="#f59e0b" /> MERCHANT & ACCESS VECTOR</div>
          <div style={styles.entityMainText}>{tx.merchant}</div>
          <div style={styles.entityMeta}>
            Entity Status: {tx.is_merchant_verified ? (
              <span style={{ color: '#34d399', fontWeight: 'bold' }}>✓ Verified LEI</span>
            ) : (
              <span style={{ color: '#ef4444', fontWeight: 'bold' }}>⚠ Unverified Entity</span>
            )} (MCC {tx.mcc_code})
          </div>
          <div style={styles.entitySub}>Device: {tx.device_id || 'DEV-UNKNOWN'} • IP: {tx.ip_address || '198.51.100.1'}</div>
        </div>
      </div>

      {/* Main 2-Column Split: Left = Evidence & Signals; Right = AI Investigation & Human Decision */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        
        {/* Left Column: Risk Signals + Counterfactual Sensitivity */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Section 5: Structured Risk Factors */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={16} color="#ef4444" />
                <h3 style={styles.sectionTitle}>Calculated Risk Factors</h3>
              </div>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Additive Exact Allocation</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {(caseData.risk_factors || []).length === 0 ? (
                <div style={{ color: '#6b7280', fontSize: '0.8rem' }}>No individual risk factors exceeded thresholds.</div>
              ) : (
                caseData.risk_factors.map((rf, idx) => (
                  <div key={idx} style={styles.factorRow}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <span style={{ fontWeight: '700', fontSize: '0.85rem', color: '#f3f4f6' }}>
                        {rf.factor}
                      </span>
                      <span style={{ 
                        fontWeight: '800', 
                        fontSize: '0.85rem', 
                        color: rf.points >= 30 ? '#ef4444' : (rf.points >= 15 ? '#fbbf24' : '#60a5fa'),
                        backgroundColor: '#1f2937',
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px'
                      }}>
                        +{Math.round(rf.points)} pts
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>
                      {rf.description}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Section 11: Feature Sensitivity / Counterfactual Scenarios */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <TrendingDown size={16} color="#34d399" />
                <h3 style={styles.sectionTitle}>Feature Sensitivity Scenarios</h3>
              </div>
              <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>Transparent Deterministic Delta</span>
            </div>

            <p style={{ fontSize: '0.75rem', color: '#9ca3af', margin: '0 0 0.75rem 0' }}>
              Measured change in composite risk score if individual risk signals were mitigated:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {(caseData.counterfactuals || []).length === 0 ? (
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>No sensitivity deltas computed for current baseline.</div>
              ) : (
                caseData.counterfactuals.map((cf, idx) => (
                  <div key={idx} style={styles.cfRow}>
                    <div style={{ fontSize: '0.8rem', color: '#d1d5db', flex: 1 }}>{cf.scenario}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#34d399' }}>{cf.delta} pts</span>
                      <span style={styles.cfEstPill}>Est: {Math.round(cf.estimated_risk_score)}/100</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Network Linkage Snapshot Preview */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Users size={16} color="#818cf8" />
                <h3 style={styles.sectionTitle}>Connected Entity Signals</h3>
              </div>
              <Link to="/network" style={{ fontSize: '0.75rem', color: '#818cf8', textDecoration: 'none' }}>
                Full Graph →
              </Link>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', fontSize: '0.8rem' }}>
              <div style={styles.subDetailBox}>
                <span style={{ color: '#6b7280' }}>Device Fingerprint</span>
                <span style={{ fontWeight: '600', color: '#f3f4f6', fontFamily: 'monospace' }}>{tx.device_id || 'DEV-APPLE-9921'}</span>
              </div>
              <div style={styles.subDetailBox}>
                <span style={{ color: '#6b7280' }}>IP Address Location</span>
                <span style={{ fontWeight: '600', color: '#f3f4f6' }}>{tx.ip_address}</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: AI Investigation + Human Decision Workstation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Section 6 & 7: Evidence-First AI Investigation Box */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Cpu size={16} color="#10b981" />
                <h3 style={styles.sectionTitle}>Autonomous AI Investigation</h3>
              </div>
              {latestRun && (
                <span style={{ fontSize: '0.7rem', color: '#10b981', fontFamily: 'monospace' }}>
                  Latency: {Math.round(latestRun.total_latency_ms)}ms • {latestRun.model_version}
                </span>
              )}
            </div>

            {!latestRun ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af', border: '1px dashed #374151', borderRadius: '6px' }}>
                <Sparkles size={24} color="#10b981" style={{ margin: '0 auto 0.5rem auto' }} />
                <div style={{ fontWeight: '600', color: '#f3f4f6', marginBottom: '0.25rem' }}>Autonomous Agent Ready</div>
                <p style={{ fontSize: '0.8rem', color: '#9ca3af', maxWidth: '350px', margin: '0 auto 1rem auto' }}>
                  Execute controlled read-only tools across customer history, devices, merchant records, and institutional policies.
                </p>
                <button onClick={handleRunInvestigation} style={styles.primaryActionBtn} disabled={investigating}>
                  Start AI Investigation
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                
                {/* 1. Recommendation Banner */}
                <div style={{
                  padding: '0.85rem',
                  borderRadius: '6px',
                  backgroundColor: latestRun.recommendation === 'CONFIRM_FRAUD' ? 'rgba(239, 68, 68, 0.15)' : (latestRun.recommendation === 'FALSE_POSITIVE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)'),
                  border: `1px solid ${latestRun.recommendation === 'CONFIRM_FRAUD' ? '#ef4444' : (latestRun.recommendation === 'FALSE_POSITIVE' ? '#10b981' : '#f59e0b')}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <span style={{ fontSize: '0.7rem', fontWeight: '700', color: '#9ca3af', display: 'block' }}>PROPOSED NEXT ACTION</span>
                    <span style={{ fontSize: '1.1rem', fontWeight: '800', color: '#f3f4f6' }}>
                      {latestRun.recommendation}
                    </span>
                  </div>
                  {latestRun.abstained && (
                    <span style={{ padding: '0.2rem 0.5rem', backgroundColor: '#374151', color: '#f3f4f6', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700' }}>
                      ABSTAINED: INSUFFICIENT EVIDENCE
                    </span>
                  )}
                </div>

                {/* 2. Reasoning Summary */}
                <div>
                  <span style={styles.miniLabel}>AI REASONING SYNTHESIS</span>
                  <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: '1.45', backgroundColor: '#0f172a', padding: '0.75rem', borderRadius: '6px', border: '1px solid #1e293b' }}>
                    {latestRun.reasoning_summary}
                  </div>
                </div>

                {/* 3. Observed Facts (Evidence) */}
                <div>
                  <span style={styles.miniLabel}>OBSERVED SYSTEM FACTS (CONTROLLED READ-ONLY RETRIEVAL)</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {(latestRun.observed_evidence || []).map((ev, idx) => (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.35rem 0.5rem', backgroundColor: '#1f2937', borderRadius: '4px' }}>
                        <span style={{ color: '#9ca3af', fontWeight: '600' }}>{ev.label}:</span>
                        <span style={{ color: '#f3f4f6', fontWeight: '700' }}>{ev.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 4. Grounded Policy Evidence */}
                <div>
                  <span style={styles.miniLabel}>APPLICABLE FRAUD POLICIES</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {(latestRun.retrieved_policies || []).map((pol, idx) => (
                      <div key={idx} style={{ fontSize: '0.75rem', padding: '0.5rem', backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '700', color: '#60a5fa' }}>
                          <span>[{pol.policy_id}] {pol.title}</span>
                          <span>Relevance: {Math.round(pol.relevance_score * 100)}%</span>
                        </div>
                        <div style={{ color: '#9ca3af', marginTop: '0.2rem' }}>{pol.rule_summary}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 5. Tool Telemetry Trace (Section 15) */}
                <div>
                  <span style={styles.miniLabel}>TOOL EXECUTION TRACE (READ-ONLY AUDIT)</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                    {(latestRun.tool_calls || []).map((tc, idx) => (
                      <span key={idx} style={styles.toolPill}>
                        {tc.tool}() • {tc.latency_ms}ms
                      </span>
                    ))}
                  </div>
                </div>

              </div>
            )}
          </div>

          {/* Section 13: Human-in-the-Loop Decision Station */}
          <div style={styles.sectionCard}>
            <div style={styles.sectionHeader}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <UserCheck size={16} color="#fbbf24" />
                <h3 style={styles.sectionTitle}>Human Decision & Adjudication</h3>
              </div>
              <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>Mandatory Final Oversight</span>
            </div>

            <p style={{ fontSize: '0.75rem', color: '#9ca3af', margin: '0 0 0.75rem 0' }}>
              The AI recommendation does not execute financial actions. Investigators record final binding decisions.
            </p>

            {/* Notes input */}
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginBottom: '0.35rem', fontWeight: '600' }}>
                INVESTIGATOR RATIONALE & NOTES:
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Document your findings, customer verification steps, or escalation justification..."
                style={styles.notesTextarea}
                rows={3}
              />
            </div>

            {/* Decision Buttons Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.65rem' }}>
              <button
                onClick={() => handleDecisionSubmit('CONFIRM_FRAUD')}
                disabled={deciding}
                style={{
                  ...styles.decisionBtn,
                  backgroundColor: caseData.human_decision === 'CONFIRM_FRAUD' ? '#dc2626' : 'rgba(239, 68, 68, 0.1)',
                  borderColor: '#ef4444',
                  color: caseData.human_decision === 'CONFIRM_FRAUD' ? '#ffffff' : '#f87171'
                }}
              >
                <XCircle size={15} />
                CONFIRM FRAUD
              </button>

              <button
                onClick={() => handleDecisionSubmit('FALSE_POSITIVE')}
                disabled={deciding}
                style={{
                  ...styles.decisionBtn,
                  backgroundColor: caseData.human_decision === 'FALSE_POSITIVE' ? '#059669' : 'rgba(16, 185, 129, 0.1)',
                  borderColor: '#10b981',
                  color: caseData.human_decision === 'FALSE_POSITIVE' ? '#ffffff' : '#34d399'
                }}
              >
                <Check size={15} />
                FALSE POSITIVE
              </button>

              <button
                onClick={() => handleDecisionSubmit('ESCALATE')}
                disabled={deciding}
                style={{
                  ...styles.decisionBtn,
                  backgroundColor: caseData.human_decision === 'ESCALATE' ? '#d97706' : 'rgba(245, 158, 11, 0.1)',
                  borderColor: '#f59e0b',
                  color: caseData.human_decision === 'ESCALATE' ? '#ffffff' : '#fbbf24'
                }}
              >
                <AlertOctagon size={15} />
                ESCALATE
              </button>

              <button
                onClick={() => handleDecisionSubmit('REQUEST_MORE_INFO')}
                disabled={deciding}
                style={{
                  ...styles.decisionBtn,
                  backgroundColor: caseData.human_decision === 'REQUEST_MORE_INFO' ? '#2563eb' : 'rgba(59, 130, 246, 0.1)',
                  borderColor: '#3b82f6',
                  color: caseData.human_decision === 'REQUEST_MORE_INFO' ? '#ffffff' : '#93c5fd'
                }}
              >
                <HelpCircle size={15} />
                REQUEST INFO
              </button>
            </div>

            {caseData.human_decision && (
              <div style={{ marginTop: '0.75rem', padding: '0.5rem', backgroundColor: '#1f2937', borderRadius: '4px', fontSize: '0.75rem', color: '#9ca3af' }}>
                Current Adjudication: <strong style={{ color: '#f3f4f6' }}>{caseData.human_decision}</strong> by {caseData.decided_by || 'Investigator'} on {new Date(caseData.decided_at).toLocaleString()}
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Section 14: Dedicated Chronological Audit Timeline */}
      <div style={styles.sectionCard}>
        <div style={styles.sectionHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={16} color="#9ca3af" />
            <h3 style={styles.sectionTitle}>Case Audit Timeline</h3>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Immutable Regulatory Trail</span>
        </div>

        <div style={styles.timelineContainer}>
          {(caseData.audit_logs || []).map((log, idx) => (
            <div key={idx} style={styles.timelineItem}>
              <div style={styles.timelineDot}></div>
              <div style={styles.timelineContent}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: '700', fontSize: '0.8rem', color: '#f3f4f6' }}>
                    {log.action}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#6b7280', fontFamily: 'monospace' }}>
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>
                  {log.details}
                </div>
                <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: '0.15rem' }}>
                  Actor: {log.actor} ({log.actor_id || 'System'})
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}

const styles = {
  backBtn: {
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    color: '#d1d5db',
    borderRadius: '6px',
    padding: '0.4rem 0.6rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
  },
  statusPill: {
    padding: '0.2rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: '700',
    backgroundColor: '#1f2937',
    color: '#d1d5db',
    border: '1px solid #374151',
  },
  primaryActionBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.45rem 0.85rem',
    borderRadius: '6px',
    border: '1px solid #10b981',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    color: '#10b981',
    fontWeight: '700',
    fontSize: '0.8rem',
    cursor: 'pointer',
  },
  entityGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1rem',
  },
  entityCard: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    padding: '1rem',
  },
  entityCardTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    fontSize: '0.7rem',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.04em',
    marginBottom: '0.4rem',
  },
  entityMainText: {
    fontSize: '1.25rem',
    fontWeight: '800',
    color: '#f3f4f6',
  },
  entityMeta: {
    fontSize: '0.8rem',
    color: '#9ca3af',
    marginTop: '0.25rem',
  },
  entitySub: {
    fontSize: '0.75rem',
    color: '#6b7280',
    marginTop: '0.2rem',
  },
  sectionCard: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    padding: '1.15rem',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.85rem',
    borderBottom: '1px solid #1e293b',
    paddingBottom: '0.5rem',
  },
  sectionTitle: {
    fontSize: '0.95rem',
    fontWeight: '700',
    color: '#f3f4f6',
    margin: 0,
  },
  factorRow: {
    padding: '0.65rem 0.75rem',
    backgroundColor: '#0f172a',
    borderRadius: '6px',
    border: '1px solid #1e293b',
  },
  cfRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.45rem 0.65rem',
    backgroundColor: '#0f172a',
    borderRadius: '4px',
    border: '1px solid #1e293b',
  },
  cfEstPill: {
    fontSize: '0.75rem',
    fontWeight: '700',
    color: '#9ca3af',
    backgroundColor: '#1e293b',
    padding: '0.1rem 0.35rem',
    borderRadius: '3px',
  },
  subDetailBox: {
    backgroundColor: '#0f172a',
    padding: '0.5rem',
    borderRadius: '4px',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
  },
  miniLabel: {
    display: 'block',
    fontSize: '0.68rem',
    fontWeight: '700',
    color: '#94a3b8',
    letterSpacing: '0.04em',
    marginBottom: '0.35rem',
  },
  toolPill: {
    backgroundColor: '#0f172a',
    color: '#38bdf8',
    padding: '0.2rem 0.45rem',
    borderRadius: '4px',
    fontSize: '0.68rem',
    fontFamily: 'monospace',
    border: '1px solid #1e293b',
  },
  notesTextarea: {
    width: '100%',
    backgroundColor: '#0f172a',
    border: '1px solid #374151',
    borderRadius: '6px',
    padding: '0.5rem 0.75rem',
    color: '#f3f4f6',
    fontSize: '0.8rem',
    outline: 'none',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
  },
  decisionBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.4rem',
    padding: '0.6rem 0.85rem',
    borderRadius: '6px',
    border: '1px solid',
    fontSize: '0.75rem',
    fontWeight: '800',
    cursor: 'pointer',
    letterSpacing: '0.02em',
  },
  timelineContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
    position: 'relative',
    paddingLeft: '1.25rem',
    borderLeft: '2px solid #1e293b',
    marginLeft: '0.5rem',
  },
  timelineItem: {
    position: 'relative',
  },
  timelineDot: {
    position: 'absolute',
    left: '-1.65rem',
    top: '4px',
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    backgroundColor: '#10b981',
    border: '2px solid #111827',
  },
  timelineContent: {
    backgroundColor: '#0f172a',
    padding: '0.5rem 0.75rem',
    borderRadius: '6px',
    border: '1px solid #1e293b',
  }
};
