import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  FaWallet, 
  FaTimes, 
  FaExternalLinkAlt, 
  FaArrowUp, 
  FaArrowDown,
  FaInfoCircle,
  FaFilter,
  FaChartLine,
  FaCoins,
  FaExchangeAlt,
  FaCheck,
  FaTimesCircle,
  FaChevronLeft,
  FaChevronRight,
  FaSortAmountDown,
  FaSortAmountUp
} from 'react-icons/fa';
import './SmartMoneyWalletModal.css';

function SmartMoneyWalletModal({ wallet, onClose }) {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProfitable, setShowProfitable] = useState(true);
  const [showLossMaking, setShowLossMaking] = useState(true);
  const modalRef = useRef(null);
  const [totalPnl, setTotalPnl] = useState(0);
  const [sortDirection, setSortDirection] = useState('desc'); // 'desc' for highest PNL first
  const [currentPage, setCurrentPage] = useState(1);
  const [tokensPerPage, setTokensPerPage] = useState(10); // Show 10 tokens per page
  const [walletData, setWalletData] = useState(null);
  
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

  useEffect(() => {
    const fetchWalletTokens = async () => {
      if (!wallet || !wallet.walletaddress) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // Fetch wallet token details from the API
        const apiUrl = `http://localhost:8080/api/reports/smartmoneywallet/${wallet.walletaddress}`;
        const response = await axios.get(apiUrl, {
          params: {
            sort_by: 'profitandloss',
            sort_order: sortDirection
          },
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        console.log('Smart money wallet report response:', response.data);
        
        // Set wallet data - this includes the overall PNL from smartmoneywallet table
        if (response.data.wallet) {
          setWalletData(response.data.wallet);
          // Use the PNL from the smart money wallet table
          setTotalPnl(parseFloat(response.data.wallet.profitAndLoss) || 0);
        }
        
        // Set token data - this includes token-specific PNL from smwallettoppnltoken table
        if (response.data.tokens && Array.isArray(response.data.tokens)) {
          // Log token data for debugging
          console.log('Token data received:', response.data.tokens);
          
          // Count profitable and loss-making tokens for debugging
          const profitableTokens = response.data.tokens.filter(token => parseFloat(token.profitAndLoss) >= 0);
          const lossTokens = response.data.tokens.filter(token => parseFloat(token.profitAndLoss) < 0);
          console.log(`Profitable tokens: ${profitableTokens.length}, Loss-making tokens: ${lossTokens.length}`);
          
          setTokens(response.data.tokens);
        } else {
          setTokens([]);
        }
      } catch (err) {
        console.error('Error fetching smart money wallet report:', err);
        
        // If API is not available, fall back to mock data for development
        if (process.env.NODE_ENV === 'development') {
          console.log('Falling back to mock data in development mode');
          const mockTokens = generateMockTokenData(wallet);
          const calculatedTotalPnl = mockTokens.reduce((sum, token) => sum + token.profitAndLoss, 0);
          setTotalPnl(calculatedTotalPnl);
          setTokens(mockTokens);
        } else {
          setError('Failed to load wallet token data. API endpoint may not be implemented yet.');
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchWalletTokens();
  }, [wallet, sortDirection]);

  // Add debugging useEffect to log token data whenever it changes
  useEffect(() => {
    if (tokens.length > 0) {
      console.log('Current tokens state:', tokens);
      
      // Analyze token data
      const profitableTokens = tokens.filter(token => parseFloat(token.profitAndLoss) >= 0);
      const lossTokens = tokens.filter(token => parseFloat(token.profitAndLoss) < 0);
      
      console.log(`Token analysis - Total: ${tokens.length}, Profitable: ${profitableTokens.length}, Loss-making: ${lossTokens.length}`);
      
      // Check if any tokens have invalid PNL values
      const invalidPnlTokens = tokens.filter(token => isNaN(parseFloat(token.profitAndLoss)));
      if (invalidPnlTokens.length > 0) {
        console.warn('Found tokens with invalid PNL values:', invalidPnlTokens);
      }
    }
  }, [tokens]);

  // Generate mock token data based on the wallet (for development/fallback only)
  const generateMockTokenData = (wallet) => {
    // Create some realistic token data with both profitable and loss-making tokens
    const baseTokens = [
      { 
        tokenId: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 
        tokenName: 'USDC',
        amountInvested: parseFloat(wallet.totalinvestedamount) * 0.3,
        amountTakenOut: parseFloat(wallet.amounttakenout) * 0.35,
        profitAndLoss: 1200.50,
        avgEntry: 1.0,
        avgExit: 1.0,
        currentPrice: 1.0
      },
      { 
        tokenId: 'So11111111111111111111111111111111111111112', 
        tokenName: 'SOL',
        amountInvested: parseFloat(wallet.totalinvestedamount) * 0.2,
        amountTakenOut: parseFloat(wallet.amounttakenout) * 0.15,
        profitAndLoss: -450.75,
        avgEntry: 70.25,
        avgExit: 65.50,
        currentPrice: 150.0
      },
      { 
        tokenId: 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So', 
        tokenName: 'mSOL',
        amountInvested: parseFloat(wallet.totalinvestedamount) * 0.15,
        amountTakenOut: parseFloat(wallet.amounttakenout) * 0.1,
        profitAndLoss: 850.25,
        avgEntry: 45.0,
        avgExit: 55.0,
        currentPrice: 160.0
      },
      { 
        tokenId: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263', 
        tokenName: 'BONK',
        amountInvested: parseFloat(wallet.totalinvestedamount) * 0.05,
        amountTakenOut: parseFloat(wallet.amounttakenout) * 0.02,
        profitAndLoss: -120.30,
        avgEntry: 0.00001,
        avgExit: 0.000008,
        currentPrice: 0.000015
      },
      { 
        tokenId: '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs', 
        tokenName: 'ETH (Wormhole)',
        amountInvested: parseFloat(wallet.totalinvestedamount) * 0.25,
        amountTakenOut: parseFloat(wallet.amounttakenout) * 0.3,
        profitAndLoss: -250.45,
        avgEntry: 3500,
        avgExit: 3300,
        currentPrice: 3800
      }
    ];
    
    // Generate additional tokens with random PNL values (both positive and negative)
    const additionalTokens = [];
    const tokenNames = ['JUP', 'RAY', 'SRM', 'MNGO', 'SAMO', 'ORCA', 'ATLAS', 'POLIS', 'SLND', 'COPE'];
    
    for (let i = 0; i < 15; i++) {
      const isProfit = Math.random() > 0.5; // 50% chance of profit
      const pnl = isProfit ? 
        Math.random() * 1000 + 50 : // Profitable: 50-1050
        -(Math.random() * 1000 + 50); // Loss: -50 to -1050
        
      additionalTokens.push({
        tokenId: `mock-token-${i}`,
        tokenName: tokenNames[i % tokenNames.length],
        amountInvested: parseFloat(wallet.totalinvestedamount) * (Math.random() * 0.1 + 0.01),
        amountTakenOut: parseFloat(wallet.amounttakenout) * (Math.random() * 0.1 + 0.01),
        profitAndLoss: pnl,
        avgEntry: Math.random() * 100 + 1,
        avgExit: Math.random() * 100 + 1,
        currentPrice: Math.random() * 100 + 1
      });
    }
    
    // Combine base tokens with additional tokens
    const allTokens = [...baseTokens, ...additionalTokens];
    
    // Log mock data for debugging
    const profitableCount = allTokens.filter(t => parseFloat(t.profitAndLoss) >= 0).length;
    const lossCount = allTokens.filter(t => parseFloat(t.profitAndLoss) < 0).length;
    console.log(`Generated mock data: ${allTokens.length} tokens (${profitableCount} profitable, ${lossCount} loss-making)`);
    
    return allTokens;
  };

  // Sort tokens by PNL
  const sortTokensByPnl = (tokensToSort, direction) => {
    return [...tokensToSort].sort((a, b) => {
      const aPnl = parseFloat(a.profitAndLoss) || 0;
      const bPnl = parseFloat(b.profitAndLoss) || 0;
      
      if (direction === 'desc') {
        return bPnl - aPnl; // Highest PNL first
      } else {
        return aPnl - bPnl; // Lowest PNL first
      }
    });
  };

  // Toggle sort direction
  const toggleSortDirection = () => {
    setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };
  
  const formatAbbreviatedCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    
    const num = parseFloat(value);
    if (isNaN(num)) return '-';
    
    // Format with appropriate suffix
    if (Math.abs(num) >= 1_000_000) {
      return `$${(num / 1_000_000).toFixed(2)}M`;
    } else if (Math.abs(num) >= 1_000) {
      return `$${(num / 1_000).toFixed(2)}K`;
    } else {
      return `$${num.toFixed(2)}`;
    }
  };
  
  const openExternalLink = (tokenId) => {
    if (!wallet || !wallet.walletaddress) return;
    
    // Open Cielo profile with token parameter
    window.open(`https://app.cielo.finance/profile/${wallet.walletaddress}?tokens=${tokenId}`, '_blank');
  };
  
  // Get filtered tokens based on toggle settings
  const getFilteredTokens = () => {
    // Log filter settings for debugging
    console.log(`Filter settings - Show profitable: ${showProfitable}, Show loss-making: ${showLossMaking}`);
    
    const filtered = tokens.filter(token => {
      const pnl = parseFloat(token.profitAndLoss) || 0;
      const isProfitable = pnl >= 0;
      
      // Log token filtering for debugging
      console.log(`Token ${token.tokenName} - PNL: ${pnl}, isProfitable: ${isProfitable}, Will show: ${(isProfitable && showProfitable) || (!isProfitable && showLossMaking)}`);
      
      if (isProfitable && !showProfitable) return false;
      if (!isProfitable && !showLossMaking) return false;
      
      return true;
    });
    
    console.log(`Filtered tokens: ${filtered.length} out of ${tokens.length}`);
    return filtered;
  };
  
  const handleModalClick = (e) => {
    e.stopPropagation();
  };
  
  // Add a specific handler for the close button
  const handleCloseClick = (e) => {
    e.stopPropagation();
    onClose();
  };
  
  const toggleProfitable = () => {
    setShowProfitable(!showProfitable);
    setCurrentPage(1); // Reset to first page when filter changes
  };
  
  const toggleLossMaking = () => {
    setShowLossMaking(!showLossMaking);
    setCurrentPage(1); // Reset to first page when filter changes
  };
  
  // Pagination functions
  const nextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };
  
  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };
  
  const changeTokensPerPage = (e) => {
    setTokensPerPage(parseInt(e.target.value));
    setCurrentPage(1); // Reset to first page when items per page changes
  };
  
  // Get current tokens for pagination
  const filteredTokens = getFilteredTokens();
  const indexOfLastToken = currentPage * tokensPerPage;
  const indexOfFirstToken = indexOfLastToken - tokensPerPage;
  const currentTokens = filteredTokens.slice(indexOfFirstToken, indexOfLastToken);
  const totalPages = Math.ceil(filteredTokens.length / tokensPerPage);
  
  const profitableCount = tokens.filter(token => parseFloat(token.profitAndLoss) >= 0).length;
  const lossCount = tokens.filter(token => parseFloat(token.profitAndLoss) < 0).length;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="wallet-token-modal-backdrop" onClick={handleBackdropClick}>
      <div className="wallet-token-modal-content" ref={modalRef} onClick={handleModalClick}>
        <div className="wallet-token-modal-header">
          <h2>
            <FaWallet />
            Smart Money Wallet Details
            <span className="wallet-address-display">
              {wallet?.walletaddress ? 
                `${wallet.walletaddress.substring(0, 6)}...${wallet.walletaddress.substring(wallet.walletaddress.length - 4)}` : 
                '-'}
            </span>
            <span className={`total-pnl ${totalPnl >= 0 ? 'positive' : 'negative'}`}>
              Total PNL: {formatCurrency(totalPnl)}
              {totalPnl >= 0 ? 
                <FaArrowUp style={{ fontSize: '0.9rem' }} /> : 
                <FaArrowDown style={{ fontSize: '0.9rem' }} />
              }
            </span>
          </h2>
          <button className="close-button" onClick={handleCloseClick} aria-label="Close">
            <FaTimes />
          </button>
        </div>
        
        <div className="wallet-token-modal-body">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading token data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : tokens.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Token Data Found</h3>
              <p>No token data available for this wallet.</p>
            </div>
          ) : (
            <>
              <div className="filter-controls">
                <div className="filter-toggle">
                  <button 
                    className={`toggle-button ${showProfitable ? 'active' : ''}`}
                    onClick={toggleProfitable}
                    title="Toggle profitable tokens"
                  >
                    <FaArrowUp className="profit-icon" />
                    Profitable ({profitableCount})
                    {showProfitable ? <FaCheck style={{ marginLeft: '5px' }} /> : <FaTimesCircle style={{ marginLeft: '5px', opacity: 0.7 }} />}
                  </button>
                  <button 
                    className={`toggle-button ${showLossMaking ? 'active' : ''}`}
                    onClick={toggleLossMaking}
                    title="Toggle loss-making tokens"
                  >
                    <FaArrowDown className="loss-icon" />
                    Loss-Making ({lossCount})
                    {showLossMaking ? <FaCheck style={{ marginLeft: '5px' }} /> : <FaTimesCircle style={{ marginLeft: '5px', opacity: 0.7 }} />}
                  </button>
                  <button 
                    className="toggle-button sort-button"
                    onClick={toggleSortDirection}
                    title={sortDirection === 'desc' ? "Sorting by highest PNL first" : "Sorting by lowest PNL first"}
                  >
                    {sortDirection === 'desc' ? 
                      <><FaSortAmountDown className="sort-icon" /> Highest PNL First</> : 
                      <><FaSortAmountUp className="sort-icon" /> Lowest PNL First</>
                    }
                  </button>
                </div>
                <div className="filter-info">
                  <FaInfoCircle />
                  <span>Showing {filteredTokens.length} of {tokens.length} tokens</span>
                </div>
              </div>
              
              {filteredTokens.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-icon">🔍</div>
                  <h3>No Tokens Match Filters</h3>
                  <p>
                    No tokens match your current filter settings. 
                    {!showProfitable && !showLossMaking ? 
                      " You've disabled both profitable and loss-making tokens." : 
                      !showProfitable ? 
                        " You've disabled profitable tokens." : 
                        " You've disabled loss-making tokens."
                    }
                  </p>
                  <button 
                    className="reset-filters-button"
                    onClick={() => {
                      setShowProfitable(true);
                      setShowLossMaking(true);
                      console.log("Reset filters to show all tokens");
                    }}
                  >
                    Show All Tokens
                  </button>
                </div>
              ) : (
                <>
                  <div className="token-table-container">
                    <table className="token-table">
                      <thead>
                        <tr>
                          <th>Token ID</th>
                          <th>Name</th>
                          <th className="text-center">Amount Invested</th>
                          <th className="text-center">Amount Taken Out</th>
                          <th className="text-center">PNL</th>
                          <th className="text-center">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentTokens.map((token, index) => {
                          const pnl = parseFloat(token.profitAndLoss) || 0;
                          const isProfitable = pnl >= 0;
                          
                          return (
                            <tr 
                              key={index}
                              className={isProfitable ? 'profitable-row' : 'loss-row'}
                            >
                              <td className="token-id" title={token.tokenId}>
                                {token.tokenId.substring(0, 6)}...{token.tokenId.substring(token.tokenId.length - 4)}
                              </td>
                              <td className="token-name">
                                {token.tokenName}
                              </td>
                              <td 
                                className="text-center" 
                                title={formatCurrency(token.amountInvested)}
                              >
                                {formatAbbreviatedCurrency(token.amountInvested)}
                              </td>
                              <td 
                                className="text-center" 
                                title={formatCurrency(token.amountTakenOut)}
                              >
                                {formatAbbreviatedCurrency(token.amountTakenOut)}
                              </td>
                              <td 
                                className={`text-center pnl-cell ${isProfitable ? 'positive' : 'negative'}`}
                                title={formatCurrency(token.profitAndLoss)}
                              >
                                {formatAbbreviatedCurrency(token.profitAndLoss)}
                              </td>
                              <td className="text-center">
                                <button 
                                  className="view-token-button"
                                  onClick={() => openExternalLink(token.tokenId)}
                                  title="View on Cielo"
                                >
                                  <FaExternalLinkAlt style={{ marginRight: '4px' }} />
                                  View
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination controls */}
                  <div className="pagination-controls">
                    <div className="pagination-info">
                      Showing {indexOfFirstToken + 1}-{Math.min(indexOfLastToken, filteredTokens.length)} of {filteredTokens.length} tokens
                    </div>
                    <div className="pagination-actions">
                      <select 
                        className="tokens-per-page" 
                        value={tokensPerPage} 
                        onChange={changeTokensPerPage}
                        title="Tokens per page"
                      >
                        <option value="5">5 per page</option>
                        <option value="10">10 per page</option>
                        <option value="15">15 per page</option>
                        <option value="20">20 per page</option>
                      </select>
                      <div className="pagination-buttons">
                        <button 
                          className={`pagination-button ${currentPage === 1 ? 'disabled' : ''}`}
                          onClick={prevPage}
                          disabled={currentPage === 1}
                          title="Previous page"
                        >
                          <FaChevronLeft />
                        </button>
                        <span className="page-indicator">
                          Page {currentPage} of {totalPages}
                        </span>
                        <button 
                          className={`pagination-button ${currentPage === totalPages ? 'disabled' : ''}`}
                          onClick={nextPage}
                          disabled={currentPage === totalPages}
                          title="Next page"
                        >
                          <FaChevronRight />
                        </button>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default SmartMoneyWalletModal; 