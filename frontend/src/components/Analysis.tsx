import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const Analysis: React.FC = () => {
  // Stock data (simplified)
  const stockData = [
    { date: '2024-01', price: 150, volume: 1200000 },
    { date: '2024-02', price: 165, volume: 1350000 },
    { date: '2024-03', price: 142, volume: 1100000 },
    { date: '2024-04', price: 178, volume: 1450000 },
    { date: '2024-05', price: 185, volume: 1600000 },
    { date: '2024-06', price: 172, volume: 1380000 },
    { date: '2024-07', price: 195, volume: 1750000 },
    { date: '2024-08', price: 188, volume: 1520000 },
    { date: '2024-09', price: 203, volume: 1820000 },
    { date: '2024-10', price: 210, volume: 1900000 },
    { date: '2024-11', price: 198, volume: 1650000 },
    { date: '2024-12', price: 215, volume: 2000000 },
  ];

  // Industry bar chart data
  const industryData = [
    { industry: 'Tech', revenue: 45000, growth: 12.5 },
    { industry: 'Finance', revenue: 38000, growth: 8.2 },
    { industry: 'Healthcare', revenue: 32000, growth: 15.3 },
    { industry: 'Energy', revenue: 28000, growth: -2.1 },
    { industry: 'Consumer', revenue: 35000, growth: 6.8 },
    { industry: 'Industrial', revenue: 25000, growth: 4.2 },
  ];

  // Portfolio pie chart data
  const portfolioData = [
    { name: 'Stocks', value: 45, color: '#0088FE' },
    { name: 'Bonds', value: 25, color: '#00C49F' },
    { name: 'Funds', value: 20, color: '#FFBB28' },
    { name: 'Cash', value: 10, color: '#FF8042' },
  ];

  return (
    <div className="p-6 bg-gray-50 min-h-full">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Financial Data Analysis</h1>
      
      {/* Stock Price Trend */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Stock Price Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={stockData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#2563eb" 
              strokeWidth={2}
              name="Price ($)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Industry Revenue Analysis */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Industry Revenue Analysis</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={industryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="industry" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="revenue" fill="#3b82f6" name="Revenue (Million)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Portfolio Distribution */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Portfolio Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={portfolioData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {portfolioData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Volume Analysis */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-8">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Volume Analysis</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={stockData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="volume" fill="#10b981" name="Volume" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8">
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h3 className="text-lg font-semibold text-gray-600">Total Assets</h3>
          <p className="text-3xl font-bold text-blue-600 mt-2">$2.5M</p>
          <p className="text-sm text-green-500 mt-1">+12.5%</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h3 className="text-lg font-semibold text-gray-600">Monthly Return</h3>
          <p className="text-3xl font-bold text-green-600 mt-2">+8.2%</p>
          <p className="text-sm text-green-500 mt-1">+2.1%</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h3 className="text-lg font-semibold text-gray-600">Risk Level</h3>
          <p className="text-3xl font-bold text-yellow-600 mt-2">Medium</p>
          <p className="text-sm text-gray-500 mt-1">Stable</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <h3 className="text-lg font-semibold text-gray-600">Positions</h3>
          <p className="text-3xl font-bold text-purple-600 mt-2">24</p>
          <p className="text-sm text-blue-500 mt-1">+3 New</p>
        </div>
      </div>
    </div>
  );
};

export default Analysis; 