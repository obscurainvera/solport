import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { FaTimes, FaCalendarAlt, FaExchangeAlt, FaChevronLeft, FaChevronRight, FaCheck } from 'react-icons/fa';
import './SmartMoneyMovementsModal.css';
import './TokenMovementsPopup.css';

function TokenMovementsPopup({ wallet, token, days, onClose }) {
  const [movementsData, setMovementsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedAddress, setCopiedAddress] = useState(false);
  const [isScrollable, setIsScrollable] = useState(false);
  const tableContainerRef = useRef(null);

  // Fetch token movements data when component mounts
  useEffect(() => {
    const fetchTokenMovements = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await axios.get(
          `http://localhost:8080/api/reports/smartmoneymovements/wallet/${wallet.walletaddress}/token/${token.tokenAddress}?days=${days}`,
          {
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            }
          }
        );
        
        setMovementsData(response.data);
      } catch (err) {
        console.error('Error fetching token movements:', err);
        setError(err.response?.data?.message || 'Failed to load token movements data');
      } finally {
        setLoading(false);
      }
    };
    
    if (wallet && wallet.walletaddress && token && token.tokenAddress) {
      fetchTokenMovements();
    }
  }, [wallet, token, days]);

  // Check if table is scrollable and update class
  useEffect(() => {
    const checkScroll = () => {
      if (tableContainerRef.current) {
        const { scrollWidth, clientWidth } = tableContainerRef.current;
        setIsScrollable(scrollWidth > clientWidth);
      }
    };

    // Check on initial load and when data changes
    checkScroll();
    
    // Add listener for resize events
    window.addEventListener('resize', checkScroll);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', checkScroll);
    };
  }, [movementsData]);

  // Prevent closing when clicking inside the popup
  const handlePopupClick = (e) => {
    e.stopPropagation();
  };

  // Handle copying token address to clipboard
  const handleCopyTokenAddress = () => {
    navigator.clipboard.writeText(token.tokenAddress)
      .then(() => {
        setCopiedAddress(true);
        setTimeout(() => setCopiedAddress(false), 2000);
      })
      .catch(err => {
        console.error('Failed to copy address:', err);
      });
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
  
  // Format numbers
  const formatNumber = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 6
    }).format(value);
  };

  return (
    <div className="token-popup-backdrop" onClick={onClose}>
      <div className="token-popup-content" onClick={handlePopupClick}>
        <div className="token-popup-header">
          <h2>
            <FaExchangeAlt className="movements-icon" />
            {token.tokenName || 'Unknown Token'} Movements
          </h2>
          <div className="token-address-display" onClick={handleCopyTokenAddress}>
            {token.tokenAddress ? 
              `${token.tokenAddress.substring(0, 8)}...${token.tokenAddress.substring(token.tokenAddress.length - 8)}` : 
              '-'}
            {copiedAddress && (
              <span className="copied-indicator">
                <FaCheck />
              </span>
            )}
          </div>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <FaTimes />
          </button>
        </div>
        
        <div className="token-popup-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading token movements...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : !movementsData || !movementsData.movements || movementsData.movements.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No Movement Data</h3>
              <p>No movement data available for this token in the selected time period.</p>
            </div>
          ) : (
            <>
              <div className="date-range-banner">
                <FaCalendarAlt className="date-icon" />
                <span className="date-text">
                  {formatDate(movementsData.period?.startDate)} - {formatDate(movementsData.period?.endDate)}
                </span>
              </div>
              
              <div className="movements-section">
                <div className="section-header">
                  <h3>Daily Movements</h3>
                  <div className="movements-count">
                    {movementsData.movements.length} records
                  </div>
                </div>
                
                <div 
                  className={`movements-table-container ${isScrollable ? 'scrollable' : ''}`}
                  ref={tableContainerRef}
                >
                  <table className="movements-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Buy Amount</th>
                        <th>Buy USD</th>
                        <th>Sell Amount</th>
                        <th>Sell USD</th>
                      </tr>
                    </thead>
                    <tbody>
                      {movementsData.movements.map((movement, index) => (
                        <tr key={index}>
                          <td title={formatDate(movement.date)}>
                            {formatDate(movement.date)}
                          </td>
                          <td 
                            className={movement.buyTokenChange > 0 ? 'positive' : ''} 
                            title={movement.buyTokenChange > 0 ? formatNumber(movement.buyTokenChange) : '-'}
                          >
                            {movement.buyTokenChange > 0 ? formatNumber(movement.buyTokenChange) : '-'}
                          </td>
                          <td 
                            className={movement.buyUsdChange > 0 ? 'positive' : ''} 
                            title={movement.buyUsdChange > 0 ? formatCurrency(movement.buyUsdChange) : '-'}
                          >
                            {movement.buyUsdChange > 0 ? formatCurrency(movement.buyUsdChange) : '-'}
                          </td>
                          <td 
                            className={movement.sellTokenChange > 0 ? 'negative' : ''}
                            title={movement.sellTokenChange > 0 ? formatNumber(movement.sellTokenChange) : '-'}
                          >
                            {movement.sellTokenChange > 0 ? formatNumber(movement.sellTokenChange) : '-'}
                          </td>
                          <td 
                            className={movement.sellUsdChange > 0 ? 'negative' : ''}
                            title={movement.sellUsdChange > 0 ? formatCurrency(movement.sellUsdChange) : '-'}
                          >
                            {movement.sellUsdChange > 0 ? formatCurrency(movement.sellUsdChange) : '-'}
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
    </div>
  );
}

export default TokenMovementsPopup; 