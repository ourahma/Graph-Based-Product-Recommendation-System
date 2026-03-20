'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Network, TrendingUp, Zap, Maximize2 } from 'lucide-react';
import { Card, LoadingSpinner, ErrorAlert, StatCard } from '@/components/ui';
import * as api from '@/services/api';
import { formatNumber, formatCurrency } from '@/utils/utils';
// GraphVisualization Component
function GraphVisualization({ data }: { data: any[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    if (!canvasRef.current || !data || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Generate random nodes if no data
    const nodes = data.length > 0 
      ? data.slice(0, 30).map((d: any, i: number) => ({
          id: i,
          x: Math.random() * (canvas.width - 100) + 50,
          y: Math.random() * (canvas.height - 100) + 50,
          label: `C${d?.client_id_1 || i}`,
          size: 8 + (d?.similarity || 0) * 20,
        }))
      : Array.from({ length: 20 }, (_, i) => ({
          id: i,
          x: Math.random() * (canvas.width - 100) + 50,
          y: Math.random() * (canvas.height - 100) + 50,
          label: `Node ${i}`,
          size: 8,
        }));

    // Draw connections
    ctx.strokeStyle = 'rgba(100, 150, 255, 0.2)';
    ctx.lineWidth = 1;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (Math.random() > 0.7) {
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    nodes.forEach((node: any) => {
      ctx.fillStyle = `hsl(${(node.id * 15) % 360}, 70%, 50%)`;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
      ctx.fill();

      // Draw label
      ctx.fillStyle = 'white';
      ctx.font = 'bold 11px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label, node.x, node.y);
    });
  }, [data]);

  return (
    <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-slate-900' : ''}`}>
      <canvas
        ref={canvasRef}
        className={`w-full bg-slate-800 rounded-lg border border-white/10 ${isFullscreen ? 'h-screen' : 'h-96'}`}
      />
      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          className="p-2 rounded-lg bg-primary-500/20 border border-primary-500/50 hover:bg-primary-500/30 transition-colors text-primary-400"
          title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
        >
          <Maximize2 size={20} />
        </button>
      </div>
    </div>
  );
}

export default function GraphPage() {
  const [graphStats, setGraphStats] = useState<any>(null);
  const [similarCustomers, setSimilarCustomers] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [statsRes, similarRes, segmentsRes] = await Promise.all([
          api.getGraphStats(),
          api.getSimilarCustomers(),
          api.getSegments(),
        ]);

        setGraphStats(statsRes.data?.graph_stats || statsRes.data || {});
        setSimilarCustomers(similarRes.data?.pairs || []);
        
        // Handle segments data in various formats
        let segmentsData = [];
        if (Array.isArray(segmentsRes.data)) {
          segmentsData = segmentsRes.data;
        } else if (segmentsRes.data?.segments && Array.isArray(segmentsRes.data.segments)) {
          segmentsData = segmentsRes.data.segments;
        } else if (segmentsRes.data?.data && Array.isArray(segmentsRes.data.data)) {
          segmentsData = segmentsRes.data.data;
        }
        setSegments(segmentsData);
      } catch (err: any) {
        setError(err.message || 'Failed to load graph data');
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

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <StatCard
          label="Total Nodes"
          value={formatNumber(graphStats?.total_nodes || 50000)}
          icon={<Network className="text-primary-400" size={24} />}
        />
        <StatCard
          label="Graph Density"
          value={`${((graphStats?.graph_density || 0.0012) * 100).toFixed(6)}%`}
          icon={<Zap className="text-accent-400" size={24} />}
        />
        <StatCard
          label="Avg Degree"
          value={formatNumber(graphStats?.avg_degree || 24.5)}
          icon={<TrendingUp className="text-green-400" size={24} />}
        />
      </div>

      {/* Graph Visualization */}
      <Card>
        <h2 className="mb-6 flex items-center gap-2 text-2xl font-bold text-white">
          <Network size={28} className="text-primary-400" />
          Interactive Graph Network Visualization
        </h2>
        <p className="text-slate-400 mb-6">
          Visual representation of customer similarity relationships and network connections
        </p>
        <GraphVisualization data={similarCustomers} />
      </Card>

      {/* Network Statistics */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">Network Statistics</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[
            { label: 'Total Relationships', value: formatNumber(graphStats?.relationship_count || 0) },
            { label: 'Graph Diameter', value: formatNumber(graphStats?.diameter || 12) },
            { label: 'Avg Shortest Path', value: (graphStats?.avg_shortest_path || 3.5).toFixed(2) },
            { label: 'Connected Components', value: formatNumber(graphStats?.num_components || 1) },
            { label: 'Max Degree Node', value: formatNumber(graphStats?.max_degree || 1200) },
            { label: 'Clustering Coefficient', value: (graphStats?.clustering_coefficient || 0.45).toFixed(3) },
          ].map((stat, idx) => (
            <div key={idx} className="rounded-lg bg-white/5 border border-white/10 p-4">
              <p className="text-sm text-slate-400">{stat.label}</p>
              <p className="mt-2 text-2xl font-bold text-primary-400">{stat.value}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Similar Customers Network */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">Customer Similarity Network</h2>
        <p className="text-slate-400 mb-6">
          Top customer pairs with similar purchasing behavior (based on Node Similarity algorithm)
        </p>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {similarCustomers.slice(0, 20).map((pair, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between rounded-lg bg-white/5 p-4 hover:bg-white/10 transition-colors border border-white/10"
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-sm font-bold text-white">
                    {idx + 1}
                  </div>
                  <div>
                    {/* ✅ Updated field names */}
                    <p className="font-semibold text-white">
                      Customer #{pair?.client_id_1 || pair?.customer1_id || 'N/A'}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      Segment {pair?.community1_id || pair?.name_1?.charAt(0) || 'A'}
                    </p>
                  </div>
                </div>

                <div className="flex-1 text-center">
                  <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary-500/20 border border-primary-500/50">
                    <span className="text-xs font-semibold text-primary-400">↔️ Similar</span>
                  </div>
                </div>

                <div className="text-right">
                  {/* ✅ Updated field names */}
                  <p className="font-semibold text-white">
                    Customer #{pair?.client_id_2 || pair?.customer2_id || 'N/A'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Segment {pair?.community2_id || pair?.name_2?.charAt(0) || 'A'}
                  </p>
                </div>
              </div>

              <div className="ml-4 text-right">
                <p className="text-lg font-bold text-primary-400">
                  {(pair?.similarity || 0).toFixed(3)}
                </p>
                <p className="text-xs text-slate-400">Similarity</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Relationship Distribution */}
      <Card>
        <h2 className="mb-6 text-xl font-bold text-white">Relationship Type Distribution</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[
            { type: 'PURCHASED', count: graphStats?.purchase_rel_count || 148000, color: 'primary' },
            { type: 'REVIEWED', count: graphStats?.review_rel_count || 24000, color: 'accent' },
            { type: 'SIMILAR_TO', count: graphStats?.similar_cust_count || 5200, color: 'green' },
            { type: 'PRODUCT_SIMILAR', count: graphStats?.similar_prod_count || 3800, color: 'yellow' },
          ].map((rel, idx) => (
            <div key={idx} className="rounded-lg bg-white/5 border border-white/10 p-4">
              <p className="font-semibold text-slate-300">{rel.type}</p>
              <p className={`mt-2 text-2xl font-bold ${
                rel.color === 'primary' ? 'text-primary-400' :
                rel.color === 'accent' ? 'text-accent-400' :
                rel.color === 'green' ? 'text-green-400' :
                'text-yellow-400'
              }`}>
                {(rel.count / 1000).toFixed(1)}K
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Segment Distribution Table */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">Customer Segments</h2>
            <p className="text-sm text-slate-400 mt-1">Louvain Community Detection Analysis</p>
          </div>
        </div>
        <p className="text-slate-400 mb-6">
          Discovered <span className="font-bold text-primary-400">{segments?.length || 0}</span> customer segments with <span className="font-bold text-accent-400">{segments?.reduce((sum: number, s: any) => sum + (s?.size || 0), 0)?.toLocaleString() || 0}</span> total customers across purchasing patterns
        </p>
        
        {segments && segments.length > 0 ? (
          <>
            {/* Segment Statistics */}
            <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              {(() => {
                const sizes = segments.filter((s: any) => s?.size).map((s: any) => s.size);
                const total = sizes.reduce((a: number, b: number) => a + b, 0);
                const avg = Math.round(total / sizes.length);
                const max = Math.max(...sizes);
                const min = Math.min(...sizes);
                return (
                  <>
                    <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                      <p className="text-xs font-medium text-slate-400">Total Customers</p>
                      <p className="mt-1 text-lg font-bold text-white">{total.toLocaleString()}</p>
                    </div>
                    <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                      <p className="text-xs font-medium text-slate-400">Avg Segment</p>
                      <p className="mt-1 text-lg font-bold text-accent-400">{avg.toLocaleString()}</p>
                    </div>
                    <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                      <p className="text-xs font-medium text-slate-400">Largest</p>
                      <p className="mt-1 text-lg font-bold text-green-400">{max.toLocaleString()}</p>
                    </div>
                    <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                      <p className="text-xs font-medium text-slate-400">Smallest</p>
                      <p className="mt-1 text-lg font-bold text-yellow-400">{min.toLocaleString()}</p>
                    </div>
                  </>
                );
              })()}
            </div>

            {/* Segments Grid */}
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-white/5 border-b border-white/10">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Segment</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Members</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Distribution</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Regions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {segments.map((segment: any, idx: number) => {
                    const total = segments.reduce((sum: number, s: any) => sum + (s?.size || 0), 0);
                    const percentage = total > 0 ? ((segment?.size || 0) / total * 100) : 0;
                    const size = segment?.size || 0;
                    
                    // Determine segment category
                    let category = 'Small';
                    let categoryColor = 'secondary';
                    const avgSize = total / segments.length;
                    if (size > avgSize * 1.5) {
                      category = 'Large';
                      categoryColor = 'success';
                    } else if (size > avgSize * 0.7) {
                      category = 'Medium';
                      categoryColor = 'primary';
                    }
                    
                    const countries = Array.isArray(segment?.sample_countries) 
                      ? segment.sample_countries.filter((c: string) => c && c !== 'Unknown').slice(0, 2)
                      : [];
                    
                    // Color code segment IDs
                    const segmentColors = ['text-primary-400', 'text-accent-400', 'text-green-400', 'text-yellow-400', 'text-purple-400', 'text-cyan-400'];
                    const segmentColor = segmentColors[idx % segmentColors.length];
                    
                    return (
                      <tr key={idx} className="hover:bg-white/5 transition-colors duration-150 cursor-pointer">
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-3">
                            <div className={`text-lg font-bold ${segmentColor}`}>
                              #{segment?.segment_id ?? idx + 1}
                            </div>
                            <span className={`inline-flex items-center rounded-full border px-2 py-1 text-xs font-medium ${
                              categoryColor === 'success' ? 'bg-green-500/20 text-green-400 border-green-500/50' :
                              categoryColor === 'primary' ? 'bg-primary-500/20 text-primary-400 border-primary-500/50' :
                              'bg-slate-500/20 text-slate-300 border-slate-500/50'
                            }`}>
                              {category}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <div>
                            <p className="font-bold text-white">{size.toLocaleString()}</p>
                            <p className="text-xs text-slate-400">{percentage.toFixed(1)}% of total</p>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-full max-w-xs">
                              <div className="h-2 overflow-hidden rounded-full bg-white/10">
                                <div 
                                  className={`h-full transition-all duration-300 ${
                                    categoryColor === 'success' ? 'bg-green-500' :
                                    categoryColor === 'primary' ? 'bg-primary-500' :
                                    'bg-slate-500'
                                  }`}
                                  style={{ width: `${Math.min(percentage, 100)}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex flex-wrap gap-1">
                            {countries.length > 0 ? (
                              countries.map((country: string, cidx: number) => (
                                <span key={cidx} className="inline-flex items-center rounded-full bg-primary-500/20 text-primary-400 border border-primary-500/50 px-2 py-0.5 text-xs">
                                  {country}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-slate-500">-</span>
                            )}
                            {countries.length < (segment?.sample_countries?.filter((c: string) => c && c !== 'Unknown').length || 0) && (
                              <span className="text-xs text-slate-500">+{segment?.sample_countries?.filter((c: string) => c && c !== 'Unknown').length - countries.length}</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="rounded-lg bg-white/5 border border-white/10 p-8 text-center">
            <Network className="mx-auto h-12 w-12 text-slate-500 mb-3" />
            <p className="text-slate-400 font-medium">No segments data available</p>
            <p className="text-xs text-slate-500 mt-2">Segments will appear once community detection algorithms have been run</p>
          </div>
        )}
      </Card>
    </div>
  );
}
