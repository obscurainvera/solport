import React, { useState, useEffect, useRef } from 'react';
import { FaSort, FaSortUp, FaSortDown, FaTags, FaCopy, FaCheck, FaArrowUp, FaArrowDown, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import './PortSummaryReportTable.css';

function PortSummaryReportTable({ data, onSort, sortConfig, onRowClick }) {
  const [hoveredRow, setHoveredRow] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [tagScrollStates, setTagScrollStates] = useState({});
  const tagCellRefs = useRef({});
  const tableContainerRef = useRef(null);

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
  }, [data]);

  // Check if tag cells are scrollable and update indicators
  const checkTagCellScroll = (rowId) => {
    const tagCell = tagCellRefs.current[rowId];
    if (!tagCell) return;

    const isScrollable = tagCell.scrollWidth > tagCell.clientWidth;
    const isScrolledLeft = tagCell.scrollLeft > 0;
    const isScrolledRight = tagCell.scrollLeft < (tagCell.scrollWidth - tagCell.clientWidth - 1);

    setTagScrollStates(prev => ({
      ...prev,
      [rowId]: {
        scrollable: isScrollable,
        showLeftIndicator: isScrolledLeft,
        showRightIndicator: isScrolledRight && isScrollable
      }
    }));
  };

  // Initialize scroll states when data changes
  useEffect(() => {
    // Reset refs when data changes
    tagCellRefs.current = {};
    
    // Initialize scroll states for all rows
    const initialStates = {};
    data.forEach((row) => {
      const rowId = row.portsummaryid || `row-${data.indexOf(row)}`;
      initialStates[rowId] = {
        scrollable: false,
        showLeftIndicator: false,
        showRightIndicator: false
      };
    });
    setTagScrollStates(initialStates);
    
    // Check scroll states after render
    setTimeout(() => {
      Object.keys(tagCellRefs.current).forEach(rowId => {
        checkTagCellScroll(rowId);
      });
    }, 100);
  }, [data]);

  // Handle scroll event for tag cells
  const handleTagCellScroll = (rowId) => {
    checkTagCellScroll(rowId);
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 2,
      minimumFractionDigits: 2,
    }).format(num);
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    // Handle zero values properly
    if (value === 0) return '$0.00';
    
    // For very small values (less than 0.01), use more decimal places
    if (value > 0 && value < 0.01) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
      }).format(value);
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (num) => {
    if (num === null || num === undefined) return '-';
    
    // For very small changes, just show 0
    if (Math.abs(num) < 0.1) return '0';
    
    // Format with no decimal places for maximum compactness
    const formatted = Math.round(num);
    
    // Add plus sign for positive values
    return `${num > 0 ? '+' : ''}${formatted}`;
  };

  const formatLargeNumber = (num) => {
    if (num === null || num === undefined) return '-';
    
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

  const formatTags = (tagsString) => {
    // If empty or null, return empty array
    if (!tagsString || tagsString === '[]') return [];
    
    // If it's already an array, return it
    if (Array.isArray(tagsString)) return tagsString;
    
    // If it's a string, handle it based on format
    if (typeof tagsString === 'string') {
      // First check if it looks like a comma-separated list (most common case in our data)
      if (tagsString.includes(',') && !tagsString.includes('{') && !tagsString.includes('[')) {
        const splitTags = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
        return splitTags;
      }
      
      // If not a simple comma list, try to parse as JSON
      try {
        const parsed = JSON.parse(tagsString);
        
        // Handle both array and object formats
        if (Array.isArray(parsed)) {
          return parsed;
        } else if (typeof parsed === 'object') {
          return Object.values(parsed);
        }
        
        return [];
      } catch (e) {
        // Last resort: just split by comma
        const splitTags = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
        return splitTags;
      }
    }
    
    // If we get here, return empty array
    return [];
  };

  const getSortIndicator = (key) => {
    if (sortConfig && sortConfig.sort_by === key) {
      return sortConfig.sort_order === 'asc' ? 
        <FaChevronUp className="sort-icon active" /> : 
        <FaChevronDown className="sort-icon active" />;
    }
    return <FaChevronDown className="sort-icon" />;
  };

  const handleRowHover = (id) => {
    setHoveredRow(id);
  };

  const handleRowLeave = () => {
    setHoveredRow(null);
  };

  const handleCopyTokenId = (e, tokenId) => {
    // Stop event propagation to prevent row click
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

  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <h3>No Data Available</h3>
        <p>Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  return (
    <div className="report-table-wrapper" ref={tableContainerRef}>
      <table className="report-table">
        <colgroup>
          <col style={{ width: '8%' }} /> {/* Token ID */}
          <col style={{ width: '8%' }} /> {/* Name */}
          <col style={{ width: '5%' }} /> {/* Age */}
          <col style={{ width: '10%' }} /> {/* Market Cap */}
          <col style={{ width: '7%' }} /> {/* Avg Price */}
          <col style={{ width: '7%' }} /> {/* Current Price */}
          <col style={{ width: '5%' }} /> {/* Price Change % */}
          <col style={{ width: '12%' }} /> {/* Smart Balance */}
          <col style={{ width: '39%' }} /> {/* Tags */}
        </colgroup>
        <thead>
          <tr>
            <th onClick={() => onSort('tokenid')} className="sortable">
              <div className="th-content">Token ID {getSortIndicator('tokenid')}</div>
            </th>
            <th onClick={() => onSort('name')} className="sortable">
              <div className="th-content">Name {getSortIndicator('name')}</div>
            </th>
            <th onClick={() => onSort('tokenage')} className="sortable">
              <div className="th-content">Age {getSortIndicator('tokenage')}</div>
            </th>
            <th onClick={() => onSort('mcap')} className="sortable">
              <div className="th-content">Market Cap {getSortIndicator('mcap')}</div>
            </th>
            <th onClick={() => onSort('avgprice')} className="sortable">
              <div className="th-content">Avg {getSortIndicator('avgprice')}</div>
            </th>
            <th onClick={() => onSort('currentprice')} className="sortable">
              <div className="th-content">Current {getSortIndicator('currentprice')}</div>
            </th>
            <th onClick={() => onSort('pricechange')} className="sortable" title="Percentage change from average price to current price">
              <div className="th-content">Δ% {getSortIndicator('pricechange')}</div>
            </th>
            <th onClick={() => onSort('smartbalance')} className="sortable">
              <div className="th-content">Smart Balance {getSortIndicator('smartbalance')}</div>
            </th>
            <th className="sortable">
              <div className="th-content">
                <FaTags /> Tags
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => {
            const rowId = row.portsummaryid || `row-${index}`;
            const scrollState = tagScrollStates[rowId] || { 
              scrollable: false, 
              showLeftIndicator: false, 
              showRightIndicator: false 
            };
            
            return (
              <tr 
                key={rowId}
                onMouseEnter={() => handleRowHover(rowId)}
                onMouseLeave={handleRowLeave}
                className={`${hoveredRow === rowId ? 'hovered' : ''} chain-${row.chainname?.toLowerCase() || 'unknown'} clickable-row`}
                onClick={() => onRowClick && onRowClick(row)}
                title="Click to view wallets invested in this token"
              >
                <td className="text-center">
                  <span 
                    className={`token-id ${copiedId === row.tokenid ? 'copied' : ''}`}
                    onClick={(e) => handleCopyTokenId(e, row.tokenid)}
                    title={`Click to copy: ${row.tokenid}`}
                  >
                    {row.tokenid ? row.tokenid.substring(0, 4) : '-'}
                    {copiedId === row.tokenid ? 
                      <FaCheck className="copy-icon copied" /> : 
                      <FaCopy className="copy-icon" />}
                  </span> {/* Token ID */}
                </td>
                <td className="text-center token-name">{row.name || '-'}</td> {/* Name */}
                <td className="text-center token-age">{formatNumber(row.tokenage) || '-'}</td> {/* Age */}
                <td className="text-center market-cap" title={row.mcap ? formatCurrency(row.mcap) : '-'}>
                  {formatLargeNumber(row.mcap) || '-'}
                </td> {/* Market Cap */}
                <td className="text-center avg-price">{formatCurrency(row.avgprice)}</td> {/* Avg Price */}
                <td className="text-center current-price">
                  {formatCurrency(row.currentprice)}
                </td> {/* Current Price */}
                <td className={`text-center price-change ${row.pricechange > 0 ? 'positive' : row.pricechange < 0 ? 'negative' : ''}`} title={row.pricechange !== null ? `${row.pricechange.toFixed(2)}%` : ''}>
                  {row.pricechange !== null ? (
                    <>
                      {row.pricechange > 0 ? <FaArrowUp className="change-icon up" /> : 
                       row.pricechange < 0 ? <FaArrowDown className="change-icon down" /> : '0'}
                      {Math.abs(Math.round(row.pricechange))}
                    </>
                  ) : '-'}
                </td> {/* Price Change % */}
                <td className="text-center smart-balance" title={row.smartbalance ? formatCurrency(row.smartbalance) : '-'}>
                  {formatLargeNumber(row.smartbalance) || '-'}
                </td> {/* Smart Balance */}
                <td className="text-left">
                  <div 
                    ref={el => { tagCellRefs.current[rowId] = el; }}
                    className={`tags-cell ${scrollState.scrollable ? 'scrollable' : ''} 
                              ${scrollState.showLeftIndicator ? 'show-left-indicator' : ''} 
                              ${scrollState.showRightIndicator ? 'show-right-indicator' : ''}`}
                    onScroll={() => handleTagCellScroll(rowId)}
                  >
                    {Array.isArray(row.tags) && row.tags.length > 0 ? (
                      row.tags.map((tag, i) => (
                        <span key={i} className={`tag-badge ${tag}`}>{tag}</span>
                      ))
                    ) : typeof row.tags === 'string' && row.tags.length > 0 ? (
                      formatTags(row.tags).map((tag, i) => (
                        <span key={i} className={`tag-badge ${tag}`}>{tag}</span>
                      ))
                    ) : (
                      <span className="no-tags">No tags</span>
                    )}
                  </div>
                </td> {/* Tags */}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="table-footer">
        <div className="table-info">
          Showing {data.length} {data.length === 1 ? 'result' : 'results'}
        </div>
      </div>
    </div>
  );
}

export default PortSummaryReportTable;