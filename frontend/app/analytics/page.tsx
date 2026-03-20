'use client';

import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, PieChart as PieChartIcon } from 'lucide-react';
import { Card, LoadingSpinner, ErrorAlert, StatCard } from '@/components/ui';
import * as api from '@/services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { formatNumber, formatCurrency } from "@/utils/utils";
("@/utils/utils");
const COLORS = ['#0ea5e9', '#a855f7', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Analytics() {
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [graphStats, setGraphStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [categoriesRes, statsRes] = await Promise.all([
          api.getCategoryAnalytics(),
          api.getGraphStats(),
        ]);

        setCategoryData(categoriesRes.data?.categories || []);
        setGraphStats(statsRes.data?.graph_stats || statsRes.data || {});
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const categoryChartData = categoryData.slice(0, 10).map(cat => ({
    name: cat?.category || `Category ${cat?.id}`,
    products: cat?.product_count || 0,
    purchases: cat?.purchase_count || 0,
    revenue: cat?.total_revenue || 0,
  }));

  return (
    <div className="space-y-8 animate-fade-in">
      {error && <ErrorAlert message={error} />}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <StatCard
          label="Avg Products per Category"
          value={(graphStats?.avg_products_per_category || 45).toFixed(1)}
          icon={<BarChart3 className="text-primary-400" size={24} />}
        />
        <StatCard
          label="Most Popular Category"
          value={categoryData[0]?.category || 'Electronics'}
          icon={<TrendingUp className="text-accent-400" size={24} />}
        />
        <StatCard
          label="Categories"
          value={categoryData.length || 0}
          icon={<PieChartIcon className="text-green-400" size={24} />}
        />
      </div>

      {/* Category Distribution */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-6 text-xl font-bold text-white">Products by Category</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={categoryChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} tick={{ fill: '#cbd5e1' }} />
              <YAxis tick={{ fill: '#cbd5e1' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                }}
                cursor={{ fill: 'rgba(255,255,255,0.1)' }}
              />
              <Legend />
              <Bar dataKey="products" fill="#0ea5e9" name="Products" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h2 className="mb-6 text-xl font-bold text-white">Category Revenue Distribution</h2>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={categoryChartData}
                cx="50%"
                cy="50%"
                labelLine={true}
                label={({ name }) => `${name}`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="revenue"
              >
                {categoryChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(30, 41, 59, 0.8)',
                  border: '1px solid rgba(255,255,255,0.1)',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Category Table */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">📊 Detailed Category Analytics</h2>
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Category</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Products</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Total Purchases</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Revenue</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-slate-300">Avg Rating</th>
              </tr>
            </thead>
            <tbody>
              {categoryData.map((category, idx) => (
                <tr
                  key={idx}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-white font-medium">
                    {category?.category || `Category ${category?.id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300">
                    {category?.product_count || 0}
                  </td>
                  <td className="px-6 py-4 text-sm text-primary-400 font-semibold">
                    {category?.purchase_count || 0}
                  </td>
                  <td className="px-6 py-4 text-sm text-green-400 font-semibold">
                    ${(formatCurrency(category?.total_revenue || 0))}
                  </td>
                  <td className="px-6 py-4 text-sm text-yellow-400 font-semibold">
                    {(category?.avg_rating || 4.5).toFixed(1)} ⭐
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Graph Statistics */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">📈 Graph Database Metrics</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Total Nodes', value: formatNumber(graphStats?.total_nodes || 0 )},
            { label: 'Total Relationships', value: formatNumber(graphStats?.relationship_count || 0 )},
            { label: 'Graph Diameter', value: graphStats?.diameter || 0 },
            { label: 'Avg Shortest Path', value: (graphStats?.avg_shortest_path || 0).toFixed(2) },
          ].map((stat, idx) => (
            <div key={idx} className="rounded-lg bg-white/5 border border-white/10 p-4">
              <p className="text-sm text-slate-400">{stat.label}</p>
              <p className="mt-2 text-2xl font-bold text-primary-400">{stat.value}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
