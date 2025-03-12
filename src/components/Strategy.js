import React, { useState } from 'react';
import { FaHome, FaChartBar, FaTags, FaRobot, FaUpload, FaTimes } from 'react-icons/fa';
import './Strategy.css';

function Strategy() {
  // State for loading spinners and status messages
  const [portfolioTaggingLoading, setPortfolioTaggingLoading] = useState(false);
  const [singleTokenLoading, setSingleTokenLoading] = useState(false);
  const [monitoringLoading, setMonitoringLoading] = useState(false);
  const [pushTokenLoading, setPushTokenLoading] = useState(false);
  
  const [portfolioStatus, setPortfolioStatus] = useState({ message: '', isError: false, visible: false });
  const [monitoringStatus, setMonitoringStatus] = useState({ message: '', isError: false, visible: false });
  const [pushTokenStatus, setPushTokenStatus] = useState({ message: '', isError: false, visible: false });
  
  const [tokenId, setTokenId] = useState('');
  const [evaluateTokenId, setEvaluateTokenId] = useState('');
  const [sourceType, setSourceType] = useState('');

  // Handler functions
  const tagAllPortfolioTokens = () => {
    setPortfolioTaggingLoading(true);
    setPortfolioStatus({ message: '', isError: false, visible: false });
    
    // Simulate API call
    setTimeout(() => {
      setPortfolioTaggingLoading(false);
      setPortfolioStatus({
        message: 'Successfully tagged all portfolio tokens!',
        isError: false,
        visible: true
      });
    }, 2000);
  };

  const tagAParticularPortfolioToken = () => {
    if (!evaluateTokenId) {
      setPortfolioStatus({
        message: 'Please enter a Token ID',
        isError: true,
        visible: true
      });
      return;
    }
    
    setSingleTokenLoading(true);
    setPortfolioStatus({ message: '', isError: false, visible: false });
    
    // Simulate API call
    setTimeout(() => {
      setSingleTokenLoading(false);
      setPortfolioStatus({
        message: 'Token tags updated successfully!',
        isError: false,
        visible: true
      });
    }, 2000);
  };

  const triggerExecutionMonitoring = () => {
    setMonitoringLoading(true);
    setMonitoringStatus({ message: '', isError: false, visible: false });
    
    // Simulate API call
    setTimeout(() => {
      setMonitoringLoading(false);
      setMonitoringStatus({
        message: 'Monitoring completed successfully! Processed 24 executions, 5 profit targets hit, 2 stop losses triggered in 3.2s.',
        isError: false,
        visible: true
      });
    }, 2000);
  };

  const pushTokenToAnalytics = () => {
    if (!tokenId || !sourceType) {
      setPushTokenStatus({
        message: 'Please enter both Token ID and Source Type',
        isError: true,
        visible: true
      });
      return;
    }
    
    setPushTokenLoading(true);
    setPushTokenStatus({ message: '', isError: false, visible: false });
    
    // Simulate API call
    setTimeout(() => {
      setPushTokenLoading(false);
      setPushTokenStatus({
        message: 'Token successfully pushed to analytics framework!',
        isError: false,
        visible: true
      });
    }, 2000);
  };

  return (
    <div className="strategy-container">
      <div className="strategy-header">
        <div className="strategy-title">
          <h1>Strategy Operations</h1>
        </div>
        <p className="subtitle">Manage portfolio tagging, execution monitoring, and analytics integration</p>
      </div>

      <div className="strategy-content">
        <div className="strategy-section">
          <div className="section-grid">
            {/* Portfolio Tagger Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Portfolio Tagger</h2>
                <p>Tag and evaluate portfolio tokens</p>
              </div>
              <div className="card-content">
                <button 
                  className="luxury-button" 
                  onClick={tagAllPortfolioTokens}
                  disabled={portfolioTaggingLoading}
                >
                  Tag All Portfolio Tokens
                  {portfolioTaggingLoading && <span className="loading-spinner"></span>}
                </button>
                
                <div className="input-group">
                  <input 
                    type="text" 
                    className="luxury-input" 
                    placeholder="Token ID"
                    value={evaluateTokenId}
                    onChange={(e) => setEvaluateTokenId(e.target.value)}
                  />
                  <button 
                    className="luxury-button" 
                    onClick={tagAParticularPortfolioToken}
                    disabled={singleTokenLoading}
                  >
                    Tag A Particular Token
                    {singleTokenLoading && <span className="loading-spinner"></span>}
                  </button>
                </div>
                
                {portfolioStatus.visible && (
                  <div className={`status-message ${portfolioStatus.isError ? 'error' : 'success'}`}>
                    {portfolioStatus.message}
                    <button className="close-status" onClick={() => setPortfolioStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Execution Monitor Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Execution Monitor</h2>
                <p>Manually trigger monitoring of active strategy executions</p>
              </div>
              <div className="card-content">
                <button 
                  className="luxury-button" 
                  onClick={triggerExecutionMonitoring}
                  disabled={monitoringLoading}
                >
                  Trigger Execution Monitoring
                  {monitoringLoading && <span className="loading-spinner"></span>}
                </button>
                
                {monitoringStatus.visible && (
                  <div className={`status-message ${monitoringStatus.isError ? 'error' : 'success'}`}>
                    {monitoringStatus.message}
                    <button className="close-status" onClick={() => setMonitoringStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Push Token Card */}
            <div className="strategy-card">
              <div className="card-header">
                <h2>Push Token To Analytics</h2>
                <p>Push token data to analytics framework for analysis</p>
              </div>
              <div className="card-content">
                <div className="input-group">
                  <input 
                    type="text" 
                    className="luxury-input" 
                    placeholder="Token ID"
                    value={tokenId}
                    onChange={(e) => setTokenId(e.target.value)}
                  />
                </div>
                
                <div className="input-group">
                  <select 
                    className="luxury-input" 
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                  >
                    <option value="">Select Source Type</option>
                    <option value="PORTSUMMARY">Port Summary</option>
                    <option value="ATTENTION">Attention</option>
                    <option value="SMARTMONEY">Smart Money</option>
                    <option value="VOLUME">Volume</option>
                    <option value="PUMPFUN">Pump Fun</option>
                  </select>
                </div>
                
                <button 
                  className="luxury-button" 
                  onClick={pushTokenToAnalytics}
                  disabled={pushTokenLoading}
                >
                  Push Token To Analytics
                  {pushTokenLoading && <span className="loading-spinner"></span>}
                </button>
                
                {pushTokenStatus.visible && (
                  <div className={`status-message ${pushTokenStatus.isError ? 'error' : 'success'}`}>
                    {pushTokenStatus.message}
                    <button className="close-status" onClick={() => setPushTokenStatus(prev => ({...prev, visible: false}))}>
                      <FaTimes />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Strategy; 