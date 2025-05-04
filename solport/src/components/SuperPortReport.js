import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Container, Row, Col, Card, Button, 
  Form, Spinner, Badge, Tooltip, OverlayTrigger,
  InputGroup
} from 'react-bootstrap';
import { 
  FaFilter, FaRegCopy, FaCheckCircle, FaExclamationTriangle, 
  FaHistory, FaCoins, FaUsers, FaWallet, FaTimes, FaSearch,
  FaChevronDown, FaCheck
} from 'react-icons/fa';
import WalletInvestedModal from './WalletInvestedModal';
import './SuperPortReport.css';

const SuperPortReport = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [copiedTokenId, setCopiedTokenId] = useState(null);
  const [totalRecords, setTotalRecords] = useState(0);
  const [executionTime, setExecutionTime] = useState(0);
  const [activeFilters, setActiveFilters] = useState(0);
  const [selectedToken, setSelectedToken] = useState(null);
  const [showWalletModal, setShowWalletModal] = useState(false);
  
  // Filter popup states
  const [showWalletCategoryPopup, setShowWalletCategoryPopup] = useState(false);
  const [showWalletTypePopup, setShowWalletTypePopup] = useState(false);
  const [showTokenAgePopup, setShowTokenAgePopup] = useState(false);
  
  // Define token age ranges
  const TOKEN_AGE_RANGES = [
    { id: '1-5', label: '1-5 days', min: 1, max: 5 },
    { id: '5-10', label: '5-10 days', min: 5, max: 10 },
    { id: '10-20', label: '10-20 days', min: 10, max: 20 },
    { id: '20-50', label: '20-50 days', min: 20, max: 50 },
    { id: '50-100', label: '50-100 days', min: 50, max: 100 },
    { id: '>100', label: '> 100 days', min: 100, max: null }
  ];
  
  // Filter states
  const [filters, setFilters] = useState({
    // Wallet breakdown filters
    walletCategory: '',
    walletType: '',
    minWalletCount: '',
    minAmountInvested: '',
    
    // Token age filter
    tokenAgeRange: '',
    
    // Default sort options (not shown in UI)
    sortBy: 'smartbalance',
    sortOrder: 'desc'
  });

  // Reference for filter panel
  const filterPanelRef = useRef(null);
  
  // Fetch data on component mount and when filters change
  useEffect(() => {
    fetchReportData();
  }, []);

  // Count active filters - exclude sort parameters
  useEffect(() => {
    const count = Object.entries(filters)
      .filter(([key, value]) => 
        value !== '' && 
        !['sortBy', 'sortOrder'].includes(key)
      )
      .length;
    setActiveFilters(count);
  }, [filters]);

  // Handle outside click to close filter panel
  useEffect(() => {
    function handleClickOutside(event) {
      // Only close if clicking on the backdrop directly
      // This prevents closing when clicking on filter panel elements
      if (event.target.className === 'sp-filter-backdrop') {
        setShowFilters(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Copy token ID to clipboard
  const copyToClipboard = (tokenId) => {
    navigator.clipboard.writeText(tokenId)
      .then(() => {
        setCopiedTokenId(tokenId);
        setTimeout(() => setCopiedTokenId(null), 2000);
      })
      .catch(err => console.error('Failed to copy:', err));
  };
  
  // Handle token click to show wallet invested modal
  const handleTokenClick = (token) => {
    setSelectedToken(token);
    setShowWalletModal(true);
  };
  
  // Close wallet invested modal
  const closeWalletModal = () => {
    setSelectedToken(null);
    setShowWalletModal(false);
  };

  // Fetch report data from API
  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Process token age range if selected
      let queryParams = {};
      
      // Copy all non-empty filters
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== '') {
          queryParams[key] = value;
        }
      });
      
      // Handle token age range conversion
      if (filters.tokenAgeRange) {
        const selectedRange = TOKEN_AGE_RANGES.find(range => range.id === filters.tokenAgeRange);
        if (selectedRange) {
          // Remove tokenAgeRange from params
          delete queryParams.tokenAgeRange;
          
          // Add min/max token age parameters
          if (selectedRange.min !== null) {
            queryParams.minTokenAge = selectedRange.min;
          }
          if (selectedRange.max !== null) {
            queryParams.maxTokenAge = selectedRange.max;
          }
        }
      }
      
      // Convert to URL query string
      const queryString = Object.entries(queryParams)
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&');
      
      // Add limit parameter to fetch more records (at least 15)
      const queryWithLimit = queryString ? `${queryString}&limit=15` : 'limit=15';
      
      console.log("Fetching data with params:", queryWithLimit);
      const response = await axios.get(`/api/reports/superportreport?${queryWithLimit}`);
      
      if (response.data && response.data.data) {
        setReportData(response.data.data);
        setTotalRecords(response.data.metadata.count);
        setExecutionTime(response.data.metadata.execution_time_seconds);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      console.error('Error fetching report:', err);
      setError(err.message || 'Failed to fetch report data');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Apply filters
  const applyFilters = (e) => {
    if (e) e.preventDefault();
    fetchReportData();
    setShowFilters(false);
    setShowWalletCategoryPopup(false);
    setShowWalletTypePopup(false);
    setShowTokenAgePopup(false);
  };
  
  // Reset filters
  const resetFilters = () => {
    setFilters({
      // Wallet breakdown filters
      walletCategory: '',
      walletType: '',
      minWalletCount: '',
      minAmountInvested: '',
      
      // Token age filter
      tokenAgeRange: '',
      
      // Default sort options
      sortBy: 'smartbalance',
      sortOrder: 'desc'
    });
  };
  
  // Format token age to display in days/months/years
  const formatTokenAge = (age) => {
    if (!age) return 'N/A';
    
    if (age < 1) {
      // Less than 1 day
      return '< 1d';
    } else if (age < 30) {
      // Days
      return `${Math.floor(age)}d`;
    } else if (age < 365) {
      // Months
      return `${Math.floor(age / 30)}m`;
    } else {
      // Years with decimal
      return `${(age / 365).toFixed(1)}y`;
    }
  };
  
  // Format number with commas and specified decimal places
  const formatNumber = (num, decimals = 2) => {
    if (num === undefined || num === null) return 'N/A';
    
    // Handle different data types
    const parsedNum = typeof num === 'string' ? parseFloat(num) : num;
    
    if (isNaN(parsedNum)) return 'N/A';
    
    // Format large numbers with suffix (K, M, B)
    if (parsedNum >= 1000000000) {
      return `$${(parsedNum / 1000000000).toFixed(1)}B`;
    } else if (parsedNum >= 1000000) {
      return `$${(parsedNum / 1000000).toFixed(1)}M`;
    } else if (parsedNum >= 1000) {
      return `$${(parsedNum / 1000).toFixed(1)}K`;
    }
    
    // Format with commas and fixed decimal places
    return parsedNum.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };
  
  // Get attention status color
  const getAttentionStatusColor = (status) => {
    switch(status?.toUpperCase()) {
      case 'NEW':
        return '#34c759'; // Green
      case 'ACTIVE':
        return '#ffcc00'; // Yellow
      case 'INACTIVE':
        return '#ff3b30'; // Red
      default:
        return '#8e8e93'; // Gray
    }
  };
  
  // Render tooltip for token ID
  const renderTokenIdTooltip = (tokenId) => (props) => (
    <Tooltip id={`token-tooltip-${tokenId}`} {...props}>
      {copiedTokenId === tokenId ? 'Copied!' : 'Click to copy token ID'}
    </Tooltip>
  );

  // Render wallet category breakdown
  const renderWalletCategories = (item) => {
    // Check if the item has the new wallet_data structure
    if (!item.wallet_data) {
      console.warn('Item is missing wallet_data structure:', item);
      return <div className="wallet-categories-container">No wallet data available</div>;
    }
    
    // Format amount with K, M, B for readability
    const formatCompactAmount = (amount) => {
      if (!amount || amount === 0) return '$0';
      
      const num = parseFloat(amount);
      if (isNaN(num)) return '$0';
      
      if (num >= 1000000000) {
        return `$${(num / 1000000000).toFixed(1)}B`;
      } else if (num >= 1000000) {
        return `$${(num / 1000000).toFixed(1)}M`;
      } else if (num >= 1000) {
        return `$${(num / 1000).toFixed(1)}K`;
      }
      
      return `$${num.toFixed(0)}`;
    };
    
    // Extract the wallet data categories
    const walletData = item.wallet_data;
    const categories = ['0-300K', '300K-1M', '>1M'];
    
    // Prepare data for each wallet type
    const walletTypes = ['No Selling', '<30%', '>30%'];
    
    return (
      <div className="wallet-categories-container">
        <table className="categories-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>0-300K</th>
              <th>300K-1M</th>
              <th>&gt;1M</th>
            </tr>
          </thead>
          <tbody>
            {walletTypes.map((type, index) => (
              <tr key={index}>
                <td className="category-name">{type}</td>
                {categories.map((category, catIndex) => {
                  // Get the data for this category and type
                  const categoryData = walletData[category]?.category_data?.[type] || {
                    total_number_of_wallets: 0,
                    total_invested_amount: 0,
                    total_amount_taken_out: 0
                  };
                  
                  return (
                    <td key={catIndex}>
                      <div className="wallet-count-amount">
                        <span className="wallet-count">{categoryData.total_number_of_wallets}</span>
                        <span className="wallet-separator">·</span>
                        <span className="wallet-amount">
                          <span className="invested">{formatCompactAmount(categoryData.total_invested_amount)}</span>
                          <span className="separator">/</span>
                          <span className="taken-out">{formatCompactAmount(categoryData.total_amount_taken_out)}</span>
                        </span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
            
            {/* Add a totals row */}
            <tr className="totals-row">
              <td className="category-name">Totals</td>
              {categories.map((category, catIndex) => {
                const totalData = walletData[category] || {
                  total_number_of_wallets: 0,
                  total_invested_amount: 0,
                  total_amount_taken_out: 0
                };
                
                return (
                  <td key={catIndex}>
                    <div className="wallet-count-amount totals">
                      <span className="wallet-count">{totalData.total_number_of_wallets}</span>
                      <span className="wallet-separator">·</span>
                      <span className="wallet-amount">
                        <span className="invested">{formatCompactAmount(totalData.total_invested_amount)}</span>
                        <span className="separator">/</span>
                        <span className="taken-out">{formatCompactAmount(totalData.total_amount_taken_out)}</span>
                      </span>
                    </div>
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <Container fluid className="superport-report px-4 py-3">
      <Row className="mb-3">
        <Col>
          <h2 className="page-title">SuperPort Report</h2>
          <p className="page-description">
            Comprehensive analysis of tokens with wallet investment patterns and attention metrics
          </p>
        </Col>
        <Col xs="auto" className="d-flex align-items-center">
          <Button 
            variant="dark" 
            className="filter-btn"
            onClick={() => setShowFilters(!showFilters)}
          >
            <FaFilter /> Filters
            {activeFilters > 0 && (
              <Badge bg="primary">{activeFilters}</Badge>
            )}
          </Button>
        </Col>
      </Row>
      
      {/* Filter Panel */}
      {showFilters && (
        <>
          <div className="sp-filter-backdrop" onClick={() => setShowFilters(false)}></div>
          <div className="sp-filter-panel" ref={filterPanelRef}>
            <div className="sp-filter-header">
              <h3 className="sp-filter-title"><FaFilter /> Filter Options</h3>
              <button 
                className="sp-filter-reset" 
                onClick={resetFilters}
                disabled={Object.values(filters).every(val => val === '')}
              >
                <FaTimes /> Reset
              </button>
            </div>
            <div className="sp-filter-body">
              {/* Wallet Breakdown Filters */}
              <div className="sp-filter-row">
                <div className="sp-filter-group">
                  <label><FaUsers className="sp-filter-icon" /> Wallet Category</label>
                  <div 
                    className="sp-filter-selector" 
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setShowWalletTypePopup(false);
                      setShowTokenAgePopup(false);
                      setShowWalletCategoryPopup(!showWalletCategoryPopup);
                    }}
                  >
                    {filters.walletCategory ? filters.walletCategory : 'All Categories'}
                    <FaChevronDown className={`sp-filter-dropdown-icon ${showWalletCategoryPopup ? 'open' : ''}`} />
                  </div>
                  {showWalletCategoryPopup && (
                    <>
                      <div className="sp-filter-dropdown-overlay" onClick={() => setShowWalletCategoryPopup(false)}></div>
                      <div className="sp-filter-popup">
                        <h5>Select Wallet Category</h5>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletCategory === '' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletCategory: '' }));
                            setShowWalletCategoryPopup(false);
                          }}
                        >
                          All Categories
                          {filters.walletCategory === '' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletCategory === '0-300K' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletCategory: '0-300K' }));
                            setShowWalletCategoryPopup(false);
                          }}
                        >
                          0-300K
                          {filters.walletCategory === '0-300K' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletCategory === '300K-1M' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletCategory: '300K-1M' }));
                            setShowWalletCategoryPopup(false);
                          }}
                        >
                          300K-1M
                          {filters.walletCategory === '300K-1M' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletCategory === '>1M' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletCategory: '>1M' }));
                            setShowWalletCategoryPopup(false);
                          }}
                        >
                          Greater than 1M
                          {filters.walletCategory === '>1M' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                      </div>
                    </>
                  )}
                </div>
                
                <div className="sp-filter-group">
                  <label><FaWallet className="sp-filter-icon" /> Wallet Type</label>
                  <div 
                    className="sp-filter-selector" 
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setShowWalletCategoryPopup(false);
                      setShowTokenAgePopup(false);
                      setShowWalletTypePopup(!showWalletTypePopup);
                    }}
                  >
                    {filters.walletType ? filters.walletType : 'All Types'}
                    <FaChevronDown className={`sp-filter-dropdown-icon ${showWalletTypePopup ? 'open' : ''}`} />
                  </div>
                  {showWalletTypePopup && (
                    <>
                      <div className="sp-filter-dropdown-overlay" onClick={() => setShowWalletTypePopup(false)}></div>
                      <div className="sp-filter-popup">
                        <h5>Select Wallet Type</h5>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletType === '' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletType: '' }));
                            setShowWalletTypePopup(false);
                          }}
                        >
                          All Types
                          {filters.walletType === '' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletType === 'no-selling' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletType: 'no-selling' }));
                            setShowWalletTypePopup(false);
                          }}
                        >
                          No Selling
                          {filters.walletType === 'no-selling' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletType === '<30%' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletType: '<30%' }));
                            setShowWalletTypePopup(false);
                          }}
                        >
                          Less than 30%
                          {filters.walletType === '<30%' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        <div 
                          className={`sp-filter-popup-option ${filters.walletType === '>30%' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, walletType: '>30%' }));
                            setShowWalletTypePopup(false);
                          }}
                        >
                          Greater than 30%
                          {filters.walletType === '>30%' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                      </div>
                    </>
                  )}
                </div>
                
                <div className="sp-filter-group">
                  <label>Minimum Wallets</label>
                  <div className="sp-filter-input-with-icon">
                    <input
                      type="number"
                      name="minWalletCount"
                      value={filters.minWalletCount}
                      onChange={handleFilterChange}
                      placeholder="Enter minimum number of wallets"
                    />
                    <FaUsers className="sp-filter-input-icon" />
                  </div>
                </div>
                
                <div className="sp-filter-group">
                  <label>Minimum Amount Invested</label>
                  <div className="sp-filter-input-with-icon">
                    <input
                      type="number"
                      name="minAmountInvested"
                      value={filters.minAmountInvested}
                      onChange={handleFilterChange}
                      placeholder="Enter minimum amount in $"
                    />
                    <FaCoins className="sp-filter-input-icon" />
                  </div>
                </div>
              </div>
              
              {/* Token Age Filters */}
              <div className="sp-filter-row">
                <div className="sp-filter-group">
                  <label><FaHistory className="sp-filter-icon" /> Token Age Range</label>
                  <div 
                    className="sp-filter-selector" 
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setShowWalletCategoryPopup(false);
                      setShowWalletTypePopup(false);
                      setShowTokenAgePopup(!showTokenAgePopup);
                    }}
                  >
                    {filters.tokenAgeRange ? 
                      TOKEN_AGE_RANGES.find(range => range.id === filters.tokenAgeRange)?.label : 
                      'All Ages'}
                    <FaChevronDown className={`sp-filter-dropdown-icon ${showTokenAgePopup ? 'open' : ''}`} />
                  </div>
                  {showTokenAgePopup && (
                    <>
                      <div className="sp-filter-dropdown-overlay" onClick={() => setShowTokenAgePopup(false)}></div>
                      <div className="sp-filter-popup">
                        <h5>Select Token Age Range</h5>
                        <div 
                          className={`sp-filter-popup-option ${filters.tokenAgeRange === '' ? 'selected' : ''}`}
                          onClick={() => {
                            setFilters(prev => ({ ...prev, tokenAgeRange: '' }));
                            setShowTokenAgePopup(false);
                          }}
                        >
                          All Ages
                          {filters.tokenAgeRange === '' && <FaCheck className="sp-filter-check-icon" />}
                        </div>
                        {TOKEN_AGE_RANGES.map(range => (
                          <div 
                            key={range.id}
                            className={`sp-filter-popup-option ${filters.tokenAgeRange === range.id ? 'selected' : ''}`}
                            onClick={() => {
                              setFilters(prev => ({ ...prev, tokenAgeRange: range.id }));
                              setShowTokenAgePopup(false);
                            }}
                          >
                            {range.label}
                            {filters.tokenAgeRange === range.id && <FaCheck className="sp-filter-check-icon" />}
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            <div className="sp-filter-footer">
              <button 
                className="sp-filter-apply" 
                onClick={applyFilters}
              >
                <FaFilter /> Apply Filters
              </button>
            </div>
          </div>
        </>
      )}
      
      {/* Data Table */}
      <Row>
        <Col>
          <div className="strategy-table-wrapper">
            {loading ? (
              <div className="text-center py-5">
                <Spinner animation="border" role="status" variant="light">
                  <span className="visually-hidden">Loading...</span>
                </Spinner>
                <p className="mt-3 text-light">Loading report data...</p>
              </div>
            ) : error ? (
              <div className="empty-state">
                <FaExclamationTriangle className="empty-icon" />
                <h3>Error Loading Data</h3>
                <p>{error}</p>
              </div>
            ) : reportData.length === 0 ? (
              <div className="empty-state">
                <FaSearch className="empty-icon" />
                <h3>No Data Found</h3>
                <p>Try adjusting your filters or check back later for new data.</p>
              </div>
            ) : (
              <table className="strategy-table">
                <thead>
                  <tr>
                    <th>Token</th>
                    <th>Age</th>
                    <th>Smart Balance</th>
                    <th>Attention</th>
                    <th>Wallet Breakdown</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.map((item) => (
                    <tr key={item.tokenid} className="data-row">
                      <td>
                        <div className="token-cell">
                          <OverlayTrigger
                            placement="top"
                            delay={{ show: 250, hide: 400 }}
                            overlay={renderTokenIdTooltip(item.tokenid)}
                          >
                            <div 
                              className="strategy-name"
                              onClick={() => handleTokenClick(item)}
                            >
                              <span className="strategy-name-text">
                                {item.name} 
                                {copiedTokenId === item.tokenid && (
                                  <FaCheckCircle className="ms-2 text-success" />
                                )}
                              </span>
                              <span className="token-chain-badge">
                                {item.chainname}
                              </span>
                              <div className="strategy-hover-indicator"></div>
                            </div>
                          </OverlayTrigger>
                        </div>
                      </td>
                      <td>{formatTokenAge(item.tokenage)}</td>
                      <td className="numeric-cell">
                        <div className="numeric-value-wrapper">
                          <span className="numeric-value">
                            ${formatNumber(item.smartbalance)}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="attention-wrapper">
                          <span 
                            className="attention-badge"
                            style={{ backgroundColor: `${getAttentionStatusColor(item.attention_status)}20` }}
                          >
                            <span 
                              className="status-dot"
                              style={{ backgroundColor: getAttentionStatusColor(item.attention_status) }}
                            ></span>
                            <span style={{ color: getAttentionStatusColor(item.attention_status) }}>
                              {item.attention_status || 'UNKNOWN'}
                            </span>
                          </span>
                          <span className="attention-count">
                            ({item.attention_count || 0})
                          </span>
                        </div>
                      </td>
                      <td>
                        {renderWalletCategories(item)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            
            {/* Table Footer */}
            {!loading && !error && reportData.length > 0 && (
              <div className="table-footer">
                <div className="table-info">
                  Showing {reportData.length} of {totalRecords} records
                </div>
                <div className="execution-time">
                  Generated in {executionTime}s
                </div>
              </div>
            )}
          </div>
        </Col>
      </Row>
      
      {/* Wallet Invested Modal */}
      {selectedToken && showWalletModal && (
        <WalletInvestedModal 
          token={selectedToken} 
          onClose={closeWalletModal} 
        />
      )}
    </Container>
  );
};

export default SuperPortReport; 