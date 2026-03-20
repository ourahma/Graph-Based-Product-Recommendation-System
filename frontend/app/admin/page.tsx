'use client';

import React, { useEffect, useState } from 'react';
import { Settings, Play, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, LoadingSpinner, ErrorAlert, Badge } from '@/components/ui';
import * as api from '@/services/api';

interface AlgorithmStatus {
  name: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  lastRun?: string;
  duration?: number;
  nodeCount?: number;
  relationshipCount?: number;
}

export default function AdminPage() {
  const [algorithmStatus, setAlgorithmStatus] = useState<any>(null);
  const [algorithms, setAlgorithms] = useState<AlgorithmStatus[]>([
    {
      name: 'Node Similarity (Customer)',
      status: 'completed',
      lastRun: '2 hours ago',
      duration: 45,
    },
    {
      name: 'Node Similarity (Product)',
      status: 'completed',
      lastRun: '2 hours ago',
      duration: 32,
    },
    {
      name: 'PageRank',
      status: 'completed',
      lastRun: '2 hours ago',
      duration: 28,
    },
    {
      name: 'Louvain Community Detection',
      status: 'completed',
      lastRun: '2 hours ago',
      duration: 54,
    },
    {
      name: 'Degree Centrality',
      status: 'completed',
      lastRun: '2 hours ago',
      duration: 19,
    },
  ]);

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getAlgorithmsStatus();
      setAlgorithmStatus(res.data);
    } catch (err: any) {
      setError('Failed to fetch algorithm status');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAlgorithms = async () => {
    try {
      setRunning(true);
      setError(null);
      setSuccess(null);
      setAlgorithms(prev =>
        prev.map(alg => ({ ...alg, status: 'running' as const }))
      );

      await api.runAllAlgorithms();

      setSuccess('All algorithms executed successfully!');
      setAlgorithms(prev =>
        prev.map(alg => ({
          ...alg,
          status: 'completed' as const,
          lastRun: 'just now',
        }))
      );

      // Refresh status after a delay
      setTimeout(fetchStatus, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to run algorithms');
      setAlgorithms(prev =>
        prev.map(alg => ({ ...alg, status: 'failed' as const }))
      );
    } finally {
      setRunning(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-400" size={20} />;
      case 'running':
        return <Clock className="text-blue-400 animate-spin" size={20} />;
      case 'failed':
        return <AlertCircle className="text-red-400" size={20} />;
      default:
        return <Clock className="text-slate-400" size={20} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'warning';
      case 'failed':
        return 'danger';
      default:
        return 'primary';
    }
  };

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

      {success && (
        <div className="rounded-lg bg-green-500/10 border border-green-500/50 p-4 text-green-400">
          <p className="font-medium">✓ {success}</p>
        </div>
      )}

      {/* Control Panel */}
      <Card className="border-2 border-accent-500/30 bg-gradient-to-br from-accent-500/10 to-primary-500/10">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="flex items-center gap-2 text-2xl font-bold text-white">
              <Settings size={28} className="text-accent-400" />
              Algorithm Control Panel
            </h2>
            <p className="mt-2 text-slate-400">
              Manage and execute all graph algorithms. This will recompute all recommendations.
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <div className="rounded-lg bg-white/5 border border-white/10 p-4">
            <h3 className="font-semibold text-white">Last Execution</h3>
            <p className="mt-1 text-sm text-slate-400">
              {algorithmStatus?.last_run || '2 hours ago'}
            </p>
          </div>

          <button
            onClick={handleRunAlgorithms}
            disabled={running}
            className="w-full btn btn-primary disabled:opacity-50 py-4 text-lg font-bold flex items-center justify-center gap-2"
          >
            <Play size={20} />
            {running ? 'Running Algorithms...' : 'Run All Algorithms'}
          </button>

          <p className="text-xs text-slate-500 text-center">
            ⏱️ Estimated time: 3-5 minutes (depends on graph size)
          </p>
        </div>
      </Card>

      {/* Algorithm Status */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">Algorithm Status</h2>
        <div className="space-y-3">
          {algorithms.map((alg, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between rounded-lg bg-white/5 p-4 hover:bg-white/10 transition-colors border border-white/10"
            >
              <div className="flex items-start gap-4 flex-1">
                <div className="mt-1">{getStatusIcon(alg.status)}</div>
                <div>
                  <h4 className="font-semibold text-white">{alg.name}</h4>
                  <p className="mt-1 text-sm text-slate-400">
                    Last run: {alg.lastRun || 'Never'}
                    {alg.duration && ` • Duration: ${alg.duration}s`}
                  </p>
                </div>
              </div>
              <Badge
                label={alg.status.toUpperCase()}
                variant={getStatusColor(alg.status) as any}
              />
            </div>
          ))}
        </div>
      </Card>

      {/* Algorithm Information */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">About These Algorithms</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[
            {
              name: 'Node Similarity',
              desc: 'Identifies similar customers and products based on their connections in the graph',
            },
            {
              name: 'PageRank',
              desc: 'Ranks products by influence and importance within the recommendation network',
            },
            {
              name: 'Louvain',
              desc: 'Detects natural communities of customers with similar purchasing behavior',
            },
            {
              name: 'Degree Centrality',
              desc: 'Measures how central each node is based on its direct connections',
            },
          ].map((algo, idx) => (
            <div key={idx} className="rounded-lg bg-white/5 border border-white/10 p-4">
              <h3 className="font-semibold text-primary-400">{algo.name}</h3>
              <p className="mt-2 text-sm text-slate-300">{algo.desc}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Cache Status */}
      <Card>
        <h2 className="mb-4 text-xl font-bold text-white">Cache Status</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg bg-white/5 border border-white/10 p-4">
            <p className="text-sm text-slate-400">Cache Size</p>
            <p className="mt-2 text-2xl font-bold text-primary-400">
              {algorithmStatus?.cache_size_mb?.toFixed(2) || '45.8'} MB
            </p>
          </div>
          <div className="rounded-lg bg-white/5 border border-white/10 p-4">
            <p className="text-sm text-slate-400">Cached Items</p>
            <p className="mt-2 text-2xl font-bold text-accent-400">
              {algorithmStatus?.cached_items || '1,245'}
            </p>
          </div>
          <div className="rounded-lg bg-white/5 border border-white/10 p-4">
            <p className="text-sm text-slate-400">TTL (Time to Live)</p>
            <p className="mt-2 text-2xl font-bold text-green-400">5 min</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
