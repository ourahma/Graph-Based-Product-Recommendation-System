'use client';

import React, { useEffect, useState } from 'react';
import { TrendingUp, Users, Package, Network } from 'lucide-react';
import { StatCard, Card, LoadingSpinner, ErrorAlert } from '@/components/ui';
import * as api from '@/services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { formatNumber, formatCurrency } from '@/utils/utils'; '@/utils/utils';


export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [graphStats, topRecommendations] = await Promise.all([
          api.getGraphStats(),
          api.getTopRecommendations(),
        ]);

        setStats({
          graphStats: graphStats.data?.graph_stats || graphStats.data || {},
          topRecommendations: Array.isArray(topRecommendations.data?.products) 
            ? topRecommendations.data.products 
            : topRecommendations.data || [],
        });
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard data');
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

  return (
    <div className="space-y-8 animate-fade-in">
      {error && <ErrorAlert message={error} />}

      {/* Demo Data Banner */}
      {stats?.graphStats?.is_demo_data && (
        <div className="rounded-lg bg-blue-950/30 border border-blue-500/50 p-4 flex items-start gap-3">
          <div className="text-blue-400 mt-1">ℹ️</div>
          <div>
            <p className="text-blue-300 font-semibold">Demo Data Active</p>
            <p className="text-blue-200 text-sm mt-1">
              Your Neo4j database appears to be empty. The dashboard is showing demo data for visualization purposes.
              To see real data:
            </p>
            <ul className="text-blue-200 text-sm mt-2 list-disc list-inside space-y-1">
              <li>Import CSV data into Neo4j (customers, products, orders, reviews)</li>
              <li>Run the Admin Panel algorithms from the <a href="/admin" className="underline hover:text-blue-100">Admin</a> page</li>
            </ul>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Customers"
          value={formatNumber(stats?.graphStats?.customer_count || 0)}
          icon={<Users className="text-primary-400" size={24} />}
        />
        <StatCard
          label="Total Products"
          value={formatNumber(stats?.graphStats?.product_count || 0)}
          icon={<Package className="text-accent-400" size={24} />}
        />
        <StatCard
          label="Total Relationships"
          value={formatNumber(stats?.graphStats?.relationship_count || 0)}
          icon={<Network className="text-green-400" size={24} />}
        />
        <StatCard
          label="Graph Density"
          value={`${((stats?.graphStats?.graph_density || 0) * 100).toFixed(6)}%`}
          icon={<TrendingUp className="text-blue-400" size={24} />}
        />
      </div>

      {/* Featured Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Top Products */}
        <Card className="lg:col-span-2">
          <h2 className="mb-4 text-xl font-bold text-white">🔥 Top Recommended Products</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {stats?.topRecommendations?.slice(0, 8).map((item: any, idx: number) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-lg bg-white/5 p-4 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 text-sm font-bold text-white">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="font-medium text-white">{item?.product_name+' #'+item.product_id || 'Product ' + (idx + 1)}</p>
                    <p className="text-sm text-slate-400">{item?.recommendation_score || 'High priority'}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-primary-400">{item?.score?.toFixed(2) || Math.random().toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Quick Stats */}
        <Card>
          <h2 className="mb-4 text-xl font-bold text-white">📊 Quick Stats</h2>
          <div className="space-y-4">
            <div className="rounded-lg bg-white/5 p-4">
              <p className="text-sm text-slate-400">Avg. Recommendations/Customer</p>
              <p className="text-2xl font-bold text-green-400 mt-1">
                {(stats?.graphStats?.avg_degree?.toFixed(2) || '5.2')}
              </p>
            </div>
            <div className="rounded-lg bg-white/5 p-4">
              <p className="text-sm text-slate-400">Graph Clusters</p>
              <p className="text-2xl font-bold text-accent-400 mt-1">
                {stats?.graphStats?.num_components || '12'}
              </p>
            </div>
            <div className="rounded-lg bg-white/5 p-4">
              <p className="text-sm text-slate-400">Recommandation Algorithms</p>
              <p className="text-2xl font-bold text-blue-400 mt-1">5</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Insights */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">💡 How the System Works</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            {
              title: 'Collaborative Filtering',
              desc: 'Finds customers with similar buying patterns',
            },
            {
              title: 'Graph Algorithms',
              desc: 'Uses PageRank, Louvain clustering, and Node Similarity',
            },
            {
              title: 'Real-time Updates',
              desc: 'Caches results for instant API responses',
            },
          ].map((insight, idx) => (
            <div key={idx} className="rounded-lg bg-white/5 p-4 border border-white/10">
              <p className="font-semibold text-primary-400">{insight.title}</p>
              <p className="mt-2 text-sm text-slate-300">{insight.desc}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
