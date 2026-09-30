import React, { useState, useEffect } from 'react';
import { networkAPI } from '../services/api';
import { 
  Users, Smartphone, Globe, ShoppingBag, ShieldAlert, AlertTriangle, 
  RefreshCw, CheckCircle2, Search, Link2, Info, ArrowRight, Layers
} from 'lucide-react';

export default function NetworkIntelligence() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeTab, setActiveTab] = useState('clusters'); // 'clusters' | 'entities'

  const fetchData = async () => {
    setLoading(true);
    try {
      const [graph, clusterData] = await Promise.all([
        networkAPI.getGraph(60),
        networkAPI.getClusters()
      ]);
      setGraphData(graph);
      setClusters(clusterData);
      if (graph.nodes && graph.nodes.length > 0) {
        setSelectedNode(graph.nodes[0]);
      }
    } catch (err) {
      console.error("Failed to load network intelligence:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getNodeColor = (type, metadata = {}) => {
    if (type === 'customer') return '#3b82f6'; // Blue
    if (type === 'device') return metadata.shared_across_users > 1 ? '#ef4444' : '#10b981'; // Red if shared, green if normal
    if (type === 'ip_address') return metadata.is_proxy ? '#f59e0b' : '#8b5cf6'; // Yellow/Purple
    if (type === 'merchant') return metadata.high_risk ? '#dc2626' : '#6b7280';
    return '#9ca3af';
  };

  const getNodeIcon = (type) => {
    if (type === 'customer') return <Users size={14} color="#3b82f6" />;
    if (type === 'device') return <Smartphone size={14} color="#10b981" />;
    if (type === 'ip_address') return <Globe size={14} color="#8b5cf6" />;
    if (type === 'merchant') return <ShoppingBag size={14} color="#f59e0b" />;
    return <Layers size={14} />;
  };

  return (
    <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1f2937', paddingBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Layers size={24} color="#818cf8" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: '800', color: '#f3f4f6', margin: 0 }}>
              Relationship & Network Intelligence
            </h1>
          </div>
          <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Discover multi-hop entity linkages across customers, hardware devices, routing IPs, and high-risk merchant rings.
          </p>
        </div>

        <button 
          onClick={fetchData} 
          style={styles.refreshBtn}
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Sync Network Graph
        </button>
      </div>

      {/* Cluster Warnings Summary Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        <div style={styles.summaryBox}>
          <span style={styles.summaryLabel}>DETECTED ANOMALY CLUSTERS</span>
          <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#ef4444' }}>{clusters.length}</span>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Potential risk networks identified</span>
        </div>
        <div style={styles.summaryBox}>
          <span style={styles.summaryLabel}>TRACKED GRAPH NODES</span>
          <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#38bdf8' }}>{graphData.total_nodes || 0}</span>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Customers, devices, IPs & merchants</span>
        </div>
        <div style={styles.summaryBox}>
          <span style={styles.summaryLabel}>ACTIVE RELATIONSHIP EDGES</span>
          <span style={{ fontSize: '1.5rem', fontWeight: '800', color: '#34d399' }}>{graphData.total_edges || 0}</span>
          <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Authenticated sessions & routing links</span>
        </div>
      </div>

      {/* Main Layout: Left = Cluster Discovery & Entities; Right = Interactive Visual Node Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '1.25rem' }}>
        
        {/* Left Column: Emerging Clusters List */}
        <div style={styles.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={() => setActiveTab('clusters')}
                style={{
                  ...styles.tabBtn,
                  borderBottom: activeTab === 'clusters' ? '2px solid #818cf8' : 'none',
                  color: activeTab === 'clusters' ? '#f3f4f6' : '#9ca3af'
                }}
              >
                Emerging Risk Clusters ({clusters.length})
              </button>
              <button 
                onClick={() => setActiveTab('entities')}
                style={{
                  ...styles.tabBtn,
                  borderBottom: activeTab === 'entities' ? '2px solid #818cf8' : 'none',
                  color: activeTab === 'entities' ? '#f3f4f6' : '#9ca3af'
                }}
              >
                Connected Entities ({graphData.nodes?.length || 0})
              </button>
            </div>
          </div>

          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: '#9ca3af' }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 0.5rem auto', color: '#818cf8' }} />
              Tracing entity multi-hop linkages...
            </div>
          ) : activeTab === 'clusters' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {clusters.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: '#9ca3af' }}>No abnormal clusters detected.</div>
              ) : (
                clusters.map((c, idx) => (
                  <div key={idx} style={styles.clusterCard}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: '700', fontSize: '0.9rem', color: '#f3f4f6' }}>
                        {c.label}
                      </span>
                      <span style={{
                        padding: '0.15rem 0.45rem',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: '800',
                        backgroundColor: c.severity === 'CRITICAL' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: c.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b',
                        border: `1px solid ${c.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b'}`
                      }}>
                        {c.severity}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.8rem', color: '#d1d5db', margin: '0.4rem 0' }}>
                      {c.description}
                    </p>

                    <div style={{ fontSize: '0.75rem', color: '#9ca3af', backgroundColor: '#0f172a', padding: '0.5rem', borderRadius: '4px', border: '1px solid #1e293b' }}>
                      <strong style={{ color: '#818cf8' }}>Observed Pattern:</strong> {c.observed_pattern}
                    </div>

                    <div style={{ fontSize: '0.72rem', color: '#10b981', marginTop: '0.35rem' }}>
                      <strong>Action:</strong> {c.recommended_action}
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '520px', overflowY: 'auto' }}>
              {graphData.nodes.map((node) => (
                <div 
                  key={node.id} 
                  onClick={() => setSelectedNode(node)}
                  style={{
                    ...styles.entityRow,
                    backgroundColor: selectedNode?.id === node.id ? '#1e293b' : '#0f172a',
                    borderColor: selectedNode?.id === node.id ? '#818cf8' : '#1e293b'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {getNodeIcon(node.type)}
                    <span style={{ fontWeight: '600', color: '#f3f4f6', fontSize: '0.85rem' }}>{node.label}</span>
                    <span style={{ fontSize: '0.7rem', color: '#6b7280', textTransform: 'uppercase' }}>({node.type})</span>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: '#818cf8', fontWeight: '600' }}>Inspect →</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Entity Inspector & Multi-Hop Connections */}
        <div style={styles.card}>
          <div style={{ borderBottom: '1px solid #1f2937', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f3f4f6', margin: 0 }}>
              Entity Inspector & Connection Graph
            </h3>
            <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>Relationship Details</span>
          </div>

          {!selectedNode ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
              Select an entity node from the left to inspect its graph linkages.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              
              {/* Node Card */}
              <div style={{ padding: '0.85rem', backgroundColor: '#0f172a', borderRadius: '6px', border: '1px solid #1e293b' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <span style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: getNodeColor(selectedNode.type, selectedNode.metadata)
                  }}></span>
                  <span style={{ fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: '700' }}>
                    {selectedNode.type}
                  </span>
                </div>
                <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#f3f4f6' }}>
                  {selectedNode.label}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace', marginTop: '0.2rem' }}>
                  ID: {selectedNode.id}
                </div>
              </div>

              {/* Node Metadata Attributes */}
              <div>
                <span style={styles.miniLabel}>METADATA ATTRIBUTES</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {Object.entries(selectedNode.metadata || {}).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', padding: '0.35rem 0.5rem', backgroundColor: '#1f2937', borderRadius: '4px' }}>
                      <span style={{ color: '#9ca3af' }}>{k}:</span>
                      <span style={{ color: '#f3f4f6', fontWeight: '600' }}>{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Connected Relationships in Graph */}
              <div>
                <span style={styles.miniLabel}>DIRECT RELATIONSHIP EDGES</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '240px', overflowY: 'auto' }}>
                  {graphData.edges
                    .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((edge, idx) => (
                      <div key={idx} style={{
                        padding: '0.45rem 0.6rem',
                        backgroundColor: edge.is_risky ? 'rgba(239, 68, 68, 0.1)' : '#0f172a',
                        border: `1px solid ${edge.is_risky ? '#ef4444' : '#1e293b'}`,
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div>
                          <span style={{ color: '#94a3b8', fontWeight: '600' }}>{edge.relationship}: </span>
                          <span style={{ color: '#f3f4f6', fontWeight: '700' }}>
                            {edge.source === selectedNode.id ? edge.target : edge.source}
                          </span>
                        </div>
                        {edge.is_risky && (
                          <span style={{ color: '#ef4444', fontSize: '0.68rem', fontWeight: '800' }}>RISK LINK</span>
                        )}
                      </div>
                    ))}
                </div>
              </div>

            </div>
          )}
        </div>

      </div>

    </div>
  );
}

const styles = {
  refreshBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.45rem 0.85rem',
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '6px',
    color: '#d1d5db',
    fontSize: '0.85rem',
    cursor: 'pointer',
  },
  summaryBox: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.2rem',
  },
  summaryLabel: {
    fontSize: '0.7rem',
    fontWeight: '700',
    color: '#9ca3af',
    letterSpacing: '0.04em',
  },
  card: {
    backgroundColor: '#111827',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    padding: '1.25rem',
  },
  tabBtn: {
    background: 'none',
    border: 'none',
    padding: '0.4rem 0.75rem',
    fontSize: '0.85rem',
    fontWeight: '700',
    cursor: 'pointer',
  },
  clusterCard: {
    backgroundColor: '#0f172a',
    border: '1px solid #1e293b',
    borderRadius: '6px',
    padding: '0.85rem',
  },
  entityRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.5rem 0.75rem',
    borderRadius: '4px',
    border: '1px solid',
    cursor: 'pointer',
    transition: 'background-color 0.15s ease',
  },
  miniLabel: {
    display: 'block',
    fontSize: '0.68rem',
    fontWeight: '700',
    color: '#94a3b8',
    letterSpacing: '0.04em',
    marginBottom: '0.35rem',
  }
};
