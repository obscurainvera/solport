import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import FilterForm from './FilterForm';
import PortSummaryReportTable from './PortSummaryReportTable';
import WalletInvestedModal from './WalletInvestedModal';
import { FaFilter, FaChartLine, FaCoins, FaTimes } from 'react-icons/fa';
import './PortSummaryReport.css';

function PortSummaryReport() {
  const [filters, setFilters] = useState({});
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedToken, setSelectedToken] = useState(null);
  const [sortConfig, setSortConfig] = useState({
    sort_by: 'smartbalance',
    sort_order: 'desc'
  });

  // Define fetchData with useCallback to memoize it and avoid unnecessary re-renders
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Convert filters to snake_case for backend API, including sort config
      const apiFilters = Object.entries({ ...filters, ...sortConfig }).reduce((acc, [key, value]) => {
        if (value) {
          const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
          acc[snakeKey] = value;
        }
        return acc;
      }, {});

      // Add chainName as empty string if not provided (to maintain API compatibility)
      if (!apiFilters.chain_name) {
        apiFilters.chain_name = '';
      }

      const queryParams = new URLSearchParams(apiFilters).toString();
      
      const response = await axios.get(`http://localhost:8080/api/reports/portsummary?${queryParams}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      // Debug: Log the raw response data to verify structure
      console.log('Raw API Response:', response.data);
      console.log('Parsed Data Structure:', response.data.map(item => Object.keys(item)));

      // Ensure data structure matches expected fields
      const processedData = response.data.map(row => ({
        portsummaryid: row.portsummaryid || row.id, // Fallback if 'portsummaryid' is named differently
        chainname: row.chainname,
        tokenid: row.tokenid,
        name: row.name,
        tokenage: row.tokenage,
        mcap: row.mcap,
        avgprice: row.avgprice,
        currentprice: row.currentprice,
        pricechange: row.pricechange,
        smartbalance: row.smartbalance,
        tags: row.tags
      }));

      setData(processedData);
    } catch (err) {
      setError(err.response?.data?.message || 'An error occurred while fetching data');
      setData([]);
      console.error('Fetch Error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters, sortConfig]); // Add dependencies here

  useEffect(() => {
    fetchData();
  }, [fetchData]); // Now we only need fetchData in the dependency array

  // Add effect to check if table is scrollable
  useEffect(() => {
    const checkTableScroll = () => {
      const tableContainer = document.querySelector('.report-table-container');
      if (tableContainer) {
        if (tableContainer.scrollWidth > tableContainer.clientWidth) {
          tableContainer.classList.add('scrollable');
        } else {
          tableContainer.classList.remove('scrollable');
        }
      }
      
      // Check tag cells scrollability
      const tagCells = document.querySelectorAll('.tags-cell');
      tagCells.forEach(cell => {
        if (cell.scrollWidth > cell.clientWidth) {
          cell.classList.add('scrollable');
          // Show right indicator if there's content to scroll to
          if (cell.scrollLeft < (cell.scrollWidth - cell.clientWidth - 1)) {
            cell.classList.add('show-right-indicator');
          } else {
            cell.classList.remove('show-right-indicator');
          }
        } else {
          cell.classList.remove('scrollable', 'show-left-indicator', 'show-right-indicator');
        }
      });
    };

    // Check on initial render and when data changes
    checkTableScroll();
    
    // Also check on window resize
    window.addEventListener('resize', checkTableScroll);
    
    return () => {
      window.removeEventListener('resize', checkTableScroll);
    };
  }, [data]);

  const handleApplyFilters = (newFilters) => {
    console.log('Applying filters:', newFilters);
    setFilters(newFilters);
    setShowFilters(false);
    // fetchData will be called automatically due to the dependency in useEffect
  };

  const handleSort = (field) => {
    setSortConfig(prevConfig => {
      if (prevConfig.sort_by === field) {
        return {
          sort_by: field,
          sort_order: prevConfig.sort_order === 'asc' ? 'desc' : 'asc'
        };
      }
      // Default sort order based on field type
      let defaultOrder = 'desc';
      if (field === 'name' || field === 'tokenid' || field === 'chainname') {
        defaultOrder = 'asc';
      }
      return {
        sort_by: field,
        sort_order: defaultOrder
      };
    });
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  const handleRowClick = (row) => {
    setSelectedToken(row);
  };

  const closeModal = () => {
    setSelectedToken(null);
  };

  return (
    <div className="port-summary-container">
      <div className="port-summary-header">
        <div className="port-summary-title">
          <FaCoins className="title-icon" />
          <div>
            <h1>Portfolio Summary</h1>
            <p className="subtitle">Analyze your investments with precision</p>
          </div>
        </div>
        <div className="port-summary-actions">
          <button 
            className="filter-button" 
            onClick={toggleFilters}
            aria-label="Toggle filters"
          >
            <FaFilter /> Filters
          </button>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      <div className="port-summary-content">
        {showFilters && (
          <>
            <div className="filter-backdrop" onClick={toggleFilters}></div>
            <div className="filter-panel">
              <button className="close-filter-button" onClick={toggleFilters}>
                <FaTimes />
              </button>
              <FilterForm onApply={handleApplyFilters} initialFilters={filters} />
            </div>
          </>
        )}
        
        <div className="report-stats">
          <div className="stat-card">
            <FaChartLine className="stat-icon" />
            <div className="stat-content">
              <h3>Total Tokens</h3>
              <p>{data.length}</p>
            </div>
          </div>
          <div className="stat-card">
            <FaCoins className="stat-icon" />
            <div className="stat-content">
              <h3>Total Market Cap</h3>
              <p>{data.length > 0 ? 
                new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  maximumFractionDigits: 0
                }).format(data.reduce((sum, item) => sum + (item.mcap || 0), 0)) 
                : '$0'}
              </p>
            </div>
          </div>
        </div>

        <div className="report-container">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading report data...</p>
            </div>
          ) : error ? (
            <div className="error-message">
              <p>{error}</p>
            </div>
          ) : data.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Data Found</h3>
              <p>No portfolio data available with the current filters.</p>
            </div>
          ) : (
            <PortSummaryReportTable 
              data={data} 
              onSort={handleSort} 
              sortConfig={sortConfig}
              onRowClick={handleRowClick}
            />
          )}
        </div>
      </div>
      
      {selectedToken && (
        <WalletInvestedModal 
          token={selectedToken} 
          onClose={closeModal} 
        />
      )}
    </div>
  );
}

export default PortSummaryReport;