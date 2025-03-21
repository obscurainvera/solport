import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Container, Row, Col, Form, Button, Spinner } from 'react-bootstrap';
import AttentionTable from './AttentionTable';
import './AttentionReport.css';

const AttentionReport = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [attentionData, setAttentionData] = useState([]);
  const [filters, setFilters] = useState({
    tokenName: '',
    chain: '',
    status: '',
    minCount: ''
  });

  useEffect(() => {
    fetchAttentionData();
  }, []);

  const fetchAttentionData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/reports/attention', {
        params: {
          name: filters.tokenName || undefined,
          chain: filters.chain || undefined,
          currentStatus: filters.status || undefined,
          minAttentionCount: filters.minCount || undefined,
        }
      });
      setAttentionData(response.data);
    } catch (err) {
      console.error('Error fetching attention data:', err);
      setError('Failed to load attention data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Extract unique chains from API data
  const uniqueChains = useMemo(() => {
    if (!attentionData || attentionData.length === 0) return [];
    
    // Get unique chain values
    const chains = [...new Set(attentionData.map(item => item.chain))];
    
    // Sort chains alphabetically
    return chains.sort((a, b) => a.localeCompare(b));
  }, [attentionData]);

  // Extract unique status values from API data
  const uniqueStatuses = useMemo(() => {
    if (!attentionData || attentionData.length === 0) return [];
    
    // Get unique currentStatus values
    const statuses = [...new Set(attentionData.map(item => item.currentStatus))];
    
    // Sort statuses alphabetically
    return statuses.sort((a, b) => a.localeCompare(b));
  }, [attentionData]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchAttentionData();
  };

  const clearFilters = () => {
    setFilters({
      tokenName: '',
      chain: '',
      status: '',
      minCount: ''
    });
  };

  const renderFilters = () => {
    return (
      <Form onSubmit={handleSubmit} className="attention-filters">
        <Row>
          <Col md={3}>
            <Form.Group className="mb-0">
              <Form.Label>Token Name</Form.Label>
              <Form.Control
                type="text"
                name="tokenName"
                value={filters.tokenName}
                onChange={handleFilterChange}
                placeholder="Search by name"
                className="attention-input"
              />
            </Form.Group>
          </Col>
          <Col md={3}>
            <Form.Group className="mb-0">
              <Form.Label>Chain</Form.Label>
              <Form.Select
                name="chain"
                value={filters.chain}
                onChange={handleFilterChange}
                className="attention-input"
              >
                <option value="">All Chains</option>
                {uniqueChains.map(chain => (
                  <option key={chain} value={chain.toLowerCase()}>
                    {chain === 'eth' ? 'Ethereum' : 
                     chain === 'sol' ? 'Solana' : 
                     chain === 'bsc' ? 'BSC' :
                     chain === 'arb' ? 'Arbitrum' :
                     chain === 'poly' ? 'Polygon' :
                     chain.charAt(0).toUpperCase() + chain.slice(1)}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={2}>
            <Form.Group className="mb-0">
              <Form.Label>Status</Form.Label>
              <Form.Select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="attention-input"
              >
                <option value="">All Statuses</option>
                {uniqueStatuses.map(status => (
                  <option key={status} value={status.toLowerCase()}>
                    {status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={2}>
            <Form.Group className="mb-0">
              <Form.Label>Min. Count</Form.Label>
              <Form.Control
                type="number"
                name="minCount"
                min="0"
                value={filters.minCount}
                onChange={handleFilterChange}
                placeholder="Min count"
                className="attention-input"
              />
            </Form.Group>
          </Col>
          <Col md={2}>
            <Form.Group className="mb-0">
              <Form.Label style={{ visibility: "hidden" }}>Actions</Form.Label>
              <div className="d-flex w-100 gap-2">
                <Button variant="primary" type="submit" className="attention-button">
                  Apply
                </Button>
                <Button variant="outline-secondary" onClick={clearFilters} className="attention-button-outline">
                  Clear
                </Button>
              </div>
            </Form.Group>
          </Col>
        </Row>
      </Form>
    );
  };

  return (
    <div className="attention-container">
      <div className="attention-background"></div>
      <Container fluid className="px-4">
        <div className="attention-header">
          <h1 className="attention-title">Attention Report</h1>
          <p className="attention-subtitle">
            Track and analyze token attention metrics across different chains
          </p>
        </div>

        {renderFilters()}

        {loading ? (
          <div className="attention-loading">
            <Spinner animation="border" role="status" variant="light" />
            <p>Loading attention data...</p>
          </div>
        ) : error ? (
          <div className="attention-error">
            <i className="fas fa-exclamation-triangle me-2"></i>
            {error}
          </div>
        ) : (
          <AttentionTable data={attentionData} />
        )}
      </Container>
    </div>
  );
};

export default AttentionReport; 