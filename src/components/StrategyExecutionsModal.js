import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { FaTimes, FaCopy, FaCheck, FaExternalLinkAlt } from 'react-icons/fa';
import './StrategyExecutionsModal.css';

// Execution status definitions from the enum
const EXECUTION_STATUS = {
  1: { description: "Active", color: "#5ac8fa", textColor: "#fff" },
  2: { description: "Invested", color: "#34c759", textColor: "#fff" },
  3: { description: "Taking profit", color: "#30d158", textColor: "#fff" },
  4: { description: "Stop loss", color: "#ff3b30", textColor: "#fff" },
  5: { description: "Completed with moonbag", color: "#5856d6", textColor: "#fff" },
  6: { description: "Completed", color: "#007aff", textColor: "#fff" },
  7: { description: "Failed during execution", color: "#ff9500", textColor: "#000" }
};

// Create an axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:8080',
  timeout: 10000,
  headers: {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json'
  }
});

function StrategyExecutionsModal({ strategy, onClose }) {
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [sortConfig, setSortConfig] = useState({
    key: 'createdat',
    direction: 'desc'
  });
  const modalRef = useRef(null);
  const tableContainerRef = useRef(null);

  // Fetch executions data when modal opens
  useEffect(() => {
    const fetchExecutions = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(`/api/reports/strategyperformance/config/${strategy.strategyid}/executions`);
        
        if (!response.data || !response.data.data) {
          throw new Error('Invalid response format from API');
        }
        
        setExecutions(response.data.data);
      } catch (err) {
        console.error('Failed to fetch executions:', err);
        setError('Failed to load strategy executions. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchExecutions();
    
    // Add event listener to close modal on escape key
    const handleEscKey = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    document.addEventListener('keydown', handleEscKey);
    
    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [strategy.strategyid, onClose]);

  // Check if table container is scrollable
  useEffect(() => {
    const checkTableScroll = () => {
      if (tableContainerRef.current) {
        const { scrollWidth, clientWidth } = tableContainerRef.current;
        if (scrollWidth > clientWidth) {
          tableContainerRef.current.classList.add('scrollable');
        } else {
          tableContainerRef.current.classList.remove('scrollable');
        }
      }
    };
    
    // Check on initial render and when data changes
    checkTableScroll();
    
    // Add resize listener
    window.addEventListener('resize', checkTableScroll);
    return () => window.removeEventListener('resize', checkTableScroll);
  }, [executions]);

  // Handle copy token ID to clipboard
  const handleCopyTokenId = (tokenId, e) => {
    e.stopPropagation();
    
    navigator.clipboard.writeText(tokenId)
      .then(() => {
        setCopiedId(tokenId);
        setTimeout(() => setCopiedId(null), 2000); // Reset after 2 seconds
      })
      .catch(err => {
        console.error('Failed to copy token ID:', err);
      });
  };

  // Handle sorting
  const handleSort = (key) => {
    setSortConfig(prevConfig => {
      if (prevConfig.key === key) {
        return {
          key,
          direction: prevConfig.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return {
        key,
        direction: 'desc'
      };
    });
  };

  // Get sorted executions
  const getSortedExecutions = () => {
    if (!executions || executions.length === 0) return [];
    
    const sortableExecutions = [...executions];
    
    return sortableExecutions.sort((a, b) => {
      // Handle null or undefined values
      if (a[sortConfig.key] === null || a[sortConfig.key] === undefined) return 1;
      if (b[sortConfig.key] === null || b[sortConfig.key] === undefined) return -1;
      
      // Handle specific columns
      if (['amountinvested', 'amounttakenout', 'entryprice', 'remainingCoinsValue', 'realizedPnl', 'pnl'].includes(sortConfig.key)) {
        const aValue = parseFloat(a[sortConfig.key]) || 0;
        const bValue = parseFloat(b[sortConfig.key]) || 0;
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      // Default string comparison
      if (typeof a[sortConfig.key] === 'string' && typeof b[sortConfig.key] === 'string') {
        return sortConfig.direction === 'asc' 
          ? a[sortConfig.key].localeCompare(b[sortConfig.key])
          : b[sortConfig.key].localeCompare(a[sortConfig.key]);
      }
      
      // Fallback for other types
      return sortConfig.direction === 'asc' 
        ? a[sortConfig.key] > b[sortConfig.key] ? 1 : -1
        : a[sortConfig.key] < b[sortConfig.key] ? 1 : -1;
    });
  };

  // Format currency values
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    // Handle zero values properly
    if (value === 0) return '$0.00';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  // Format number with commas
  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: decimals,
      minimumFractionDigits: decimals,
    }).format(num);
  };

  // Format large numbers with K, M, B suffixes
  const formatLargeNumber = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    
    // Ensure num is a number
    num = Number(num);
    
    // Convert to absolute value for easier comparison
    const absNum = Math.abs(num);
    
    // Format with appropriate suffix
    let formattedValue;
    if (absNum >= 1_000_000_000) {
      // Billions
      formattedValue = (num / 1_000_000_000).toFixed(2);
    } else if (absNum >= 1_000_000) {
      // Millions
      formattedValue = (num / 1_000_000).toFixed(2);
    } else if (absNum >= 1_000) {
      // Thousands
      formattedValue = (num / 1_000).toFixed(2);
    } else {
      // Regular number
      formattedValue = num.toFixed(2);
    }
    
    // Remove trailing zeros after decimal point
    if (formattedValue.includes('.')) {
      formattedValue = formattedValue.replace(/\.?0+$/, '');
    }
    
    // Add appropriate suffix
    if (absNum >= 1_000_000_000) {
      return `${formattedValue}B`;
    } else if (absNum >= 1_000_000) {
      return `${formattedValue}M`;
    } else if (absNum >= 1_000) {
      return `${formattedValue}K`;
    }
    
    return formattedValue;
  };

  // Get sort indicator icon
  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' ? '↑' : '↓';
    }
    return '';
  };

  // Open token explorer link
  const openExternalLink = (tokenId, e) => {
    e.stopPropagation();
    
    // Determine the explorer URL based on the token ID format
    // This is a placeholder - adjust based on your actual token ID format
    let explorerUrl;
    
    // For Solana tokens
    explorerUrl = `https://solscan.io/token/${tokenId}`;
    
    window.open(explorerUrl, '_blank', 'noopener,noreferrer');
  };

  // Get status badge with appropriate color
  const getStatusBadge = (statusCode) => {
    const status = EXECUTION_STATUS[statusCode] || { 
      description: "Unknown Status", 
      color: "#8e8e93", 
      textColor: "#fff" 
    };
    
    return (
      <div 
        className="status-badge" 
        style={{ 
          backgroundColor: status.color,
          color: status.textColor
        }}
        title={status.description}
      >
        {status.description}
      </div>
    );
  };

  // Handle click on modal backdrop to close
  const handleModalClick = (e) => {
    if (modalRef.current && !modalRef.current.contains(e.target)) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleModalClick}>
      <div className="modal-content" ref={modalRef}>
        <div className="modal-header">
          <h2>
            <span className="strategy-title">{strategy.strategyname}</span>
            <span className={`source-badge ${strategy.source?.toLowerCase().replace(/\s+/g, '-')}`}>
              {strategy.source}
            </span>
          </h2>
          <button className="close-button" onClick={onClose}>
            <FaTimes />
          </button>
        </div>
        
        <div className="modal-description">
          {strategy.description}
        </div>
        
        <div className="modal-stats">
          <div className="stat-card">
            <div className="stat-label">Invested</div>
            <div className="stat-value">
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.investedamount || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Taken Out</div>
            <div className="stat-value">
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.amounttakenout || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Remaining</div>
            <div className="stat-value">
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.remainingValue || exec.remainingCoinsValue || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Realized PNL</div>
            <div className={`stat-value ${executions.length > 0 && executions.reduce((sum, exec) => sum + Number(exec.realizedPnl || 0), 0) >= 0 ? 'positive' : 'negative'}`}>
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.realizedPnl || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total PNL</div>
            <div className={`stat-value ${executions.length > 0 && executions.reduce((sum, exec) => sum + Number(exec.pnl || 0), 0) >= 0 ? 'positive' : 'negative'}`}>
              {executions.length > 0 ? formatCurrency(executions.reduce((sum, exec) => sum + Number(exec.pnl || 0), 0)) : formatCurrency(0)}
            </div>
          </div>
        </div>
        
        <div className="modal-body">
          <h3>Strategy Executions</h3>
          
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading executions...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : executions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No Executions Found</h3>
              <p>This strategy doesn't have any executions yet.</p>
            </div>
          ) : (
            <div className="table-container" ref={tableContainerRef}>
              <table className="executions-table">
                <thead>
                  <tr>
                    <th onClick={() => handleSort('tokenid')} className="sortable">
                      Token ID {getSortIcon('tokenid')}
                    </th>
                    <th onClick={() => handleSort('tokenname')} className="sortable">
                      Token Name {getSortIcon('tokenname')}
                    </th>
                    <th onClick={() => handleSort('avgentryprice')} className="sortable">
                      Avg Entry {getSortIcon('avgentryprice')}
                    </th>
                    <th onClick={() => handleSort('investedamount')} className="sortable">
                      Invested {getSortIcon('investedamount')}
                    </th>
                    <th onClick={() => handleSort('amounttakenout')} className="sortable">
                      Taken Out {getSortIcon('amounttakenout')}
                    </th>
                    <th onClick={() => handleSort('status')} className="sortable">
                      Status {getSortIcon('status')}
                    </th>
                    <th onClick={() => handleSort('remainingValue')} className="sortable">
                      Remaining {getSortIcon('remainingValue')}
                    </th>
                    <th onClick={() => handleSort('realizedPnl')} className="sortable">
                      Realized PNL {getSortIcon('realizedPnl')}
                    </th>
                    <th onClick={() => handleSort('pnl')} className="sortable">
                      Total PNL {getSortIcon('pnl')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {getSortedExecutions().map((execution) => {
                    // Use API values directly instead of recalculating
                    const realizedPNL = execution.realizedPnl;
                    const totalPNL = execution.pnl;
                    
                    return (
                      <tr key={execution.executionid}>
                        <td className="token-id-cell text-center">
                          <div className="token-actions">
                            <span 
                              className={`token-id ${copiedId === execution.tokenid ? 'copied' : ''}`}
                              onClick={(e) => handleCopyTokenId(execution.tokenid, e)}
                              title="Click to copy token ID"
                            >
                              {execution.tokenid ? execution.tokenid.substring(0, 8) + '...' : '-'}
                              {copiedId === execution.tokenid ? 
                                <FaCheck className="action-icon copied" /> : 
                                <FaCopy className="action-icon" />}
                            </span>
                            <button 
                              className="link-button" 
                              onClick={(e) => openExternalLink(execution.tokenid, e)}
                              title="View on explorer"
                            >
                              <FaExternalLinkAlt />
                            </button>
                          </div>
                        </td>
                        <td className="token-name text-center">{execution.tokenname || '-'}</td>
                        <td className="text-center">{formatCurrency(execution.avgentryprice)}</td>
                        <td className="text-center" title={execution.investedamount ? formatCurrency(execution.investedamount) : '-'}>
                          {formatLargeNumber(execution.investedamount) || '-'}
                        </td>
                        <td className="text-center" title={execution.amounttakenout ? formatCurrency(execution.amounttakenout) : '-'}>
                          {formatLargeNumber(execution.amounttakenout) || '-'}
                        </td>
                        <td className="status-cell text-center">
                          {getStatusBadge(execution.status)}
                        </td>
                        <td className="text-center" title={execution.remainingValue || execution.remainingCoinsValue ? formatCurrency(execution.remainingValue || execution.remainingCoinsValue) : '-'}>
                          {formatLargeNumber(execution.remainingValue || execution.remainingCoinsValue) || '-'}
                        </td>
                        <td className={`text-center ${realizedPNL > 0 ? 'positive' : realizedPNL < 0 ? 'negative' : ''}`} 
                            title={realizedPNL !== null ? formatCurrency(realizedPNL) : '-'}>
                          {realizedPNL !== null ? formatLargeNumber(realizedPNL) : '-'}
                        </td>
                        <td className={`text-center ${totalPNL > 0 ? 'positive' : totalPNL < 0 ? 'negative' : ''}`} 
                            title={totalPNL !== null ? formatCurrency(totalPNL) : '-'}>
                          {totalPNL !== null ? formatLargeNumber(totalPNL) : '-'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <div className="table-footer">
                <div className="table-info">
                  Showing {executions.length} {executions.length === 1 ? 'execution' : 'executions'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StrategyExecutionsModal; 