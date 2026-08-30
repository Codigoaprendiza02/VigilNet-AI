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
  RefreshCw,
  ArrowRight,
  Cpu,
  FileText,
  Mail,
  Users
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
      icon: <Shield size={18} style={{ color: 'var(--primary)' }} />,
      generator: "IEEE-CIS / PaySim Hybrid",
      engineered: "TransactionAmt, balanceOrig/Dest error ratio, card identity mapping",
      defense: "Sequence Layer (LSTM) & Tabular (XGBoost)",
      layers: ["Tabular", "Sequence"],
      desc: "Simulates cards checking validity via successive small transactions. Caught by temporal sequence analysis.",
      mechanics: [
        "Adversary compiles targeted debit/credit card accounts.",
        "Executes rapid successive low-value ($1.00 - $5.00) authorization checks.",
        "LSTM checks timing spacing anomalies; XGBoost evaluates AMT outliers."
      ]
    },
    {
      id: "synthetic_identity",
      name: "Synthetic Identity Fraud",
      icon: <Users size={18} style={{ color: 'var(--primary)' }} />,
      generator: "IEEE-CIS statistical model",
      engineered: "addr1, addr2, card1-card6 aliases, D1-D15 offset features",
      defense: "Tabular (XGBoost) & Graph (GCN)",
      layers: ["Tabular", "Graph"],
      desc: "Red Team builds synthetic profiles and makes applications. Tabular signals identify anomaly correlations.",
      mechanics: [
        "Adversary builds false identity profiles using real SSNs and fake addresses.",
        "Opens credit accounts, establishing small initial histories to build trust.",
        "Evaluated via tabular model correlations and GCN relationship networks."
      ]
    },
    {
      id: "structuring",
      name: "Structuring / Smurfing",
      icon: <Cpu size={18} style={{ color: 'var(--primary)' }} />,
      generator: "PaySim transactional flow",
      engineered: "Splitted amounts, sub-threshold CTR offsets, account out-degree",
      defense: "Graph Layer (GCN) & Tabular (XGBoost)",
      layers: ["Tabular", "Graph"],
      desc: "Breaks a large sum into smurfing nodes to bypass thresholds. Detected via GCN node propagation.",
      mechanics: [
        "Adversary splits a large transfer into multiple sub-threshold transactions.",
        "Routes funds through smurf sender nodes to a target mule account hub.",
        "GCN flags nodes with anomalous out-degree; Tabular flags sub-threshold transactions."
      ]
    },
    {
      id: "phishing",
      name: "BEC Spear-Phishing",
      icon: <Mail size={18} style={{ color: 'var(--primary)' }} />,
      generator: "Gemini Text Embeddings",
      engineered: "Business context, urgency phrasing, payment routing command alerts",
      defense: "Text Layer (Gemini Prompted)",
      layers: ["Text"],
      desc: "Emails sent to C-Suite asking to wire money to routing updates. Caught by the prompted Text defense layer.",
      mechanics: [
        "Adversary spear-phishes accounting department pretending to be CEO/vendor.",
        "Demands urgent wire transfer for acquisition retainer or billing renewal.",
        "Prompted Gemini-3.5-flash evaluates email text structure for routing modifications."
      ]
    },
    {
      id: "fake_invoice",
      name: "Supplier Invoice Fraud",
      icon: <FileText size={18} style={{ color: 'var(--primary)' }} />,
      generator: "Gemini Text Embeddings",
      engineered: "Invoicing terminology, vendor verification matching",
      defense: "Text Layer (Gemini Prompted)",
      layers: ["Text"],
      desc: "Red Team acts as false suppliers renewing license bills. Checked against text-based LLM classifier.",
      mechanics: [
        "Adversary spoof-emails accounts payable department with a duplicate software bill.",
        "Claims bank details changed and threatens service interruption if unpaid.",
        "Prompted Gemini evaluates the text rationale and invoice details for BEC indicators."
      ]
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

              {/* Intuitive Loop Flowchart Card */}
              <div className="loop-flow-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)' }}>
                  <TrendingUp size={16} />
                  <span style={{ fontSize: '0.8rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Adversarial Learning Cycle (Feedback Loop)
                  </span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  VigilNet operates as a closed-loop system. When the Blue Team shields block a Red Team persona's attack campaign, the evasion brief details are compiled to dynamically adapt the next campaign strategy.
                </p>

                <div className="loop-flow-container">
                  <div className="loop-flow-node">
                    <Activity size={18} style={{ color: 'var(--danger)' }} />
                    <span className="loop-flow-node-title">1. Red Team Agent</span>
                    <span className="loop-flow-node-desc">Gemini plans campaign step bounds</span>
                  </div>

                  <div className="arrow-connector">
                    <ArrowRight size={18} />
                  </div>

                  <div className="loop-flow-node">
                    <Cpu size={18} style={{ color: 'var(--secondary)' }} />
                    <span className="loop-flow-node-title">2. SDV Generator</span>
                    <span className="loop-flow-node-desc">Projects realistic synthetic data</span>
                  </div>

                  <div className="arrow-connector">
                    <ArrowRight size={18} />
                  </div>

                  <div className="loop-flow-node">
                    <Shield size={18} style={{ color: 'var(--primary)' }} />
                    <span className="loop-flow-node-title">3. Ensemble Shield</span>
                    <span className="loop-flow-node-desc">Evaluates & blocks transactions</span>
                  </div>

                  <div className="arrow-connector">
                    <ArrowRight size={18} />
                  </div>

                  <div className="loop-flow-node">
                    <RotateCcw size={18} style={{ color: 'var(--success)' }} />
                    <span className="loop-flow-node-title">4. Adapt & Loop</span>
                    <span className="loop-flow-node-desc">Miss-agent redirects adversary</span>
                  </div>
                </div>
              </div>

              {/* Taxonomy Cards Grid (2-Columns) */}
              <div className="grid-2-columns">
                {taxonomyItems.map((item) => (
                  <div key={item.id} className="card hoverable">
                    <div className="card-header-row">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {item.icon}
                        <h3 className="card-title">{item.name}</h3>
                      </div>
                      <span className="card-pill primary" style={{ fontSize: '8px' }}>ACTIVE</span>
                    </div>

                    <p className="card-description" style={{ fontSize: '0.8rem' }}>{item.desc}</p>

                    <div>
                      <span className="details-block-label" style={{ display: 'block', marginBottom: '0.25rem' }}>Core Mechanics</span>
                      <ul className="mechanics-list">
                        {item.mechanics.map((step, sIdx) => (
                          <li key={sIdx}>{step}</li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ borderTop: '1px solid var(--card-border)', paddingTop: '0.75rem', marginTop: '0.25rem' }}>
                      <span className="details-block-label">Active Ensemble Shields</span>
                      <div className="chip-group">
                        {item.layers.map((layer) => (
                          <span key={layer} className="defense-chip">{layer} Layer</span>
                        ))}
                      </div>
                    </div>

                    <div className="details-row-container" style={{ borderTop: '1px solid var(--card-border)', paddingTop: '0.75rem', marginTop: '0.25rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                      <div>
                        <span className="details-block-label">Generator Profile</span>
                        <div className="details-block-value" style={{ fontSize: '0.7rem' }}>{item.generator}</div>
                      </div>
                      <div>
                        <span className="details-block-label">Telemetry Fields</span>
                        <div className="details-block-value" style={{ fontSize: '0.7rem' }}>{item.engineered}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--card-border)', paddingBottom: '0.75rem' }}>
                    <Activity size={18} style={{ color: 'var(--primary)' }} />
                    <h3 className="card-title" style={{ margin: 0 }}>Campaign Configuration</h3>
                  </div>

                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                    Specify the target threat vector constraints. The orchestrator will trigger the corresponding Gemini Red Team agent to generate adaptive transactions.
                  </p>

                  <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700 }}>
                      <span className="defense-chip" style={{ margin: 0 }}>Step 1</span>
                      <span>Target Persona Profile</span>
                    </label>
                    <select 
                      value={selectedPersona}
                      onChange={(e) => setSelectedPersona(e.target.value)}
                      className="form-select"
                    >
                      <option value="card_tester">Card Tester (Tabular/Sequence)</option>
                      <option value="synthetic_identity">Synthetic Identity (Tabular/Graph)</option>
                      <option value="structuring">Structuring / Smurfing (Tabular/Graph)</option>
                      <option value="phishing">BEC Spear-Phishing (Text)</option>
                      <option value="fake_invoice">Vendor Invoice Spoofing (Text)</option>
                    </select>
                  </div>

                  <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700 }}>
                      <span className="defense-chip" style={{ margin: 0 }}>Step 2</span>
                      <span>Progression Rounds</span>
                    </label>
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

                  <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700 }}>
                      <span className="defense-chip" style={{ margin: 0 }}>Step 3</span>
                      <span>Custom Objective (Optional)</span>
                    </label>
                    <textarea 
                      placeholder={personaDefaultConfigs[selectedPersona].objective}
                      value={customObjective}
                      onChange={(e) => setCustomObjective(e.target.value)}
                      className="form-textarea"
                      style={{ height: '60px', fontSize: '0.75rem' }}
                    />
                  </div>

                  <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700 }}>
                      <span className="defense-chip" style={{ margin: 0 }}>Step 4</span>
                      <span>Target Profile (Optional)</span>
                    </label>
                    <textarea 
                      placeholder={personaDefaultConfigs[selectedPersona].profile}
                      value={customTargetProfile}
                      onChange={(e) => setCustomTargetProfile(e.target.value)}
                      className="form-textarea"
                      style={{ height: '60px', fontSize: '0.75rem' }}
                    />
                  </div>

                  <button 
                    onClick={triggerChallenge}
                    disabled={isSimulating || !isConnected}
                    className="btn-submit"
                    style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
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
                <div className="console-box" style={{ backgroundColor: 'var(--console-bg)', border: '1px solid var(--card-border)', display: 'flex', flexDirection: 'column' }}>
                  <div className="card-header-row" style={{ marginBottom: '0.75rem', borderBottom: '1px solid var(--card-border)', paddingBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Cpu size={16} style={{ color: 'var(--primary)' }} />
                      <h3 className="card-title" style={{ margin: 0 }}>Simulation Logs</h3>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {simLogs.length > 0 && (
                        <button 
                          onClick={() => setSimLogs([])}
                          className="defense-chip"
                          style={{ cursor: 'pointer', margin: 0 }}
                        >
                          Clear
                        </button>
                      )}
                      <span className="card-pill primary" style={{ fontFamily: 'monospace', margin: 0 }}>STDOUT</span>
                    </div>
                  </div>

                  <div className="console-body" style={{ color: 'var(--text-primary)', flex: 1, padding: '0.5rem 0' }}>
                    {simLogs.map((log, idx) => {
                      const match = log.match(/^\[([^\]]+)\](.*)$/);
                      if (match) {
                        const tag = match[1];
                        const text = match[2];
                        let badgeClass = 'log-badge-info';
                        let textClass = 'console-line-info';
                        
                        if (tag === 'System') {
                          badgeClass = 'log-badge-sys';
                          textClass = 'console-line-sys';
                        } else if (tag === 'Error') {
                          badgeClass = 'log-badge-err';
                          textClass = 'console-line-err';
                        }
                        
                        return (
                          <div key={idx} className={textClass} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.35rem', lineHeight: 1.4 }}>
                            <span className={`log-badge ${badgeClass}`}>{tag}</span>
                            <span style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{text.trim()}</span>
                          </div>
                        );
                      }
                      
                      return (
                        <div key={idx} className="console-line-info" style={{ paddingLeft: '3.8rem', fontSize: '0.75rem', fontFamily: 'monospace', marginBottom: '0.35rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                          {log}
                        </div>
                      );
                    })}
                    
                    {isSimulating && (
                      <div className="console-line-sys" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.75rem', paddingLeft: '0.25rem' }}>
                        <span className="connection-indicator online" style={{ width: '8px', height: '8px' }}></span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: 700 }}>Red Team agent is generating next campaign bounds...</span>
                      </div>
                    )}
                    
                    {simLogs.length === 0 && (
                      <p style={{ color: 'var(--text-muted)', textAlign: 'center', margin: 'auto', fontSize: '0.75rem' }}>
                        Simulation idle. Select a persona and click "Trigger Adaptive Loop" to initiate.
                      </p>
                    )}
                  </div>

                  {simResult && (
                    <div className="alert-box" style={{ border: '1px solid var(--success-border)', backgroundColor: 'var(--success-bg)', padding: '0.75rem', borderRadius: '8px', marginTop: '0.75rem' }}>
                      <div className="alert-header" style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', fontWeight: 700 }}>
                        <CheckCircle2 size={14} />
                        <span>Adaptive challenge completed!</span>
                      </div>
                      <div className="alert-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', marginTop: '0.35rem' }}>
                        <div>
                          <div className="alert-val-lbl" style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>Rounds Run</div>
                          <div className="alert-val-num" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--success)' }}>{simResult.total_rounds_executed}</div>
                        </div>
                        <div>
                          <div className="alert-val-lbl" style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>Final Evasion</div>
                          <div className="alert-val-num" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--success)' }}>{simResult.final_evasion_rate * 100}%</div>
                        </div>
                        <div>
                          <div className="alert-val-lbl" style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>Def. Performance</div>
                          <div className="alert-val-num" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--success)' }}>Recall Up</div>
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
