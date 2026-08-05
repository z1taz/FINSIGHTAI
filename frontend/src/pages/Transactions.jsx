import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { transactionsAPI } from '../services/api';
import { formatCurrency } from '../utils/currency';
import { 
  Plus, Search, Filter, Calendar, Trash2, ArrowLeft, ArrowRight,
  X, Check, AlertCircle, RefreshCw, Upload, ShieldCheck, ShieldAlert as ShieldAlertIcon, FileText
} from 'lucide-react';

const CATEGORIES = ["Groceries", "Dining Out", "Utilities", "Rent/Mortgage", "Entertainment", "Shopping", "Travel", "Wire Transfer", "Investment", "Salary", "Other"];

export default function Transactions({ currency = 'INR' }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [minAmount, setMinAmount] = useState('');
  const [maxAmount, setMaxAmount] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  
  // Add Transaction Modal
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    category: 'Groceries',
    merchant: '',
    description: '',
    mcc_code: '5999',
    is_merchant_verified: true,
    transaction_date: new Date().toISOString().substring(0, 16),
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Statement CSV Upload Modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        limit: 15,
      };
      
      if (search) params.search = search;
      if (category) params.category = category;
      if (startDate) params.start_date = new Date(startDate).toISOString();
      if (endDate) params.end_date = new Date(endDate).toISOString();
      if (minAmount) params.min_amount = parseFloat(minAmount);
      if (maxAmount) params.max_amount = parseFloat(maxAmount);
      
      const data = await transactionsAPI.getTransactions(params);
      setTransactions(data.items);
      setTotalPages(data.pages);
      setTotalCount(data.total);
    } catch (err) {
      console.error("Failed to load transactions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timeout = setTimeout(() => {
      fetchTransactions();
    }, 400);
    return () => clearTimeout(timeout);
  }, [search, category, startDate, endDate, minAmount, maxAmount, page]);

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this transaction record?")) {
      try {
        await transactionsAPI.deleteTransaction(id);
        fetchTransactions();
      } catch (err) {
        console.error("Failed to delete transaction:", err);
      }
    }
  };

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    setFormError('');
    setSubmitting(true);
    
    try {
      if (!formData.amount || parseFloat(formData.amount) <= 0) {
        throw new Error("Amount must be greater than zero.");
      }
      if (!formData.merchant.trim()) {
        throw new Error("Merchant field is required.");
      }

      // Security gate: transactions over $1,000 must come from a bank statement
      if (parseFloat(formData.amount) > 1000) {
        setShowModal(false);
        setShowUploadModal(true);
        setUploadError('');
        setSubmitting(false);
        alert("⚠️ Transactions over $1,000 cannot be added manually.\n\nFor security verification, please upload your official Bank Statement (CSV) so the system can verify the transaction directly from your bank records.");
        return;
      }
      
      await transactionsAPI.createTransaction({
        amount: parseFloat(formData.amount),
        category: formData.category,
        merchant: formData.merchant,
        description: formData.description,
        mcc_code: formData.mcc_code || "5999",
        is_merchant_verified: formData.is_merchant_verified,
        transaction_date: new Date(formData.transaction_date).toISOString(),
      });
      
      setShowModal(false);
      setFormData({
        amount: '',
        category: 'Groceries',
        merchant: '',
        description: '',
        mcc_code: '5999',
        is_merchant_verified: true,
        transaction_date: new Date().toISOString().substring(0, 16),
      });
      fetchTransactions();
    } catch (err) {
      setFormError(err.response?.data?.detail || err.message || "Failed to create transaction.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!csvFile) {
      setUploadError("Please select a CSV statement file to upload.");
      return;
    }
    setUploadError('');
    setUploading(true);

    try {
      const data = new FormData();
      data.append('file', csvFile);
      const res = await transactionsAPI.uploadStatement(data);
      alert(`✓ Successfully auto-imported ${res.length} transactions from Bank Statement and executed cybersecurity risk scan!`);
      setShowUploadModal(false);
      setCsvFile(null);
      fetchTransactions();
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Failed to parse bank statement CSV file.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: '700' }}>Transactions</h1>
          <p style={{ color: '#9ca3af', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            List statement of account: total {totalCount} records indexed.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => setShowUploadModal(true)}>
            <Upload size={16} color="#10b981" /> Upload Bank Statement (CSV)
          </button>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> Add Transaction
          </button>
        </div>
      </div>


      {/* Advanced Filters Panel */}
      <div className="card" style={styles.filterCard}>
        <div style={styles.filterRow}>
          {/* Text Search */}
          <div style={{ flex: 1, position: 'relative' }}>
            <Search size={16} color="#6b7280" style={styles.searchIcon} />
            <input
              type="text"
              placeholder="Search by merchant or description..."
              className="input"
              style={{ paddingLeft: '2.5rem' }}
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          
          {/* Category Dropdown */}
          <div style={{ width: '200px' }}>
            <select
              className="input"
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              style={{ appearance: 'none' }}
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Multi-Filter Collapsible Content */}
        <div style={styles.metaFilterRow}>
          {/* Dates */}
          <div style={styles.filterField}>
            <span style={styles.fieldLabel}>START DATE</span>
            <input
              type="date"
              className="input"
              value={startDate}
              onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
            />
          </div>
          
          <div style={styles.filterField}>
            <span style={styles.fieldLabel}>END DATE</span>
            <input
              type="date"
              className="input"
              value={endDate}
              onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
            />
          </div>

          {/* Amount range */}
          <div style={styles.filterField}>
            <span style={styles.fieldLabel}>MIN AMOUNT</span>
            <input
              type="number"
              placeholder="$0.00"
              className="input"
              value={minAmount}
              onChange={(e) => { setMinAmount(e.target.value); setPage(1); }}
            />
          </div>

          <div style={styles.filterField}>
            <span style={styles.fieldLabel}>MAX AMOUNT</span>
            <input
              type="number"
              placeholder="$10,000"
              className="input"
              value={maxAmount}
              onChange={(e) => { setMaxAmount(e.target.value); setPage(1); }}
            />
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="card">
        {loading ? (
          <div style={styles.loaderContainer}>
            <RefreshCw className="animate-spin" size={24} color="#10b981" />
            <span style={{ marginLeft: '0.75rem', color: '#9ca3af' }}>Indexing filters...</span>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>DATE</th>
                    <th>MERCHANT & ENTITY STATUS</th>
                    <th>MCC</th>
                    <th>CATEGORY</th>
                    <th>DESCRIPTION</th>
                    <th>SECURITY STATUS</th>
                    <th style={{ textAlign: 'right' }}>AMOUNT</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td style={{ minWidth: '110px', fontSize: '0.85rem' }}>
                        {new Date(tx.transaction_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                          <span style={{ fontWeight: '600', color: '#f3f4f6' }}>{tx.merchant}</span>
                          {tx.is_merchant_verified ? (
                            <span style={{ fontSize: '0.7rem', color: '#10b981', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                              <ShieldCheck size={12} /> Verified Corporate Entity
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.7rem', color: '#ef4444', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                              <ShieldAlertIcon size={12} /> Unverified Merchant ID
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '0.15rem 0.4rem', borderRadius: '4px', color: '#9ca3af' }}>
                          MCC-{tx.mcc_code || '5999'}
                        </span>
                      </td>
                      <td>
                        <span className="badge" style={{ backgroundColor: 'rgba(36, 47, 71, 0.4)', color: '#f3f4f6' }}>
                          {tx.category}
                        </span>
                      </td>
                      <td style={{ color: '#9ca3af', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.85rem' }}>
                        {tx.description || '-'}
                      </td>
                      <td>
                        {tx.is_fraudulent === 1 ? (
                          <span className="badge badge-danger">
                            🚨 Flagged ({Math.round(tx.fraud_score * 100)}%)
                          </span>
                        ) : (
                          <span className="badge badge-success">
                            ✓ Clean ({Math.round(tx.fraud_score * 100)}%)
                          </span>
                        )}
                      </td>
                      <td style={{ fontWeight: '600', textAlign: 'right', color: tx.category === 'Salary' ? '#10b981' : '#f3f4f6' }}>
                        {tx.category === 'Salary' ? '+' : '-'}{formatCurrency(tx.amount, currency)}
                      </td>
                      <td>
                        <button 
                          style={styles.deleteBtn}
                          onClick={() => handleDelete(tx.id)}
                          title="Delete Record"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {transactions.length === 0 && (
                    <tr>
                      <td colSpan="7" style={{ textAlign: 'center', color: '#9ca3af', padding: '3rem' }}>
                        No transactions match the selected filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div style={styles.pagination}>
                <button
                  className="btn btn-secondary"
                  disabled={page === 1}
                  onClick={() => setPage(p => Math.max(p - 1, 1))}
                  style={{ padding: '0.5rem 1rem' }}
                >
                  <ArrowLeft size={16} /> Prev
                </button>
                <span style={{ color: '#9ca3af', fontSize: '0.9rem' }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  className="btn btn-secondary"
                  disabled={page === totalPages}
                  onClick={() => setPage(p => Math.min(p + 1, totalPages))}
                  style={{ padding: '0.5rem 1rem' }}
                >
                  Next <ArrowRight size={16} />
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Add Transaction Modal */}
      {showModal && createPortal(
        <div style={styles.modalOverlay}>
          <div className="card animate-fade-in" style={styles.modalCard}>
            <div style={styles.modalHeader}>
              <h3 style={{ fontSize: '1.25rem' }}>Add Transaction</h3>
              <button style={styles.closeBtn} onClick={() => setShowModal(false)}>
                <X size={20} />
              </button>
            </div>

            {formError && (
              <div style={styles.formError}>
                <AlertCircle size={16} />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleAddTransaction} style={styles.modalForm}>
              <div className="form-group">
                <label className="label">MERCHANT NAME</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Amazon, Starbucks"
                  className="input"
                  value={formData.merchant}
                  onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="label">AMOUNT ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="0.00"
                    className="input"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="label">CATEGORY</label>
                  <select
                    className="input"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="label">TRANSACTION DATE & TIME</label>
                <input
                  type="datetime-local"
                  required
                  className="input"
                  value={formData.transaction_date}
                  onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="label">DESCRIPTION (OPTIONAL)</label>
                <input
                  type="text"
                  placeholder="Additional notes..."
                  className="input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div style={styles.modalActions}>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Creating...' : 'Save Transaction'}
                </button>
              </div>
            </form>
          </div>
        </div>,
        document.body
      )}

      {/* Bank Statement CSV Upload Modal */}
      {showUploadModal && createPortal(
        <div style={styles.modalOverlay}>
          <div className="card animate-fade-in" style={styles.modalCard}>
            <div style={styles.modalHeader}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Upload color="#10b981" size={20} /> Auto-Import Bank Statement
              </h3>
              <button style={styles.closeBtn} onClick={() => setShowUploadModal(false)}>
                <X size={20} />
              </button>
            </div>

            {uploadError && (
              <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444', padding: '0.75rem 1rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} />
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUploadSubmit} style={styles.modalForm}>
              <p style={{ color: '#9ca3af', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Select a bank statement CSV file. The system will automatically parse date, merchant, amount, category, detect merchant entity registration, and run cybersecurity risk scans.
              </p>

              <div className="form-group">
                <label className="label">CSV BANK STATEMENT FILE</label>
                <input
                  type="file"
                  accept=".csv"
                  className="input"
                  style={{ padding: '0.5rem' }}
                  onChange={(e) => setCsvFile(e.target.files[0])}
                  required
                />
              </div>

              <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '0.75rem', borderRadius: '8px', marginTop: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: '600', display: 'block', marginBottom: '0.25rem' }}>
                  Supported Standard CSV Headers:
                </span>
                <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontFamily: 'monospace' }}>
                  date, merchant, amount, category, description
                </span>
              </div>

              <div style={styles.modalActions}>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowUploadModal(false)}
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={uploading}
                >
                  {uploading ? 'Processing Statement...' : 'Import & Scan Statement'}
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


const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  filterCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  filterRow: {
    display: 'flex',
    gap: '1rem',
  },
  searchIcon: {
    position: 'absolute',
    left: '1rem',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  metaFilterRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
    borderTop: '1px solid var(--border-color)',
    paddingTop: '1rem',
  },
  filterField: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.4rem',
  },
  fieldLabel: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    fontWeight: '600',
  },
  loaderContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '3rem',
  },
  deleteBtn: {
    background: 'none',
    border: 'none',
    color: '#ef4444',
    cursor: 'pointer',
    padding: '0.25rem',
    display: 'flex',
    alignItems: 'center',
    borderRadius: '4px',
    transition: 'all 0.2s',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '1.5rem',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    backdropFilter: 'blur(6px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 99999,
    padding: '1rem',
  },
  modalCard: {
    maxWidth: '480px',
    width: '100%',
    padding: '2rem',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: '#9ca3af',
    cursor: 'pointer',
  },
  modalForm: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    marginTop: '1.5rem',
  },
  formError: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.75rem 1rem',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: '8px',
    color: '#ef4444',
    fontSize: '0.85rem',
    marginBottom: '1.25rem',
  },
};
