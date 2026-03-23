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
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const buildGraph = (width: number, height: number) => {
      if (!Array.isArray(data) || data.length === 0) {
        const nodes = Array.from({ length: 20 }, (_, i) => ({
          id: `node-${i}`,
          x: Math.random() * (width - 100) + 50,
          y: Math.random() * (height - 100) + 50,
          label: `Node ${i}`,
          size: 8,
        }));
        return { nodes, edges: [] as any[] };
      }

      const maxEdges = 60;
      const maxNodes = 30;
      const edges = data
        .filter((d: any) => d?.customer1_id || d?.client_id_1)
        .sort((a: any, b: any) => (b?.similarity || 0) - (a?.similarity || 0))
        .slice(0, maxEdges)
        .map((d: any) => ({
          source: String(d?.customer1_id || d?.client_id_1),
          target: String(d?.customer2_id || d?.client_id_2),
          similarity: d?.similarity || 0,
        }));

      const nodeMap = new Map<string, any>();
      for (const e of edges) {
        if (nodeMap.size < maxNodes && !nodeMap.has(e.source)) {
          nodeMap.set(e.source, {
            id: e.source,
            x: Math.random() * (width - 100) + 50,
            y: Math.random() * (height - 100) + 50,
            label: `C${e.source}`,
            size: 14,
            vx: 0,
            vy: 0,
          });
        }
        if (nodeMap.size < maxNodes && !nodeMap.has(e.target)) {
          nodeMap.set(e.target, {
            id: e.target,
            x: Math.random() * (width - 100) + 50,
            y: Math.random() * (height - 100) + 50,
            label: `C${e.target}`,
            size: 14,
            vx: 0,
            vy: 0,
          });
        }
        if (nodeMap.size >= maxNodes) break;
      }

      const nodes = Array.from(nodeMap.values());
      const nodeSet = new Set(nodes.map((n) => n.id));
      const prunedEdges = edges.filter((e) => nodeSet.has(e.source) && nodeSet.has(e.target));

      return { nodes, edges: prunedEdges };
    };

    const runLayout = (nodes: any[], edges: any[], width: number, height: number) => {
      const iterations = 260;
      const repulsion = 2600;
      const spring = 0.0012;
      const damping = 0.85;

      for (let i = 0; i < iterations; i++) {
        // Repulsion
        for (let a = 0; a < nodes.length; a++) {
          for (let b = a + 1; b < nodes.length; b++) {
            const n1 = nodes[a];
            const n2 = nodes[b];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist2 = dx * dx + dy * dy + 0.01;
            const force = repulsion / dist2;
            const fx = (force * dx);
            const fy = (force * dy);
            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }
        }

        // Springs
        for (const e of edges) {
          const n1 = nodes.find((n) => n.id === e.source);
          const n2 = nodes.find((n) => n.id === e.target);
          if (!n1 || !n2) continue;
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
          const desired = 160;
          const force = spring * (dist - desired);
          const fx = (force * dx) / dist;
          const fy = (force * dy) / dist;
          n1.vx += fx;
          n1.vy += fy;
          n2.vx -= fx;
          n2.vy -= fy;
        }

        // Simple collision resolution to reduce overlaps.
        for (let a = 0; a < nodes.length; a++) {
          for (let b = a + 1; b < nodes.length; b++) {
            const n1 = nodes[a];
            const n2 = nodes[b];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.sqrt(dx * dx + dy * dy) + 0.01;
            const minDist = (n1.size + n2.size) * 1.4;
            if (dist < minDist) {
              const push = (minDist - dist) * 0.5;
              const nx = dx / dist;
              const ny = dy / dist;
              n1.x -= nx * push;
              n1.y -= ny * push;
              n2.x += nx * push;
              n2.y += ny * push;
            }
          }
        }

        // Integrate
        for (const n of nodes) {
          n.vx *= damping;
          n.vy *= damping;
          n.x += n.vx;
          n.y += n.vy;
          const pad = 26;
          n.x = Math.min(width - pad, Math.max(pad, n.x));
          n.y = Math.min(height - pad, Math.max(pad, n.y));
        }
      }
    };

    const drawGraph = () => {
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(1, rect.width);
      const height = Math.max(1, rect.height);
      const dpr = window.devicePixelRatio || 1;

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);

      const { nodes, edges } = buildGraph(width, height);
      runLayout(nodes, edges, width, height);

      // Draw edges (actual similarity pairs)
      ctx.strokeStyle = 'rgba(100, 150, 255, 0.25)';
      for (const e of edges) {
        const n1 = nodes.find((n) => n.id === e.source);
        const n2 = nodes.find((n) => n.id === e.target);
        if (!n1 || !n2) continue;
        const alpha = Math.min(0.8, 0.15 + (e.similarity || 0) * 0.8);
        ctx.lineWidth = Math.max(1, (e.similarity || 0) * 3);
        ctx.strokeStyle = `rgba(100, 150, 255, ${alpha})`;
        ctx.beginPath();
        ctx.moveTo(n1.x, n1.y);
        ctx.lineTo(n2.x, n2.y);
        ctx.stroke();
      }

      // Draw nodes
      nodes.forEach((node: any, idx: number) => {
        ctx.fillStyle = `hsl(${(idx * 15) % 360}, 70%, 50%)`;
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
    };

    drawGraph();

    const resizeObserver = new ResizeObserver(() => {
      drawGraph();
    });
    resizeObserver.observe(canvas);

    const handleResize = () => drawGraph();
    window.addEventListener('resize', handleResize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [data, isFullscreen]);

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
          api.getSegments(0),
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

  const similarityValues = similarCustomers.map((p) => p?.similarity ?? 0);
  const similarityCount = similarityValues.length;
  const similaritySum = similarityValues.reduce((sum, v) => sum + v, 0);
  const similarityAvg = similarityCount > 0 ? similaritySum / similarityCount : 0;
  const similarityMin = similarityCount > 0 ? Math.min(...similarityValues) : 0;
  const similarityMax = similarityCount > 0 ? Math.max(...similarityValues) : 0;
  const uniqueCustomers = new Set(
    similarCustomers.flatMap((p) => [
      p?.client_id_1,
      p?.customer1_id,
      p?.client_id_2,
      p?.customer2_id,
    ].filter(Boolean))
  ).size;

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
            { label: 'Similarity Pairs', value: formatNumber(similarityCount) },
            { label: 'Unique Customers', value: formatNumber(uniqueCustomers) },
            { label: 'Avg Similarity', value: similarityAvg.toFixed(3) },
            { label: 'Min Similarity', value: similarityMin.toFixed(3) },
            { label: 'Max Similarity', value: similarityMax.toFixed(3) },
            { label: 'Total Similarity', value: similaritySum.toFixed(2) },
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
          {similarCustomers.map((pair, idx) => (
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
                const max = Math.max(...sizes);
                const min = Math.min(...sizes);
                return (
                  <>
                    <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                      <p className="text-xs font-medium text-slate-400">Total Customers</p>
                      <p className="mt-1 text-lg font-bold text-white">{total.toLocaleString()}</p>
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
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Genders</th>
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
                      ? Array.from(new Set<string>(
                          (segment.sample_countries as string[]).filter(
                            (c): c is string => Boolean(c) && c !== 'Unknown'
                          )
                        ))
                      : [];
                    const genders = Array.isArray(segment?.sample_genders)
                      ? Array.from(new Set<string>(
                          (segment.sample_genders as string[]).filter(
                            (g): g is string => Boolean(g) && g !== 'Unknown' && g !== 'N/A'
                          )
                        ))
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
                            
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex flex-wrap gap-1">
                            {genders.length > 0 ? (
                              genders.map((gender: string, gidx: number) => (
                                <span key={gidx} className="inline-flex items-center rounded-full bg-accent-500/20 text-accent-400 border border-accent-500/50 px-2 py-0.5 text-xs">
                                  {gender}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-slate-500">-</span>
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
