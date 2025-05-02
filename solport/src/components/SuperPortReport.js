import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Container, Row, Col, Card, Button, 
  Form, Spinner, Badge, Tooltip, OverlayTrigger,
  InputGroup
} from 'react-bootstrap';
import { 
  FaFilter, FaRegCopy, FaCheckCircle, FaExclamationTriangle, 
  FaHistory, FaCoins, FaUsers, FaWallet, FaTimes, FaSearch
} from 'react-icons/fa';
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
  
  // Filter states
  const [filters, setFilters] = useState({
    // Wallet breakdown filters
    walletCategory: '',
    walletType: '',
    minWalletCount: '',
    minAmountInvested: '',
    
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
      if (filterPanelRef.current && !filterPanelRef.current.contains(event.target)) {
        setShowFilters(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [filterPanelRef]);
  
  // Copy token ID to clipboard
  const copyToClipboard = (tokenId) => {
    navigator.clipboard.writeText(tokenId)
      .then(() => {
        setCopiedTokenId(tokenId);
        setTimeout(() => setCopiedTokenId(null), 2000);
      })
      .catch(err => console.error('Failed to copy:', err));
  };
  
  // Fetch report data from API
  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query parameters - only include non-empty values
      const queryParams = Object.entries(filters)
        .filter(([_, value]) => value !== '')
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&');
      
      console.log("Fetching data with params:", queryParams);
      const response = await axios.get(`/api/reports/superportreport${queryParams ? `?${queryParams}` : ''}`);
      
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
    e.preventDefault();
    fetchReportData();
    setShowFilters(false);
  };
  
  // Reset filters
  const resetFilters = () => {
    setFilters({
      // Wallet breakdown filters
      walletCategory: '',
      walletType: '',
      minWalletCount: '',
      minAmountInvested: '',
      
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
    // Prepare data for each PNL category
    const categoryData = [
      {
        name: 'No Selling',
        cat1: {
          count: item.pnl_category_1_no_withdrawal_count || 0,
          amount: item.pnl_category_1_no_withdrawal_amount || 0
        },
        cat2: {
          count: item.pnl_category_2_no_withdrawal_count || 0,
          amount: item.pnl_category_2_no_withdrawal_amount || 0
        },
        cat3: {
          count: item.pnl_category_3_no_withdrawal_count || 0,
          amount: item.pnl_category_3_no_withdrawal_amount || 0
        }
      },
      {
        name: '< 30%',
        cat1: {
          count: item.pnl_category_1_partial_withdrawal_count || 0,
          amount: item.pnl_category_1_partial_withdrawal_amount || 0
        },
        cat2: {
          count: item.pnl_category_2_partial_withdrawal_count || 0,
          amount: item.pnl_category_2_partial_withdrawal_amount || 0
        },
        cat3: {
          count: item.pnl_category_3_partial_withdrawal_count || 0,
          amount: item.pnl_category_3_partial_withdrawal_amount || 0
        }
      },
      {
        name: '> 30%',
        cat1: {
          count: item.pnl_category_1_significant_withdrawal_count || 0,
          amount: item.pnl_category_1_significant_withdrawal_amount || 0
        },
        cat2: {
          count: item.pnl_category_2_significant_withdrawal_count || 0,
          amount: item.pnl_category_2_significant_withdrawal_amount || 0
        },
        cat3: {
          count: item.pnl_category_3_significant_withdrawal_count || 0,
          amount: item.pnl_category_3_significant_withdrawal_amount || 0
        }
      }
    ];
    
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
            {categoryData.map((row, index) => (
              <tr key={index}>
                <td className="category-name">{row.name}</td>
                <td>
                  <div className="wallet-count-amount">
                    <span className="wallet-count">{row.cat1.count}</span>
                    <span className="wallet-separator">·</span>
                    <span className="wallet-amount">{formatCompactAmount(row.cat1.amount)}</span>
                  </div>
                </td>
                <td>
                  <div className="wallet-count-amount">
                    <span className="wallet-count">{row.cat2.count}</span>
                    <span className="wallet-separator">·</span>
                    <span className="wallet-amount">{formatCompactAmount(row.cat2.amount)}</span>
                  </div>
                </td>
                <td>
                  <div className="wallet-count-amount">
                    <span className="wallet-count">{row.cat3.count}</span>
                    <span className="wallet-separator">·</span>
                    <span className="wallet-amount">{formatCompactAmount(row.cat3.amount)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <Container fluid className="superport-report px-4 py-3">
      <Row className="mb-4">
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
        <Row className="mb-4">
          <Col>
            <Card className="filter-panel" ref={filterPanelRef}>
              <Card.Body>
                <Form onSubmit={applyFilters}>
                  {/* Wallet Breakdown Filters */}
                  <div className="filter-section">
                    <h6 className="filter-section-title"><FaUsers /> Wallet Breakdown Filters</h6>
                    <Row className="g-3">
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Category</Form.Label>
                          <Form.Select
                            name="walletCategory"
                            value={filters.walletCategory}
                            onChange={handleFilterChange}
                          >
                            <option value="">All Categories</option>
                            <option value="0-300K">0-300K</option>
                            <option value="300K-1M">300K-1M</option>
                            <option value=">1M">Greater than 1M</option>
                          </Form.Select>
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Type</Form.Label>
                          <Form.Select
                            name="walletType"
                            value={filters.walletType}
                            onChange={handleFilterChange}
                          >
                            <option value="">All Types</option>
                            <option value="no-selling">No Selling</option>
                            <option value="<30%">Less than 30%</option>
                            <option value=">30%">Greater than 30%</option>
                          </Form.Select>
                        </Form.Group>
                      </Col>
                    </Row>
                    <Row className="g-3 mt-1">
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Minimum Number of Wallets</Form.Label>
                          <Form.Control
                            type="number"
                            name="minWalletCount"
                            value={filters.minWalletCount}
                            onChange={handleFilterChange}
                            placeholder="Enter minimum wallets"
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Minimum Amount Invested</Form.Label>
                          <InputGroup>
                            <InputGroup.Text>$</InputGroup.Text>
                            <Form.Control
                              type="number"
                              name="minAmountInvested"
                              value={filters.minAmountInvested}
                              onChange={handleFilterChange}
                              placeholder="Enter minimum amount"
                            />
                          </InputGroup>
                        </Form.Group>
                      </Col>
                    </Row>
                  </div>
                  
                  <div className="filter-actions">
                    <Button 
                      variant="secondary" 
                      onClick={resetFilters}
                    >
                      <FaTimes className="me-1" /> Reset
                    </Button>
                    <Button 
                      variant="primary" 
                      type="submit"
                    >
                      <FaFilter className="me-1" /> Apply
                    </Button>
                  </div>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>
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
                              onClick={() => copyToClipboard(item.tokenid)}
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
    </Container>
  );
};

export default SuperPortReport; 