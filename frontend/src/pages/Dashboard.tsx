import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, DollarSign, Activity, LogOut, Star } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { logout } = useAuth();
  const [ticker, setTicker] = useState('RELIANCE.NS');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [predictionData, setPredictionData] = useState<any>(null);
  const [watchlist, setWatchlist] = useState<string[]>([]);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      const res = await api.get('/watchlist/');
      setWatchlist(res.data.watchlist);
    } catch (err) {
      console.error('Failed to fetch watchlist');
    }
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    runPrediction(ticker);
  };

  const runPrediction = async (targetTicker: string) => {
    setLoading(true);
    setError('');
    setPredictionData(null);
    setTicker(targetTicker);

    try {
      const response = await api.post(`/predict/${targetTicker}`);
      setPredictionData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch AI prediction.');
    } finally {
      setLoading(false);
    }
  };

  const toggleWatchlist = async (targetTicker: string) => {
    try {
      await api.post(`/watchlist/${targetTicker}`);
      fetchWatchlist();
    } catch (err) {
      console.error('Failed to update watchlist');
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      {/* Navigation */}
      <nav className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div className="flex items-center gap-2">
          <Activity className="text-emerald-400 w-8 h-8" />
          <h1 className="text-2xl font-bold">ProfLo AI</h1>
        </div>
        <button 
          onClick={logout} 
          className="flex items-center gap-2 text-gray-400 hover:text-red-400 transition-colors cursor-pointer"
        >
          <LogOut className="w-5 h-5" /> 
          <span>Logout</span>
        </button>
      </nav>

      {/* Search Bar */}
      <div className="max-w-3xl mx-auto mb-6">
        <form onSubmit={handlePredict} className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-3.5 text-gray-500 w-5 h-5" />
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Enter Stock Ticker (e.g., AAPL, RELIANCE.NS)"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-12 pr-4 py-3 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="bg-emerald-500 hover:bg-emerald-400 text-gray-950 px-8 py-3 rounded-lg font-bold transition-colors disabled:opacity-50 cursor-pointer flex items-center justify-center min-w-[120px]"
          >
            {loading ? <span>Running...</span> : <span>Predict</span>}
          </button>
        </form>
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-sm text-center">
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Watchlist Chips */}
      {watchlist.length > 0 && (
        <div className="max-w-3xl mx-auto mb-10 flex flex-wrap gap-2 items-center">
          <span className="text-sm text-gray-500 mr-2 flex items-center gap-1">
            <Star className="w-4 h-4" /> 
            <span>Saved:</span>
          </span>
          {watchlist.map((item) => (
            <button
              key={item}
              onClick={() => runPrediction(item)}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1 rounded-full text-sm font-medium transition-colors cursor-pointer border border-gray-700"
            >
              <span>{item}</span>
            </button>
          ))}
        </div>
      )}

      {/* Results Area */}
      {predictionData && (
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Target Asset Card */}
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg relative group">
              <button 
                onClick={() => toggleWatchlist(predictionData.ticker)}
                className="absolute top-4 right-4 p-2 rounded-full bg-gray-800/50 hover:bg-gray-700 transition-colors cursor-pointer"
                title="Toggle Watchlist"
              >
                <Star 
                  className={`w-5 h-5 transition-colors ${
                    watchlist.includes(predictionData.ticker) 
                      ? 'fill-yellow-400 text-yellow-400' 
                      : 'text-gray-400 group-hover:text-yellow-400'
                  }`} 
                />
              </button>
              <p className="text-gray-400 text-sm mb-1">Target Asset</p>
              <h3 className="text-3xl font-bold text-white">
                {predictionData.ticker}
              </h3>
            </div>

            {/* Predicted Price Card */}
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl shadow-lg">
              <p className="text-gray-400 text-sm mb-1">AI Predicted Price</p>
              <div className="flex items-center gap-2">
                <DollarSign className="text-emerald-400 w-6 h-6" />
                <h3 className="text-3xl font-bold text-emerald-400">
                  {predictionData.predicted_next_close ? predictionData.predicted_next_close.toFixed(2) : '---'}
                </h3>
              </div>
            </div>

            {/* Sentiment Card */}
            <div className={`border p-6 rounded-xl shadow-lg flex items-center justify-between ${
              predictionData.trend === 'BEARISH' ? 'bg-red-500/10 border-red-500/30 text-red-400' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}>
              <div>
                <p className="text-sm mb-1 opacity-80">AI Market Sentiment</p>
                <h3 className="text-3xl font-bold">{predictionData.trend || 'BULLISH'}</h3>
              </div>
              {predictionData.trend === 'BEARISH' ? <TrendingDown className="w-12 h-12" /> : <TrendingUp className="w-12 h-12" />}
            </div>
          </div>

          {/* Chart */}
          <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl h-[400px] shadow-lg flex flex-col">
            <h3 className="text-lg font-medium text-gray-300 mb-6">Recent Historical Price Action</h3>
            {predictionData.historical_data && predictionData.historical_data.length > 0 ? (
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={predictionData.historical_data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
                    <YAxis stroke="#9CA3AF" domain={['auto', 'auto']} tick={{ fill: '#9CA3AF' }} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff', borderRadius: '0.5rem' }} 
                      itemStyle={{ color: '#34D399', fontWeight: 'bold' }} 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#34D399" 
                      strokeWidth={2} 
                      dot={false} 
                      activeDot={{ r: 6, fill: '#34D399', stroke: '#111827', strokeWidth: 2 }} 
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500 bg-gray-950/50 rounded-lg border border-gray-800/50 border-dashed">
                <span>No historical chart data provided.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}