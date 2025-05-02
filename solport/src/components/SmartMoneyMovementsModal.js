import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaWallet, 
  FaTimes, 
  FaChartLine,
  FaExchangeAlt,
  FaCoins,
  FaMoneyBillWave,
  FaArrowUp,
  FaArrowDown,
  FaCalendarAlt,
  FaPercentage,
  FaChartBar,
  FaFilter,
  FaSort,
  FaCheck,
  FaSortUp,
  FaSortDown
} from 'react-icons/fa';
import './SmartMoneyMovementsModal.css';
import TokenMovementsPopup from './TokenMovementsPopup';

function SmartMoneyMovementsModal({ wallet, onClose }) {
  const [movementsData, setMovementsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(30);
  const [copiedTokenAddress, setCopiedTokenAddress] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'totalPnl', direction: 'desc' });
  const [selectedToken, setSelectedToken] = useState(null);
  const modalRef = useRef(null);

  // Center the modal in the visible viewport when it opens
  useEffect(() => {
    const centerModal = () => {
      if (modalRef.current) {
        // Get the current scroll position
        const scrollY = window.scrollY || window.pageYOffset;
        
        // Calculate the visible viewport
        const viewportHeight = window.innerHeight;
        // Position the modal in the center of the screen but slightly higher (at 45% instead of 50%)
        const viewportCenter = scrollY + (viewportHeight * 0.45);
        
        // Set the modal position to be centered in the visible viewport
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        modalRef.current.style.top = `${viewportCenter}px`;
        modalRef.current.style.transform = 'translate(-50%, -50%)';
        modalRef.current.style.left = '50%';
        modalRef.current.style.position = 'absolute';
      }
    };
    
    centerModal();
    window.addEventListener('resize', centerModal);
    
    return () => {
      window.removeEventListener('resize', centerModal);
      document.body.style.overflow = ''; // Restore scrolling when modal closes
    };
  }, []);

  // Fetch movements data when component mounts or days changes
  useEffect(() => {
    const fetchMovementsData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await axios.get(
          `http://localhost:8080/api/reports/smartmoneymovements/wallet/${wallet.walletaddress}?days=${days}`,
          {
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          }
        );
        
        setMovementsData(response.data);
      } catch (err) {
        console.error('Error fetching smart money movements:', err);
        setError(err.response?.data?.message || 'Failed to load movements data');
      } finally {
        setLoading(false);
      }
    };
    
    if (wallet && wallet.walletaddress) {
      fetchMovementsData();
    }
  }, [wallet, days]);

  // Sorting logic
  const requestSort = (key) => {
    let direction = 'asc';
    
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    
    setSortConfig({ key, direction });
  };
  
  // Get sorted data
  const getSortedData = () => {
    if (!movementsData?.tokens) return [];
    
    const sortableTokens = [...movementsData.tokens];
    
    if (sortConfig.key) {
      sortableTokens.sort((a, b) => {
        // Handle null values
        if (a[sortConfig.key] === null) return sortConfig.direction === 'asc' ? -1 : 1;
        if (b[sortConfig.key] === null) return sortConfig.direction === 'asc' ? 1 : -1;
        
        // Use standard comparison for numbers and strings
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    
    return sortableTokens;
  };

  // Format currency values
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };
  
  // Format percentages
  const formatPercentage = (value) => {
    if (value === null || value === undefined) return '-';
    
    return `${value.toFixed(2)}%`;
  };
  
  // Format numbers
  const formatNumber = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 6
    }).format(value);
  };
  
  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      return dateString;
    }
  };

  // Prevent closing when clicking inside the modal
  const handleModalClick = (e) => {
    e.stopPropagation();
  };
  
  // Handle day range change
  const handleDaysChange = (newDays) => {
    setDays(newDays);
  };

  // Handle copying token address to clipboard
  const handleCopyTokenAddress = (address, e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(address)
      .then(() => {
        setCopiedTokenAddress(address);
        setTimeout(() => setCopiedTokenAddress(null), 2000);
      })
      .catch(err => {
        console.error('Failed to copy address:', err);
      });
  };
  
  // Handle token row click to show token details popup
  const handleTokenClick = (token) => {
    setSelectedToken(token);
  };
  
  // Close token popup
  const handleCloseTokenPopup = () => {
    setSelectedToken(null);
  };
  
  // Get sort icon for column header
  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' 
        ? <FaSortUp className="sort-icon active" /> 
        : <FaSortDown className="sort-icon active" />;
    }
    return <FaSort className="sort-icon" />;
  };

  return (
    <div className="movements-modal-backdrop" onClick={onClose}>
      <div className="movements-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="movements-modal-header">
          <h2>
            <FaExchangeAlt className="movements-icon" />
            Smart Money Movements
            <span className="wallet-address-display">
              {wallet?.walletaddress ? 
                `${wallet.walletaddress.substring(0, 6)}...${wallet.walletaddress.substring(wallet.walletaddress.length - 4)}` : 
                '-'}
            </span>
          </h2>
          <div className="time-range-selector">
            <span className="time-label"><FaCalendarAlt /> Time Range:</span>
            <div className="time-buttons">
              <button 
                className={days === 7 ? 'active' : ''} 
                onClick={() => handleDaysChange(7)}
              >
                7 Days
              </button>
              <button 
                className={days === 30 ? 'active' : ''} 
                onClick={() => handleDaysChange(30)}
              >
                30 Days
              </button>
              <button 
                className={days === 90 ? 'active' : ''} 
                onClick={() => handleDaysChange(90)}
              >
                90 Days
              </button>
            </div>
          </div>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>
        
        <div className="movements-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading smart money movements...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : !movementsData || !movementsData.tokens || movementsData.tokens.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No Movement Data</h3>
              <p>No token movement data available for this wallet in the selected time period.</p>
            </div>
          ) : (
            <>
              <div className="date-range-banner">
                <FaCalendarAlt className="date-icon" />
                <span className="date-text">
                  {formatDate(movementsData.period?.startDate)} - {formatDate(movementsData.period?.endDate)}
                </span>
              </div>
              
              <div className="tokens-section">
                <div className="section-header">
                  <h3>Token Movements</h3>
                  <div className="tokens-count">
                    {movementsData.tokens.length} tokens
                  </div>
                </div>
                
                <div className="tokens-table-container">
                  <table className="tokens-table">
                    <thead>
                      <tr>
                        <th className="sortable" onClick={() => requestSort('tokenName')}>
                          Token {getSortIcon('tokenName')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('totalInvested')}>
                          Total Invested {getSortIcon('totalInvested')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('totalTakenOut')}>
                          Total Taken Out {getSortIcon('totalTakenOut')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('remainingCoins')}>
                          Remaining Coins {getSortIcon('remainingCoins')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('currentPrice')}>
                          Current Price {getSortIcon('currentPrice')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('remainingValue')}>
                          Remaining Value {getSortIcon('remainingValue')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('realizedPnl')}>
                          Realized PNL {getSortIcon('realizedPnl')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('totalPnl')}>
                          Total PNL {getSortIcon('totalPnl')}
                        </th>
                        <th className="sortable" onClick={() => requestSort('pnlPercentage')}>
                          PNL % {getSortIcon('pnlPercentage')}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {getSortedData().map((token, index) => (
                        <tr 
                          key={index} 
                          onClick={() => handleTokenClick(token)}
                          className="clickable-row"
                        >
                          <td 
                            className="token-name clickable" 
                            onClick={(e) => {
                              e.stopPropagation(); // Prevent row click
                              handleCopyTokenAddress(token.tokenAddress, e);
                            }}
                            title="Click to copy token address"
                          >
                            <span className="token-name-text">
                              {token.tokenName || 'Unknown'}
                              {copiedTokenAddress === token.tokenAddress && (
                                <span className="copied-indicator">
                                  <FaCheck />
                                </span>
                              )}
                            </span>
                          </td>
                          <td>{formatCurrency(token.totalInvested)}</td>
                          <td>{formatCurrency(token.totalTakenOut)}</td>
                          <td>{formatNumber(token.remainingCoins)}</td>
                          <td>{formatCurrency(token.currentPrice)}</td>
                          <td>{formatCurrency(token.remainingValue)}</td>
                          <td className={token.realizedPnl >= 0 ? 'positive' : 'negative'}>
                            {formatCurrency(token.realizedPnl)}
                          </td>
                          <td className={token.totalPnl >= 0 ? 'positive' : 'negative'}>
                            {formatCurrency(token.totalPnl)}
                          </td>
                          <td className={token.pnlPercentage >= 0 ? 'positive' : 'negative'}>
                            {formatPercentage(token.pnlPercentage)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Token Movements Popup */}
      {selectedToken && (
        <TokenMovementsPopup 
          wallet={wallet}
          token={selectedToken}
          days={days}
          onClose={handleCloseTokenPopup}
        />
      )}
    </div>
  );
}

export default SmartMoneyMovementsModal; 