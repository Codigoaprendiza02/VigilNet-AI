import React, { useState, useEffect, useRef } from 'react';
import { 
  Shield, 
  Activity, 
  TrendingUp, 
  RotateCcw, 
  BookOpen, 
  Sun, 
  Moon, 
  Server, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  ArrowRight,
  Eye,
  Check,
  X
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
  // Theme state: default to dark (cyberpunk stage lighting vibe)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
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

  // Sync theme to document element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

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

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
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
        // Refresh rounds lists and stats charts
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
    <div className="min-h-screen flex flex-col">
      {/* Top Banner / Navigation */}
      <header className="glass-effect rounded-none border-t-0 border-x-0 px-6 py-4 flex flex-wrap items-center justify-between gap-4 z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl text-white shadow-lg animate-pulse">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">VigilNet AI</h1>
            <p className="text-xs text-[var(--text-secondary)]">Closed-Loop Fraud Red-Teaming & Defense Ensemble</p>
          </div>
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          {/* API Connection Settings */}
          <div className="flex items-center gap-2 bg-slate-900/40 dark:bg-slate-800/40 p-1.5 rounded-lg border border-[var(--card-border)]">
            <Server className="h-4 w-4 text-[var(--text-muted)] ml-2" />
            <input 
              type="text" 
              value={apiBase} 
              onChange={(e) => setApiBase(e.target.value)}
              className="bg-transparent border-none text-xs text-[var(--text-primary)] focus:outline-none w-48 font-mono"
              placeholder="API base URL"
            />
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[10px] font-semibold bg-slate-950/60">
              <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-ping' : 'bg-rose-500'}`}></span>
              <span className={isConnected ? 'text-emerald-400' : 'text-rose-400'}>
                {isConnected ? 'CONNECTED' : 'OFFLINE'}
              </span>
            </div>
          </div>

          {/* Theme Switcher */}
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-slate-900/40 dark:bg-slate-800/40 border border-[var(--card-border)] hover:border-[var(--primary)] text-[var(--text-primary)]"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-indigo-500" />}
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Sidebar Tabs */}
        <aside className="w-full md:w-64 border-r border-[var(--card-border)] bg-[var(--sidebar-bg)] p-4 flex flex-col gap-2">
          <p className="text-[10px] uppercase font-bold tracking-wider text-[var(--text-muted)] mb-2 px-3">Control Center</p>
          
          <button 
            onClick={() => setActiveTab('taxonomy')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === 'taxonomy' ? 'bg-[var(--nav-active)] border border-[var(--primary)] text-[var(--primary)]' : 'text-[var(--text-secondary)] hover:bg-slate-800/10 hover:text-[var(--text-primary)]'}`}
          >
            <BookOpen className="h-4 w-4" />
            <span>Fraud Taxonomy</span>
          </button>

          <button 
            onClick={() => setActiveTab('runner')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === 'runner' ? 'bg-[var(--nav-active)] border border-[var(--primary)] text-[var(--primary)]' : 'text-[var(--text-secondary)] hover:bg-slate-800/10 hover:text-[var(--text-primary)]'}`}
          >
            <Activity className="h-4 w-4" />
            <span>Simulation Runner</span>
          </button>

          <button 
            onClick={() => setActiveTab('metrics')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === 'metrics' ? 'bg-[var(--nav-active)] border border-[var(--primary)] text-[var(--primary)]' : 'text-[var(--text-secondary)] hover:bg-slate-800/10 hover:text-[var(--text-primary)]'}`}
          >
            <TrendingUp className="h-4 w-4" />
            <span>Metrics Curves</span>
          </button>

          <button 
            onClick={() => setActiveTab('replay')}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${activeTab === 'replay' ? 'bg-[var(--nav-active)] border border-[var(--primary)] text-[var(--primary)]' : 'text-[var(--text-secondary)] hover:bg-slate-800/10 hover:text-[var(--text-primary)]'}`}
          >
            <RotateCcw className="h-4 w-4" />
            <span>Evasion Replay</span>
          </button>

          <div className="mt-auto border-t border-[var(--card-border)] pt-4 px-3 text-[11px] text-[var(--text-muted)]">
            <div className="flex justify-between mb-1">
              <span>FastAPI Port</span>
              <span className="font-mono text-[var(--text-secondary)]">{apiBase.split(':').pop() || '8000'}</span>
            </div>
            <div className="flex justify-between">
              <span>Database Status</span>
              <span className="font-mono text-emerald-500">CONNECTED</span>
            </div>
          </div>
        </aside>

        {/* View Switcher Content */}
        <main className="flex-1 p-6 overflow-y-auto animate-fade-in">
          
          {/* TAB 1: Taxonomy View */}
          {activeTab === 'taxonomy' && (
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Fraud Taxonomy</h2>
                <p className="text-sm text-[var(--text-secondary)]">Overview of simulated attack vectors, mathematical models, and the protecting ensemble layers.</p>
              </div>

              <div className="grid grid-cols-1 gap-6">
                {taxonomyItems.map((item) => (
                  <div key={item.id} className="glass-effect p-6 hover:border-[var(--card-hover-border)] transition-all">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold text-[var(--text-primary)]">{item.name}</h3>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--nav-active)] text-[var(--primary)]">ACTIVE</span>
                        </div>
                        <p className="text-sm text-[var(--text-secondary)] mt-1">{item.desc}</p>
                      </div>
                      <div className="flex flex-col items-end text-xs">
                        <span className="text-[var(--text-muted)]">Ensemble Defense</span>
                        <span className="font-semibold text-emerald-500">{item.defense}</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-4 border-t border-[var(--card-border)] grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-[var(--text-muted)] uppercase block tracking-wider font-bold text-[9px] mb-1">Statistical Generator</span>
                        <span className="text-[var(--text-primary)] font-mono">{item.generator}</span>
                      </div>
                      <div>
                        <span className="text-[var(--text-muted)] uppercase block tracking-wider font-bold text-[9px] mb-1">Engineered Attributes</span>
                        <span className="text-[var(--text-primary)] font-mono">{item.engineered}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: Simulation Runner */}
          {activeTab === 'runner' && (
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Simulation Runner</h2>
                <p className="text-sm text-[var(--text-secondary)]">Trigger and orchestrate Red-Team campaign runs and observe adversarial loop adaptations.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Configuration Panel */}
                <div className="glass-effect p-6 flex flex-col gap-4 lg:col-span-1">
                  <h3 className="text-md font-bold text-[var(--text-primary)] border-b border-[var(--card-border)] pb-2 mb-2">Campaign Config</h3>
                  
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-[var(--text-secondary)]">Fraud Persona</label>
                    <select 
                      value={selectedPersona}
                      onChange={(e) => setSelectedPersona(e.target.value)}
                      className="bg-slate-900 border border-[var(--card-border)] rounded-lg p-2 text-sm text-[var(--text-primary)] focus:border-[var(--primary)] font-sans"
                    >
                      <option value="card_tester">Card Tester (Debit/Credit)</option>
                      <option value="synthetic_identity">Synthetic Identity (IEEE-CIS)</option>
                      <option value="structuring">Structuring / Smurfing (PaySim)</option>
                      <option value="phishing">BEC Spear-Phishing (Phishing)</option>
                      <option value="fake_invoice">Vendor Invoice Spoofing (Fake Invoice)</option>
                    </select>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-[var(--text-secondary)]">Progression Rounds</label>
                    <input 
                      type="number" 
                      min="1" 
                      max="5"
                      value={roundsToRun}
                      onChange={(e) => setRoundsToRun(parseInt(e.target.value) || 1)}
                      className="bg-slate-900 border border-[var(--card-border)] rounded-lg p-2 text-sm text-[var(--text-primary)] focus:border-[var(--primary)] font-mono"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-[var(--text-secondary)]">Custom Objective (Optional)</label>
                    <textarea 
                      placeholder={personaDefaultConfigs[selectedPersona].objective}
                      value={customObjective}
                      onChange={(e) => setCustomObjective(e.target.value)}
                      className="bg-slate-900 border border-[var(--card-border)] rounded-lg p-2 text-xs text-[var(--text-primary)] focus:border-[var(--primary)] h-16 resize-none"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-[var(--text-secondary)]">Custom Target Profile (Optional)</label>
                    <textarea 
                      placeholder={personaDefaultConfigs[selectedPersona].profile}
                      value={customTargetProfile}
                      onChange={(e) => setCustomTargetProfile(e.target.value)}
                      className="bg-slate-900 border border-[var(--card-border)] rounded-lg p-2 text-xs text-[var(--text-primary)] focus:border-[var(--primary)] h-16 resize-none"
                    />
                  </div>

                  <button 
                    onClick={triggerChallenge}
                    disabled={isSimulating || !isConnected}
                    className="mt-4 w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-700 text-white font-semibold hover:shadow-lg disabled:opacity-50 transition-all hover:scale-[1.02] cursor-pointer"
                  >
                    {isSimulating ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        <span>Running Loop...</span>
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 fill-current" />
                        <span>Trigger Adaptive Loop</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Simulation Logs Console */}
                <div className="glass-effect p-6 lg:col-span-2 flex flex-col h-[520px] bg-slate-950/80 border-[var(--card-border)]">
                  <div className="flex justify-between items-center border-b border-[var(--card-border)] pb-2 mb-3">
                    <h3 className="text-md font-bold text-[var(--text-primary)]">Simulation Console Logs</h3>
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold tracking-wider bg-slate-900 text-[var(--primary)] font-mono">STDOUT</span>
                  </div>

                  <div className="flex-1 overflow-y-auto font-mono text-xs text-cyan-400/90 flex flex-col gap-1.5 pr-2">
                    {simLogs.map((log, idx) => (
                      <div key={idx} className={log.startsWith('[Error]') ? 'text-rose-400' : log.startsWith('[System]') ? 'text-emerald-400' : 'text-slate-300'}>
                        {log}
                      </div>
                    ))}
                    {isSimulating && (
                      <div className="text-cyan-400 flex items-center gap-1.5 mt-2">
                        <span className="h-2 w-2 bg-cyan-400 rounded-full animate-ping"></span>
                        <span>Red Team agent is generating next progression plan...</span>
                      </div>
                    )}
                    {simLogs.length === 0 && (
                      <p className="text-[var(--text-muted)] text-center my-auto">Configuration selected. Click "Trigger Adaptive Loop" to start.</p>
                    )}
                  </div>

                  {simResult && (
                    <div className="mt-4 p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/20 flex flex-col gap-2">
                      <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Adaptive challenge completed!</span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-xs mt-1 text-slate-300">
                        <div>
                          <span className="text-[var(--text-muted)] uppercase block text-[9px]">Rounds Executed</span>
                          <span className="font-semibold text-emerald-400 font-mono">{simResult.total_rounds_executed}</span>
                        </div>
                        <div>
                          <span className="text-[var(--text-muted)] uppercase block text-[9px]">Final Evasion Rate</span>
                          <span className="font-semibold text-emerald-400 font-mono">{simResult.final_evasion_rate * 100}%</span>
                        </div>
                        <div>
                          <span className="text-[var(--text-muted)] uppercase block text-[9px]">Ensemble Performance</span>
                          <span className="font-semibold text-emerald-400">Recall Increased</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Metrics Curves */}
          {activeTab === 'metrics' && (
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Metrics Curves</h2>
                <p className="text-sm text-[var(--text-secondary)]">Verify round-over-round evasion rates and recall curves showing detection success.</p>
              </div>

              {/* Chart Grid */}
              <div className="grid grid-cols-1 gap-6">
                {['card_tester', 'structuring', 'phishing', 'fake_invoice', 'synthetic_identity'].map(pName => {
                  const data = chartData[pName] || [];
                  if (data.length === 0) return null;
                  
                  return (
                    <div key={pName} className="glass-effect p-6 flex flex-col gap-4">
                      <div className="flex justify-between items-center border-b border-[var(--card-border)] pb-2">
                        <h3 className="text-lg font-bold text-[var(--text-primary)] uppercase tracking-wide">
                          {pName.replace('_', ' ')} Performance
                        </h3>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[var(--nav-active)] text-[var(--primary)] font-bold">
                          {data.length} rounds logged
                        </span>
                      </div>

                      <div className="h-[280px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
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
                  <div className="glass-effect p-12 text-center text-[var(--text-muted)]">
                    No simulation records available in MongoDB Atlas yet. Trigger a loop to view curves.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: Loop Replay View */}
          {activeTab === 'replay' && (
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Loop Replay</h2>
                <p className="text-sm text-[var(--text-secondary)]">Investigate past rounds, check evasion briefs, and examine per-layer anomaly score scorecards.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Rounds List Sidebar */}
                <div className="glass-effect p-6 flex flex-col gap-4 lg:col-span-1 h-[600px] overflow-y-auto">
                  <h3 className="text-md font-bold text-[var(--text-primary)] border-b border-[var(--card-border)] pb-2 mb-2">Round History</h3>
                  
                  {isLoadingRounds ? (
                    <div className="text-center my-auto flex flex-col items-center gap-2">
                      <RefreshCw className="h-5 w-5 animate-spin text-[var(--primary)]" />
                      <span className="text-xs text-[var(--text-secondary)]">Loading rounds...</span>
                    </div>
                  ) : rounds.map(r => (
                    <div 
                      key={r.round_id}
                      onClick={() => setSelectedRound(r)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col gap-1.5 ${selectedRound?.round_id === r.round_id ? 'border-[var(--primary)] bg-[var(--nav-active)]' : 'border-[var(--card-border)] hover:border-slate-500/30 bg-slate-900/10'}`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-mono font-bold text-[var(--text-primary)]">{r.round_id}</span>
                        <span className="px-2 py-0.5 rounded text-[9px] uppercase font-bold bg-slate-950/60 text-[var(--text-secondary)] font-sans">
                          {r.persona.replace('_', ' ')}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center text-xs text-[var(--text-secondary)] mt-1">
                        <span>Evasion: <strong className="text-rose-500 font-mono">{(r.evasion_rate * 100).toFixed(0)}%</strong></span>
                        <span>Recall: <strong className="text-cyan-500 font-mono">{((1 - r.evasion_rate) * 100).toFixed(0)}%</strong></span>
                      </div>
                      
                      <div className="text-[10px] text-[var(--text-muted)] text-right">
                        {r.timestamp ? new Date(r.timestamp).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                  ))}

                  {rounds.length === 0 && !isLoadingRounds && (
                    <p className="text-[var(--text-muted)] text-center text-xs my-auto">No rounds stored in MongoDB. Trigger one to view logs.</p>
                  )}
                </div>

                {/* Round Details Console */}
                <div className="glass-effect p-6 lg:col-span-2 h-[600px] overflow-y-auto flex flex-col gap-4">
                  {selectedRound ? (
                    <>
                      {/* Round Heading */}
                      <div className="flex justify-between items-start border-b border-[var(--card-border)] pb-4">
                        <div>
                          <div className="flex items-center gap-3">
                            <h3 className="text-lg font-bold text-[var(--text-primary)] font-mono">{selectedRound.round_id}</h3>
                            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono font-bold bg-[var(--nav-active)] text-[var(--primary)]">
                              {selectedRound.persona}
                            </span>
                          </div>
                          <p className="text-xs text-[var(--text-muted)] mt-1">Executed on {new Date(selectedRound.timestamp).toLocaleString()}</p>
                        </div>

                        <div className="flex items-center gap-6 text-sm">
                          <div className="text-center">
                            <span className="text-[9px] text-[var(--text-muted)] uppercase block">Total Steps</span>
                            <span className="font-mono text-lg font-bold">{selectedRound.total_steps}</span>
                          </div>
                          <div className="text-center">
                            <span className="text-[9px] text-[var(--text-muted)] uppercase block text-rose-500">Blocked</span>
                            <span className="font-mono text-lg font-bold text-rose-500">{selectedRound.blocked_steps}</span>
                          </div>
                          <div className="text-center">
                            <span className="text-[9px] text-[var(--text-muted)] uppercase block text-cyan-400">Evasion</span>
                            <span className="font-mono text-lg font-bold text-cyan-400">{(selectedRound.evasion_rate * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      </div>

                      {/* Evasion Brief Overview */}
                      <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-950/10 flex flex-col gap-1.5">
                        <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
                          <AlertTriangle className="h-4 w-4" />
                          <span>Adversarial Evasion Brief Summary</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed font-sans">
                          Adversary encountered {selectedRound.blocked_steps} blocks across {selectedRound.total_steps} total transaction projections.
                          {selectedRound.blocked_steps > 0 
                            ? " Campaign feedback loop successfully adjusted the next round's generation parameters, shifting transaction bounds to evade ensemble detectors." 
                            : " Perfect evasion achieved in this run. Parameters locked."
                          }
                        </p>
                      </div>

                      {/* Detailed Events Table */}
                      <div className="flex-1 flex flex-col gap-2">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">Transaction Steps & Scorecards</h4>
                        
                        <div className="border border-[var(--card-border)] rounded-xl overflow-hidden flex-1 overflow-y-auto">
                          <table className="w-full text-left text-xs border-collapse">
                            <thead className="bg-slate-900/60 text-[var(--text-secondary)] font-semibold border-b border-[var(--card-border)]">
                              <tr>
                                <th className="p-3">Step</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Amount</th>
                                <th className="p-3 text-center">Tabular</th>
                                <th className="p-3 text-center">Graph</th>
                                <th className="p-3 text-center">Seq</th>
                                <th className="p-3 text-center">Text</th>
                                <th className="p-3 text-right">Outcome</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-[var(--card-border)] text-slate-300">
                              {roundEvents.map((ev, idx) => {
                                const payload = ev.payload || {};
                                const stepNum = payload.step_number || (idx + 1);
                                const tType = payload.type || "PAYMENT";
                                const amt = ev.amount || 0.0;
                                const det = ev.detection_result || ev.detection || {};
                                const layers = det.layers || {};

                                return (
                                  <tr key={ev.event_id || idx} className="hover:bg-slate-900/30">
                                    <td className="p-3 font-mono font-semibold">{stepNum}</td>
                                    <td className="p-3"><span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">{tType}</span></td>
                                    <td className="p-3 font-mono">${amt.toFixed(2)}</td>
                                    <td className="p-3 text-center font-mono text-slate-400">{(layers.tabular !== undefined ? layers.tabular * 100 : 0).toFixed(0)}%</td>
                                    <td className="p-3 text-center font-mono text-slate-400">{(layers.graph !== undefined ? layers.graph * 100 : 0).toFixed(0)}%</td>
                                    <td className="p-3 text-center font-mono text-slate-400">{(layers.sequence !== undefined ? layers.sequence * 100 : 0).toFixed(0)}%</td>
                                    <td className="p-3 text-center font-mono text-slate-400">{(layers.text !== undefined ? layers.text * 100 : 0).toFixed(0)}%</td>
                                    <td className="p-3 text-right">
                                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${det.is_flagged ? 'bg-rose-950/60 text-rose-400 border border-rose-500/25' : 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/25'}`}>
                                        {det.is_flagged ? 'BLOCKED' : 'CLEAN'}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                              
                              {roundEvents.length === 0 && (
                                <tr>
                                  <td colSpan="8" className="p-8 text-center text-[var(--text-muted)]">No event details stored for this round.</td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-center my-auto text-[var(--text-muted)] flex flex-col items-center gap-2 font-sans">
                      <RotateCcw className="h-8 w-8 opacity-40 animate-spin-reverse" />
                      <span>Select a round from the history sidebar to view replay scorecard matrix.</span>
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
