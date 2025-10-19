import React, { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, FileText, RefreshCw, Upload, DollarSign, Activity, Shield } from 'lucide-react';
import './Finguard.css'; 
const FinGuardDashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isRebalancing, setIsRebalancing] = useState(false);
  const [showRebalanceModal, setShowRebalanceModal] = useState(false);
  const [rebalanceResult, setRebalanceResult] = useState(null);

  // Portfolio data
  const [portfolio] = useState({
    totalValue: 125420.50,
    target: {
      stocks: 40,
      crypto: 20,
      bonds: 25,
      etfs: 15
    },
    current: {
      stocks: 35,
      crypto: 28,
      bonds: 22,
      etfs: 15
    },
    holdings: [
      { symbol: 'AAPL', name: 'Apple Inc.', qty: 50, price: 175.20, value: 8760, allocation: 7.0, target: 10, drift: -3.0, category: 'stocks' },
      { symbol: 'MSFT', name: 'Microsoft', qty: 30, price: 380.50, value: 11415, allocation: 9.1, target: 10, drift: -0.9, category: 'stocks' },
      { symbol: 'GOOGL', name: 'Google', qty: 20, price: 142.30, value: 2846, allocation: 2.3, target: 5, drift: -2.7, category: 'stocks' },
      { symbol: 'BTC', name: 'Bitcoin', qty: 0.5, price: 62000, value: 31000, allocation: 24.7, target: 15, drift: 9.7, category: 'crypto' },
      { symbol: 'ETH', name: 'Ethereum', qty: 2, price: 2200, value: 4400, allocation: 3.5, target: 5, drift: -1.5, category: 'crypto' },
      { symbol: 'VBMFX', name: 'Vanguard Bonds', qty: 250, price: 110.20, value: 27550, allocation: 22.0, target: 25, drift: -3.0, category: 'bonds' },
      { symbol: 'SPY', name: 'S&P 500 ETF', qty: 40, price: 445.50, value: 17820, allocation: 14.2, target: 15, drift: -0.8, category: 'etfs' },
    ]
  });

  const [auditLog] = useState([
    {
      id: 'AL-20251018-001',
      timestamp: '2025-10-18T09:15:23Z',
      action: 'Reduce BTC allocation by 9.7%',
      reason: 'Bitcoin allocation exceeded target by 9.7%. Volatility increased by 32% over past 7 days. Risk-adjusted return optimization suggests reallocation to lower-volatility assets.',
      aiConfidence: 0.94,
      trades: [
        { action: 'SELL', symbol: 'BTC', amount: 0.12, value: 7440 },
        { action: 'BUY', symbol: 'AAPL', amount: 25, value: 4380 },
        { action: 'BUY', symbol: 'VBMFX', amount: 28, value: 3085 }
      ],
      status: 'pending',
      impact: {
        riskReduction: '12.3%',
        expectedReturn: '+2.1% annualized',
        sharpeImprovement: '+0.15'
      }
    },
    {
      id: 'AL-20251015-002',
      timestamp: '2025-10-15T14:22:10Z',
      action: 'Rebalance stocks allocation',
      reason: 'Market correction detected. Tech sector down 5.2%. Portfolio stocks allocation fell below target threshold (35% vs 40% target).',
      aiConfidence: 0.88,
      trades: [
        { action: 'BUY', symbol: 'GOOGL', amount: 15, value: 2134 },
        { action: 'SELL', symbol: 'VBMFX', amount: 20, value: 2204 }
      ],
      status: 'executed',
      impact: {
        riskReduction: '3.1%',
        expectedReturn: '+1.4% annualized',
        sharpeImprovement: '+0.08'
      }
    }
  ]);

  // Calculate drift alerts
  const driftAlerts = portfolio.holdings.filter(h => Math.abs(h.drift) > 2.5);

  // Pie chart data
  const pieData = [
    { name: 'Stocks', value: portfolio.current.stocks, target: portfolio.target.stocks, color: '#3b82f6' },
    { name: 'Crypto', value: portfolio.current.crypto, target: portfolio.target.crypto, color: '#f59e0b' },
    { name: 'Bonds', value: portfolio.current.bonds, target: portfolio.target.bonds, color: '#10b981' },
    { name: 'ETFs', value: portfolio.current.etfs, target: portfolio.target.etfs, color: '#8b5cf6' }
  ];

  // Historical performance data
  const performanceData = [
    { date: 'Oct 11', value: 118500, benchmark: 117000 },
    { date: 'Oct 12', value: 120200, benchmark: 118500 },
    { date: 'Oct 13', value: 119800, benchmark: 119200 },
    { date: 'Oct 14', value: 122100, benchmark: 120800 },
    { date: 'Oct 15', value: 121500, benchmark: 121200 },
    { date: 'Oct 16', value: 123800, benchmark: 122500 },
    { date: 'Oct 17', value: 124200, benchmark: 123100 },
    { date: 'Oct 18', value: 125420, benchmark: 123800 }
  ];

  const handleRebalance = () => {
    setIsRebalancing(true);
    setTimeout(() => {
      setIsRebalancing(false);
      setRebalanceResult({
        trades: auditLog[0].trades,
        impact: auditLog[0].impact,
        confidence: auditLog[0].aiConfidence
      });
      setShowRebalanceModal(true);
    }, 2500);
  };

  const StatCard = ({ title, value, change, icon: Icon, trend }) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{title}</span>
        <Icon className="text-blue-400" size={20} />
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      {change && (
        <div className={`flex items-center text-sm ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
          {trend === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
          <span className="ml-1">{change}</span>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="text-blue-400" size={32} />
            <div>
              <h1 className="text-2xl font-bold">FinGuard AI</h1>
              <p className="text-sm text-gray-400">Auditable Portfolio Rebalancer</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button className="flex items-center space-x-2 bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition">
              <Upload size={18} />
              <span>Upload CSV</span>
            </button>
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center font-bold">
              JD
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6">
        <div className="flex space-x-1">
          {['dashboard', 'audit', 'settings'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 capitalize transition ${
                activeTab === tab
                  ? 'border-b-2 border-blue-400 text-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </nav>

      {/* Main Content */}
      <main className="p-6">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="Total Portfolio Value"
                value={`$${portfolio.totalValue.toLocaleString()}`}
                change="+3.2% (7d)"
                icon={DollarSign}
                trend="up"
              />
              <StatCard
                title="Active Alerts"
                value={driftAlerts.length}
                change="Rebalancing needed"
                icon={AlertTriangle}
              />
              <StatCard
                title="AI Confidence"
                value="94%"
                change="High accuracy"
                icon={Activity}
                trend="up"
              />
              <StatCard
                title="Last Rebalance"
                value="3 days ago"
                change="Next: Today"
                icon={RefreshCw}
              />
            </div>

            {/* Alert Banner */}
            {driftAlerts.length > 0 && (
              <div className="bg-orange-900/30 border border-orange-600 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="text-orange-400 mt-1" size={24} />
                    <div>
                      <h3 className="font-bold text-orange-400 mb-1">Portfolio Drift Detected</h3>
                      <p className="text-sm text-gray-300">
                        {driftAlerts.length} asset(s) have drifted significantly from target allocation. 
                        BTC is {driftAlerts[0].drift > 0 ? 'over' : 'under'}weighted by {Math.abs(driftAlerts[0].drift).toFixed(1)}%.
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={handleRebalance}
                    disabled={isRebalancing}
                    className="bg-orange-600 hover:bg-orange-700 px-6 py-2 rounded-lg font-semibold flex items-center space-x-2 transition disabled:opacity-50"
                  >
                    <RefreshCw className={isRebalancing ? 'animate-spin' : ''} size={18} />
                    <span>{isRebalancing ? 'Analyzing...' : 'Rebalance Now'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Allocation Chart */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-lg font-bold mb-4">Asset Allocation</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, value }) => `${name} ${value}%`}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                      formatter={(value, name, props) => [
                        `${value}% (Target: ${props.payload.target}%)`,
                        name
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Performance Chart */}
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-lg font-bold mb-4">Portfolio Performance (7d)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="value" stroke="#3b82f6" name="Your Portfolio" strokeWidth={2} />
                    <Line type="monotone" dataKey="benchmark" stroke="#6b7280" name="Benchmark" strokeWidth={2} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Holdings Table */}
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-6 border-b border-gray-700">
                <h3 className="text-lg font-bold">Holdings</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Asset</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase">Quantity</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase">Price</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase">Value</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase">Allocation</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase">Target</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase">Drift</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {portfolio.holdings.map((holding, idx) => (
                      <tr key={idx} className="hover:bg-gray-700/50">
                        <td className="px-6 py-4">
                          <div>
                            <div className="font-semibold">{holding.symbol}</div>
                            <div className="text-sm text-gray-400">{holding.name}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">{holding.qty}</td>
                        <td className="px-6 py-4 text-right">${holding.price.toLocaleString()}</td>
                        <td className="px-6 py-4 text-right font-semibold">${holding.value.toLocaleString()}</td>
                        <td className="px-6 py-4 text-right">{holding.allocation}%</td>
                        <td className="px-6 py-4 text-right text-gray-400">{holding.target}%</td>
                        <td className="px-6 py-4 text-right">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${
                            Math.abs(holding.drift) > 2.5
                              ? 'bg-red-900/30 text-red-400'
                              : Math.abs(holding.drift) > 1
                              ? 'bg-yellow-900/30 text-yellow-400'
                              : 'bg-green-900/30 text-green-400'
                          }`}>
                            {holding.drift > 0 ? '+' : ''}{holding.drift.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold">Audit Trail</h3>
                  <p className="text-sm text-gray-400">Complete history of AI-driven portfolio actions</p>
                </div>
                <button className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition">
                  <FileText size={18} />
                  <span>Export Report</span>
                </button>
              </div>

              <div className="space-y-4">
                {auditLog.map((log, idx) => (
                  <div key={idx} className="bg-gray-700 rounded-lg p-6 border border-gray-600">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center space-x-3 mb-2">
                          <span className="text-xs font-mono text-gray-400">{log.id}</span>
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            log.status === 'executed' ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'
                          }`}>
                            {log.status.toUpperCase()}
                          </span>
                        </div>
                        <h4 className="text-lg font-bold mb-1">{log.action}</h4>
                        <p className="text-sm text-gray-400">{new Date(log.timestamp).toLocaleString()}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-400">AI Confidence</div>
                        <div className="text-2xl font-bold text-blue-400">{(log.aiConfidence * 100).toFixed(0)}%</div>
                      </div>
                    </div>

                    <div className="bg-gray-800 rounded p-4 mb-4">
                      <h5 className="font-semibold mb-2 text-blue-400">Reasoning:</h5>
                      <p className="text-sm text-gray-300">{log.reason}</p>
                    </div>

                    <div className="mb-4">
                      <h5 className="font-semibold mb-2">Proposed Trades:</h5>
                      <div className="space-y-2">
                        {log.trades.map((trade, tidx) => (
                          <div key={tidx} className="flex items-center justify-between bg-gray-800 rounded px-4 py-2">
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 rounded text-xs font-bold ${
                                trade.action === 'BUY' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                              }`}>
                                {trade.action}
                              </span>
                              <span className="font-semibold">{trade.symbol}</span>
                              <span className="text-gray-400">×{trade.amount}</span>
                            </div>
                            <span className="font-semibold">${trade.value.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-gray-800 rounded p-3">
                        <div className="text-xs text-gray-400 mb-1">Risk Reduction</div>
                        <div className="text-lg font-bold text-green-400">{log.impact.riskReduction}</div>
                      </div>
                      <div className="bg-gray-800 rounded p-3">
                        <div className="text-xs text-gray-400 mb-1">Expected Return</div>
                        <div className="text-lg font-bold text-blue-400">{log.impact.expectedReturn}</div>
                      </div>
                      <div className="bg-gray-800 rounded p-3">
                        <div className="text-xs text-gray-400 mb-1">Sharpe Improvement</div>
                        <div className="text-lg font-bold text-purple-400">{log.impact.sharpeImprovement}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-bold mb-4">Target Allocation</h3>
              <div className="space-y-4">
                {pieData.map(asset => (
                  <div key={asset.name}>
                    <div className="flex justify-between mb-2">
                      <span className="font-semibold">{asset.name}</span>
                      <span>{asset.target}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={asset.target}
                      className="w-full"
                      readOnly
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-bold mb-4">Rebalancing Preferences</h3>
              <div className="space-y-3">
                <label className="flex items-center space-x-3">
                  <input type="checkbox" defaultChecked className="w-4 h-4" />
                  <span>Auto-rebalance when drift exceeds 5%</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input type="checkbox" defaultChecked className="w-4 h-4" />
                  <span>Send email notifications for rebalancing opportunities</span>
                </label>
                <label className="flex items-center space-x-3">
                  <input type="checkbox" className="w-4 h-4" />
                  <span>Enable tax-loss harvesting</span>
                </label>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Rebalance Modal */}
      {showRebalanceModal && rebalanceResult && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full border border-gray-700">
            <div className="flex items-center space-x-3 mb-6">
              <CheckCircle className="text-green-400" size={32} />
              <h3 className="text-2xl font-bold">Rebalancing Plan Ready</h3>
            </div>

            <div className="mb-6">
              <h4 className="font-semibold mb-3">Recommended Trades:</h4>
              <div className="space-y-2">
                {rebalanceResult.trades.map((trade, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-gray-700 rounded px-4 py-3">
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        trade.action === 'BUY' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                      }`}>
                        {trade.action}
                      </span>
                      <span className="font-semibold">{trade.symbol}</span>
                      <span className="text-gray-400">×{trade.amount}</span>
                    </div>
                    <span className="font-semibold">${trade.value.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-700 rounded p-4 mb-6">
              <h4 className="font-semibold mb-3">Expected Impact:</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-gray-400 mb-1">Risk Reduction</div>
                  <div className="text-lg font-bold text-green-400">{rebalanceResult.impact.riskReduction}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400 mb-1">Expected Return</div>
                  <div className="text-lg font-bold text-blue-400">{rebalanceResult.impact.expectedReturn}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400 mb-1">AI Confidence</div>
                  <div className="text-lg font-bold text-purple-400">{(rebalanceResult.confidence * 100).toFixed(0)}%</div>
                </div>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={() => setShowRebalanceModal(false)}
                className="flex-1 bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-lg font-semibold transition"
              >
                Review Later
              </button>
              <button
                onClick={() => {
                  setShowRebalanceModal(false);
                  setActiveTab('audit');
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition"
              >
                Execute Rebalance
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FinGuardDashboard;