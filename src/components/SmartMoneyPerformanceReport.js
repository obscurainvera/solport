import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import SmartMoneyPerformanceFilterForm from './SmartMoneyPerformanceFilterForm';
import SmartMoneyPerformanceTable from './SmartMoneyPerformanceTable';
import { FaFilter, FaChartLine, FaCoins, FaTimes, FaWallet, FaExchangeAlt } from 'react-icons/fa';
import './SmartMoneyPerformanceReport.css';

function SmartMoneyPerformanceReport() {
  const [filters, setFilters] = useState({});
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [sortConfig, setSortConfig] = useState({
    sort_by: 'profitandloss',
    sort_order: 'desc'
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const apiFilters = Object.entries({ ...filters, ...sortConfig }).reduce((acc, [key, value]) => {
        if (value) {
          const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
          acc[snakeKey] = value;
        }
        return acc;
      }, {});

      const queryParams = new URLSearchParams(apiFilters).toString();
      
      const response = await axios.get(`http://localhost:8080/api/reports/smartmoneyperformance?${queryParams}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      console.log('Raw API Response:', response.data);
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'An error occurred while fetching data');
      setData([]);
      console.error('Fetch Error:', err);
    } finally {
      setLoading(false);
    }
  }, [filters, sortConfig]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleApplyFilters = (newFilters) => {
    console.log('Applying filters:', newFilters);
    setFilters(newFilters);
    setShowFilters(false);
  };

  const handleSort = (field) => {
    setSortConfig(prevConfig => {
      if (prevConfig.sort_by === field) {
        return {
          sort_by: field,
          sort_order: prevConfig.sort_order === 'asc' ? 'desc' : 'asc'
        };
      }
      let defaultOrder = 'desc';
      if (field === 'walletaddress') {
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

  const totalWallets = data.length;
  const totalProfitAndLoss = data.reduce((sum, wallet) => sum + (wallet.profitandloss || 0), 0);
  const averageWinRate = data.length > 0 
    ? data.reduce((sum, wallet) => sum + (wallet.winrate || 0), 0) / data.length 
    : 0;

  return (
    <div className="sm-performance-report-container">
      <div className="sm-performance-report-header">
        <div className="sm-performance-report-title">
          <FaWallet className="sm-title-icon" />
          <div>
            <h1>Smart Money Performance</h1>
            <p className="sm-subtitle">Analyze smart money wallet performance metrics</p>
          </div>
        </div>
        <div className="sm-performance-report-actions">
          <button 
            className="sm-filter-button" 
            onClick={toggleFilters}
            aria-label="Toggle filters"
          >
            <FaFilter /> Filters
          </button>
        </div>
      </div>
      
      {error && (
        <div className="sm-error-message">
          <p>{error}</p>
        </div>
      )}

      <div className="sm-performance-report-content">
        {showFilters && (
          <>
            <div className="sm-filter-backdrop" onClick={toggleFilters}></div>
            <div className="sm-filter-panel">
              <button className="sm-close-filter-button" onClick={toggleFilters}>
                <FaTimes />
              </button>
              <SmartMoneyPerformanceFilterForm onApply={handleApplyFilters} initialFilters={filters} />
            </div>
          </>
        )}
        
        <div className="sm-report-stats">
          <div className="sm-stat-card">
            <FaWallet className="sm-stat-icon" />
            <div className="sm-stat-content">
              <h3>Total Wallets</h3>
              <p>{totalWallets}</p>
            </div>
          </div>
          <div className="sm-stat-card">
            <FaCoins className="sm-stat-icon" />
            <div className="sm-stat-content">
              <h3>Total Profit & Loss</h3>
              <p className={totalProfitAndLoss >= 0 ? 'positive' : 'negative'}>
                {totalProfitAndLoss > 0 ? '+' : ''}
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  maximumFractionDigits: 0
                }).format(totalProfitAndLoss)}
              </p>
            </div>
          </div>
          <div className="sm-stat-card">
            <FaExchangeAlt className="sm-stat-icon" />
            <div className="sm-stat-content">
              <h3>Average Win Rate</h3>
              <p>{Math.round(averageWinRate)}%</p>
            </div>
          </div>
        </div>

        <div className="sm-report-container">
          {loading ? (
            <div className="sm-loading-container">
              <div className="sm-loading-spinner"></div>
              <p>Loading report data...</p>
            </div>
          ) : error ? (
            <div className="sm-error-message">
              <p>{error}</p>
            </div>
          ) : data.length === 0 ? (
            <div className="sm-empty-state">
              <div className="sm-empty-icon">🔍</div>
              <h3>No Data Found</h3>
              <p>No smart money wallet data available with the current filters.</p>
            </div>
          ) : (
            <SmartMoneyPerformanceTable 
              data={data} 
              onSort={handleSort} 
              sortConfig={sortConfig}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default SmartMoneyPerformanceReport;