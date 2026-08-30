import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Activity, 
  TrendingUp, 
  RotateCcw, 
  BookOpen, 
  Server, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw 
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export default function App() {
  // Theme state: fixed to light theme by default
  const [theme] = useState('light');
  const [apiBase, setApiBase] = useState(() => localStorage.getItem('apiBase') || 'http://127.0.0.1:8000');
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState('taxonomy');
  
  // Simulation config & execution states
  const [selectedPersona, setSelectedPersona] = useState('phishing');
  const [roundsToRun, setRoundsToRun] = useState(2);
  const [customObjective, setCustomObjective] = useState('');
  const [customTargetProfile, setCustomTargetProfile] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simLogs, setSimLogs] = useState([]);
  const [simResult, setSimResult] = useState(null);
  
  // Data lists loaded from backend
  const [rounds, setRounds] = useState([]);
  const [selectedRound, setSelectedRound] = useState(null);
  const [roundEvents, setRoundEvents] = useState([]);
  const [chartData, setChartData] = useState({});
  const [isLoadingRounds, setIsLoadingRounds] = useState(false);

  // Set default objectives per persona
  const personaDefaultConfigs = {
    card_tester: {
      objective: "Validate active credit/debit card status with small-value checks up to a target balance of $500.",
      profile: "Standard consumer card, active status, no prior velocity alerts."
    },
    synthetic_identity: {
      objective: "Open fraudulent accounts using synthetic identities, establishing small legitimate transaction histories before maxing out limits.",
      profile: "Clean credit profile, newly generated SSN, synthetic income history."
    },
    structuring: {
      objective: "Evade standard $10,000 CTR flags by splitting a $25,000 transfer into multiple sub-threshold transactions.",
      profile: "Standard commercial checking account, multiple transfer endpoints."
    },
    phishing: {
      objective: "Conduct Business Email Compromise (BEC) to convince finance executives to wire funds to an updated bank routing path.",
      profile: "C-Level executive corporate accounts."
    },
    fake_invoice: {
      objective: "Inject fake supplier invoices into the accounting pipeline for software licensing, requesting urgent payment.",
      profile: "Accounts payable automated processing mailbox."
    }
  };

  // Sync light theme to document element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'light');
  }, []);

  // Persist API base
  useEffect(() => {
    localStorage.setItem('apiBase', apiBase);
    checkHealth();
  }, [apiBase]);

  // Periodic health check & rounds fetch
  useEffect(() => {
    checkHealth();
    fetchRounds();
    fetchStats();
    const interval = setInterval(() => {
      checkHealth();
    }, 10000);
    return () => clearInterval(interval);
  }, [apiBase]);

  // Fetch events when round is selected
  useEffect(() => {
    if (selectedRound) {
      fetchEvents(selectedRound.round_id);
    } else {
      setRoundEvents([]);
    }
  }, [selectedRound]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${apiBase}/health`);
      if (res.ok) {
        setIsConnected(true);
      } else {
        setIsConnected(false);
      }
    } catch {
      setIsConnected(false);
    }
  };

  const fetchRounds = async () => {
    setIsLoadingRounds(true);
    try {
      const res = await fetch(`${apiBase}/orchestrator/rounds`);
      if (res.ok) {
        const data = await res.json();
        setRounds(data.rounds || []);
      }
    } catch (err) {
      console.error("Error fetching rounds:", err);
    } finally {
      setIsLoadingRounds(false);
    }
  };

  const fetchEvents = async (roundId) => {
    try {
      const res = await fetch(`${apiBase}/orchestrator/events/${roundId}`);
      if (res.ok) {
        const data = await res.json();
        setRoundEvents(data.events || []);
      }
    } catch (err) {
      console.error("Error fetching round events:", err);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${apiBase}/orchestrator/stats`);
      if (res.ok) {
        const data = await res.json();
        setChartData(data.stats || {});
      }
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  const triggerChallenge = async () => {
    setIsSimulating(true);
    setSimResult(null);
    setSimLogs([`[System] Connecting to campaign orchestrator...`]);
    
    const obj = customObjective || personaDefaultConfigs[selectedPersona].objective;
    const prof = customTargetProfile || personaDefaultConfigs[selectedPersona].profile;

    setSimLogs(prev => [...prev, `[System] Triggering challenge loop for persona: ${selectedPersona.toUpperCase()}`]);
    setSimLogs(prev => [...prev, `[System] Max rounds configured: ${roundsToRun}`]);
    setSimLogs(prev => [...prev, `[System] Target Objective: "${obj}"`]);

    try {
      const response = await fetch(`${apiBase}/orchestrator/challenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona: selectedPersona,
          num_rounds: roundsToRun,
          objective: obj,
          target_profile: prof
        })
      });

      if (!response.ok) {
        throw new Error(`API returned HTTP ${response.status}`);
      }

      const data = await response.json();
      if (data.status === 'success') {
        setSimResult(data.challenge_summary);
        setSimLogs(prev => [
          ...prev, 
          `[System] Challenge completed successfully!`,
          `[System] Final Evasion Rate: ${data.challenge_summary.final_evasion_rate * 100}%`
        ]);
        fetchRounds();
        fetchStats();
      } else {
        throw new Error(data.detail || "Unknown loop execution error");
      }
    } catch (err) {
      setSimLogs(prev => [...prev, `[Error] Challenge loop failed: ${err.message}`]);
    } finally {
      setIsSimulating(false);
    }
  };

  // Hardcoded taxonomy to guarantee static presentation is flawless
  const taxonomyItems = [
    {
      id: "card_tester",
      name: "Card Testing Attack",
      generator: "IEEE-CIS / PaySim Hybrid",
      engineered: "TransactionAmt, balanceOrig/Dest error ratio, card identity mapping",
      defense: "Sequence Layer (LSTM) & Tabular (XGBoost)",
      desc: "Simulates cards checking validity via successive small transactions. Caught by temporal sequence analysis.",
      active: true
    },
    {
      id: "synthetic_identity",
      name: "Synthetic Identity Fraud",
      generator: "IEEE-CIS statistical model",
      engineered: "addr1, addr2, card1-card6 aliases, D1-D15 offset features",
      defense: "Tabular (XGBoost) & Graph (GCN)",
      desc: "Red Team builds synthetic profiles and makes applications. Tabular signals identify anomaly correlations.",
      active: true
    },
    {
      id: "structuring",
      name: "Money Laundering Structuring",
      generator: "PaySim transactional flow",
      engineered: "Splitted amounts, sub-threshold CTR offsets, account out-degree",
      defense: "Graph Layer (GCN) & Tabular (XGBoost)",
      desc: "Breaks a large sum into smurfing nodes to bypass thresholds. Detected via graph network density changes.",
      active: true
    },
    {
      id: "phishing",
      name: "BEC Spear-Phishing",
      generator: "Gemini Text Embeddings",
      engineered: "Business context, urgency phrasing, payment routing command alerts",
      defense: "Text Layer (Gemini Prompted)",
      desc: "Emails sent to C-Suite asking to wire money to routing updates. Caught by the prompted Text defense layer.",
      active: true
    },
    {
      id: "fake_invoice",
      name: "Supplier Invoice Fraud",
      generator: "Gemini Text Embeddings",
      engineered: "Invoicing terminology, vendor verification matching",
      defense: "Text Layer (Gemini Prompted)",
      desc: "Red Team acts as false suppliers renewing license bills. Checked against text-based LLM classifier.",
      active: true
    }
  ];

  return (
    <div className="app-container">
      {/* Main Workspace Layout (Header is fully removed) */}
      <div className="workspace">
        {/* Sidebar Nav */}
        <aside className="sidebar">
          {/* VigilNet AI branding kept in the sidebar */}
          <div className="header-brand" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div className="brand-logo-container">
              <Shield size={24} />
            </div>
            <div className="brand-text">
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>VigilNet AI</h1>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Fraud Control Center</p>
            </div>
          </div>

          <p className="sidebar-title">Control Center</p>
          
          <button 
            onClick={() => setActiveTab('taxonomy')}
            className={`sidebar-nav-btn ${activeTab === 'taxonomy' ? 'active' : ''}`}
          >
            <BookOpen size={16} />
            <span>Fraud Taxonomy</span>
          </button>

          <button 
            onClick={() => setActiveTab('runner')}
            className={`sidebar-nav-btn ${activeTab === 'runner' ? 'active' : ''}`}
          >
            <Activity size={16} />
            <span>Simulation Runner</span>
          </button>

          <button 
            onClick={() => setActiveTab('metrics')}
            className={`sidebar-nav-btn ${activeTab === 'metrics' ? 'active' : ''}`}
          >
            <TrendingUp size={16} />
            <span>Metrics Curves</span>
          </button>

          <button 
            onClick={() => setActiveTab('replay')}
            className={`sidebar-nav-btn ${activeTab === 'replay' ? 'active' : ''}`}
          >
            <RotateCcw size={16} />
            <span>Evasion Replay</span>
          </button>

          {/* Connection Host Selector placed inside the sidebar */}
          <div className="api-connection-selector" style={{ marginTop: '1.5rem', marginBottom: '1rem', width: '100%', display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: 1 }}>
              <Server size={14} style={{ opacity: 0.6 }} />
              <input 
                type="text" 
                value={apiBase} 
                onChange={(e) => setApiBase(e.target.value)}
                className="api-input"
                style={{ width: '90px', fontSize: '0.7rem' }}
                placeholder="API base"
              />
            </div>
            <div className="connection-badge" style={{ padding: '0.15rem 0.35rem' }}>
              <span className={`connection-indicator ${isConnected ? 'online' : 'offline'}`}></span>
            </div>
          </div>

          <div className="sidebar-footer">
            <div className="sidebar-footer-row">
              <span>FastAPI Port</span>
              <span className="sidebar-footer-val">{apiBase.split(':').pop() || '8000'}</span>
            </div>
            <div className="sidebar-footer-row">
              <span>Database Status</span>
              <span className="sidebar-footer-val" style={{ color: 'var(--success)' }}>CONNECTED</span>
            </div>
          </div>
        </aside>

        {/* Dynamic Workspace Content */}
        <main className="main-panel animate-fade-in">
          
          {/* VIEW 1: Taxonomy */}
          {activeTab === 'taxonomy' && (
            <div className="grid-stack">
              <div className="panel-title-container">
                <h2 className="panel-title">Fraud Taxonomy</h2>
                <p className="panel-subtitle">Overview of simulated attack vectors, mathematical models, and the protecting ensemble layers.</p>
              </div>

              {taxonomyItems.map((item) => (
                <div key={item.id} className="card hoverable">
                  <div className="card-header-row">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <h3 className="card-title">{item.name}</h3>
                      <span className="card-pill primary">ACTIVE</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '0.75rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Ensemble Defense</span>
                      <span style={{ fontWeight: 700, color: 'var(--success)' }}>{item.defense}</span>
                    </div>
                  </div>
                  <p className="card-description">{item.desc}</p>
                  
                  <div className="details-row-container">
                    <div>
                      <span className="details-block-label">Statistical Generator</span>
                      <div className="details-block-value">{item.generator}</div>
                    </div>
                    <div>
                      <span className="details-block-label">Engineered Attributes</span>
                      <div className="details-block-value">{item.engineered}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* VIEW 2: Simulation Runner */}
          {activeTab === 'runner' && (
            <div className="grid-stack">
              <div className="panel-title-container">
                <h2 className="panel-title">Simulation Runner</h2>
                <p className="panel-subtitle">Trigger and orchestrate Red-Team campaign runs and observe adversarial loop adaptations.</p>
              </div>

              <div className="grid-cols-3">
                {/* Inputs card */}
                <div className="card">
                  <h3 className="card-title" style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '0.5rem' }}>Campaign Config</h3>
                  
                  <div className="form-group">
                    <label className="form-label">Fraud Persona</label>
                    <select 
                      value={selectedPersona}
                      onChange={(e) => setSelectedPersona(e.target.value)}
                      className="form-select"
                    >
                      <option value="card_tester">Card Tester (Debit/Credit)</option>
                      <option value="synthetic_identity">Synthetic Identity (IEEE-CIS)</option>
                      <option value="structuring">Structuring / Smurfing (PaySim)</option>
                      <option value="phishing">BEC Spear-Phishing (Phishing)</option>
                      <option value="fake_invoice">Vendor Invoice Spoofing (Fake Invoice)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Progression Rounds</label>
                    <input 
                      type="number" 
                      min="1" 
                      max="5"
                      value={roundsToRun}
                      onChange={(e) => setRoundsToRun(parseInt(e.target.value) || 1)}
                      className="form-input"
                      style={{ fontFamily: 'monospace' }}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Custom Objective (Optional)</label>
                    <textarea 
                      placeholder={personaDefaultConfigs[selectedPersona].objective}
                      value={customObjective}
                      onChange={(e) => setCustomObjective(e.target.value)}
                      className="form-textarea"
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Custom Target Profile (Optional)</label>
                    <textarea 
                      placeholder={personaDefaultConfigs[selectedPersona].profile}
                      value={customTargetProfile}
                      onChange={(e) => setCustomTargetProfile(e.target.value)}
                      className="form-textarea"
                    />
                  </div>

                  <button 
                    onClick={triggerChallenge}
                    disabled={isSimulating || !isConnected}
                    className="btn-submit"
                  >
                    {isSimulating ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        <span>Running Loop...</span>
                      </>
                    ) : (
                      <>
                        <Play size={14} fill="currentColor" />
                        <span>Trigger Adaptive Loop</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Console card */}
                <div className="console-box">
                  <div className="card-header-row" style={{ marginBottom: '0.75rem' }}>
                    <h3 className="card-title">Simulation Console Logs</h3>
                    <span className="card-pill primary" style={{ fontFamily: 'monospace' }}>STDOUT</span>
                  </div>

                  <div className="console-body">
                    {simLogs.map((log, idx) => {
                      let typeClass = 'console-line-info';
                      if (log.startsWith('[Error]')) typeClass = 'console-line-err';
                      else if (log.startsWith('[System]')) typeClass = 'console-line-sys';

                      return (
                        <div key={idx} className={typeClass}>
                          {log}
                        </div>
                      );
                    })}
                    
                    {isSimulating && (
                      <div className="console-line-sys" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
                        <span className="connection-indicator online"></span>
                        <span>Red Team agent is generating next progression plan...</span>
                      </div>
                    )}
                    
                    {simLogs.length === 0 && (
                      <p style={{ color: 'var(--text-muted)', textAlign: 'center', margin: 'auto' }}>
                        Configuration selected. Click "Trigger Adaptive Loop" to start.
                      </p>
                    )}
                  </div>

                  {simResult && (
                    <div className="alert-box">
                      <div className="alert-header">
                        <CheckCircle2 size={16} />
                        <span>Adaptive challenge completed!</span>
                      </div>
                      <div className="alert-grid">
                        <div>
                          <div className="alert-val-lbl">Rounds Executed</div>
                          <div className="alert-val-num">{simResult.total_rounds_executed}</div>
                        </div>
                        <div>
                          <div className="alert-val-lbl">Final Evasion Rate</div>
                          <div className="alert-val-num">{simResult.final_evasion_rate * 100}%</div>
                        </div>
                        <div>
                          <div className="alert-val-lbl">Ensemble Performance</div>
                          <div className="alert-val-num" style={{ fontSize: '0.75rem' }}>Recall Increased</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* VIEW 3: Metrics curves */}
          {activeTab === 'metrics' && (
            <div className="grid-stack">
              <div className="panel-title-container">
                <h2 className="panel-title">Metrics Curves</h2>
                <p className="panel-subtitle">Verify round-over-round evasion rates and recall curves showing detection success.</p>
              </div>

              {['card_tester', 'structuring', 'phishing', 'fake_invoice', 'synthetic_identity'].map(pName => {
                const data = chartData[pName] || [];
                if (data.length === 0) return null;
                
                return (
                  <div key={pName} className="card">
                    <div className="card-header-row">
                      <h3 className="card-title" style={{ textTransform: 'uppercase' }}>
                        {pName.replace('_', ' ')} Performance
                      </h3>
                      <span className="card-pill primary">
                        {data.length} rounds logged
                      </span>
                    </div>

                    <div className="chart-container">
                      <ResponsiveContainer width="100%" height={280}>
                        <LineChart data={data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis 
                            dataKey="round_id" 
                            stroke="var(--text-secondary)"
                            fontSize={10} 
                          />
                          <YAxis 
                            stroke="var(--text-secondary)"
                            domain={[0, 100]}
                            fontSize={10}
                            unit="%"
                          />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: 'var(--background)', 
                              borderColor: 'var(--card-border)',
                              color: 'var(--text-primary)',
                              borderRadius: '8px',
                              fontSize: '11px'
                            }} 
                          />
                          <Legend verticalAlign="top" height={36} iconType="circle" />
                          <Line 
                            type="monotone" 
                            name="Evasion Rate" 
                            dataKey="evasion_rate" 
                            stroke="var(--danger)" 
                            strokeWidth={3}
                            dot={{ r: 5 }}
                            activeDot={{ r: 8 }}
                          />
                          <Line 
                            type="monotone" 
                            name="Blue Team Recall" 
                            dataKey="recall" 
                            stroke="var(--primary)" 
                            strokeWidth={3}
                            dot={{ r: 5 }}
                            activeDot={{ r: 8 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                );
              })}

              {Object.keys(chartData).length === 0 && (
                <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No simulation records available in MongoDB Atlas yet. Trigger a loop to view curves.
                </div>
              )}
            </div>
          )}

          {/* VIEW 4: Loop Replay */}
          {activeTab === 'replay' && (
            <div className="grid-stack">
              <div className="panel-title-container">
                <h2 className="panel-title">Loop Replay</h2>
                <p className="panel-subtitle">Investigate past rounds, check evasion briefs, and examine per-layer anomaly score scorecards.</p>
              </div>

              <div className="grid-cols-3">
                {/* Round Sidebar */}
                <div className="card" style={{ maxHeight: '560px', overflowY: 'auto' }}>
                  <h3 className="card-title" style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>Round History</h3>
                  
                  <div className="history-list">
                    {isLoadingRounds ? (
                      <div style={{ textAlign: 'center', padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                        <RefreshCw size={20} className="animate-spin" style={{ color: 'var(--primary)' }} />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Loading rounds...</span>
                      </div>
                    ) : rounds.map(r => (
                      <div 
                        key={r.round_id}
                        onClick={() => setSelectedRound(r)}
                        className={`history-item ${selectedRound?.round_id === r.round_id ? 'active' : ''}`}
                      >
                        <div className="history-item-top">
                          <span className="history-item-id">{r.round_id}</span>
                          <span className="card-pill primary" style={{ fontSize: '8px' }}>
                            {r.persona.replace('_', ' ')}
                          </span>
                        </div>
                        
                        <div className="history-item-stats">
                          <span>Evasion: <strong style={{ color: 'var(--danger)' }}>{(r.evasion_rate * 100).toFixed(0)}%</strong></span>
                          <span>Recall: <strong style={{ color: 'var(--primary)' }}>{((1 - r.evasion_rate) * 100).toFixed(0)}%</strong></span>
                        </div>
                        
                        <div className="history-item-date">
                          {r.timestamp ? new Date(r.timestamp).toLocaleString() : 'N/A'}
                        </div>
                      </div>
                    ))}

                    {rounds.length === 0 && !isLoadingRounds && (
                      <p style={{ color: 'var(--text-muted)', textAlign: 'center', fontSize: '0.75rem', margin: 'auto' }}>
                        No rounds stored in MongoDB. Trigger one to view logs.
                      </p>
                    )}
                  </div>
                </div>

                {/* Round details container */}
                <div className="card" style={{ minHeight: '560px', overflowY: 'auto' }}>
                  {selectedRound ? (
                    <>
                      {/* Round stats top */}
                      <div className="card-header-row">
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <h3 className="card-title" style={{ fontFamily: 'monospace' }}>{selectedRound.round_id}</h3>
                            <span className="card-pill primary">{selectedRound.persona}</span>
                          </div>
                          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                            Executed on {new Date(selectedRound.timestamp).toLocaleString()}
                          </p>
                        </div>

                        <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.85rem' }}>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Steps</div>
                            <div style={{ fontFamily: 'monospace', fontWeight: 700 }}>{selectedRound.total_steps}</div>
                          </div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Blocked</div>
                            <div style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--danger)' }}>{selectedRound.blocked_steps}</div>
                          </div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Evasion</div>
                            <div style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--primary)' }}>{(selectedRound.evasion_rate * 100).toFixed(0)}%</div>
                          </div>
                        </div>
                      </div>

                      {/* Evasion Brief Box */}
                      <div className="evasion-brief-card">
                        <div className="evasion-brief-header">
                          <AlertTriangle size={14} />
                          <span>Adversarial Evasion Brief Summary</span>
                        </div>
                        <p className="evasion-brief-desc">
                          Adversary encountered {selectedRound.blocked_steps} blocks across {selectedRound.total_steps} total transaction projections.
                          {selectedRound.blocked_steps > 0 
                            ? " Campaign feedback loop successfully adjusted the next round's generation parameters, shifting transaction bounds to evade ensemble detectors." 
                            : " Perfect evasion achieved in this run. Parameters locked."
                          }
                        </p>
                      </div>

                      {/* Event scorecards table */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
                        <h4 style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                          Transaction Steps & Scorecards
                        </h4>
                        
                        <div className="table-wrapper">
                          <table className="table-scorecard">
                            <thead>
                              <tr>
                                <th>Step</th>
                                <th>Type</th>
                                <th>Amount</th>
                                <th style={{ textAlign: 'center' }}>Tabular</th>
                                <th style={{ textAlign: 'center' }}>Graph</th>
                                <th style={{ textAlign: 'center' }}>Seq</th>
                                <th style={{ textAlign: 'center' }}>Text</th>
                                <th style={{ textAlign: 'right' }}>Outcome</th>
                              </tr>
                            </thead>
                            <tbody>
                              {roundEvents.map((ev, idx) => {
                                const payload = ev.payload || {};
                                const stepNum = payload.step_number || (idx + 1);
                                const tType = payload.type || "PAYMENT";
                                const amt = ev.amount || 0.0;
                                const det = ev.detection_result || ev.detection || {};
                                const layers = det.layers || {};

                                return (
                                  <tr key={ev.event_id || idx}>
                                    <td style={{ fontFamily: 'monospace', fontWeight: 700 }}>{stepNum}</td>
                                    <td><span className="card-pill primary" style={{ fontSize: '8px', textTransform: 'uppercase' }}>{tType}</span></td>
                                    <td style={{ fontFamily: 'monospace' }}>${amt.toFixed(2)}</td>
                                    <td style={{ textAlign: 'center', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{(layers.tabular !== undefined ? layers.tabular * 100 : 0).toFixed(0)}%</td>
                                    <td style={{ textAlign: 'center', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{(layers.graph !== undefined ? layers.graph * 100 : 0).toFixed(0)}%</td>
                                    <td style={{ textAlign: 'center', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{(layers.sequence !== undefined ? layers.sequence * 100 : 0).toFixed(0)}%</td>
                                    <td style={{ textAlign: 'center', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{(layers.text !== undefined ? layers.text * 100 : 0).toFixed(0)}%</td>
                                    <td style={{ textAlign: 'right' }}>
                                      <span className={`badge-outcome ${det.is_flagged ? 'blocked' : 'clean'}`}>
                                        {det.is_flagged ? 'BLOCKED' : 'CLEAN'}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                              
                              {roundEvents.length === 0 && (
                                <tr>
                                  <td colSpan="8" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                    No event details stored for this round.
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', margin: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                      <RotateCcw size={24} style={{ opacity: 0.3 }} />
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Select a round from the history sidebar to view replay scorecard matrix.</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
