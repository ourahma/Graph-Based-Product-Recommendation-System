'use client';

import React, { useState } from 'react';
import { Search, Sparkles, Package, TrendingUp } from 'lucide-react';
import { Card, LoadingSpinner, ErrorAlert, Badge } from '@/components/ui';
import * as api from '@/services/api';

type SearchType = 'customer' | 'product';

export default function Recommendations() {
  const [searchType, setSearchType] = useState<SearchType>('customer');
  const [searchId, setSearchId] = useState('');
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchId.trim()) return;

    try {
      setLoading(true);
      setError(null);

      let res;
      if (searchType === 'customer') {
        res = await api.getClientRecommendations(searchId);
        setRecommendations(res.data?.recommendations || []);
      } else {
        res = await api.getProductRecommendations(searchId);
        setRecommendations(res.data?.similar_products || []);
      }

      setSearched(true);
    } catch (err: any) {
      // Check if error is about algorithms not being run
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch recommendations';
      
      if (errorMessage.includes('algorithmes') || errorMessage.includes('algorithms')) {
        setError(
          `No recommendations computed yet. The GDS algorithms need to be executed first. Visit the Admin panel (/admin) and click "Run All Algorithms" to compute recommendations.`
        );
      } else if (err.response?.status === 404) {
        setError(`No ${searchType} found with ID "${searchId}". Please verify the ID exists in the database.`);
      } else {
        setError(errorMessage);
      }
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Search Section */}
      <Card>
        <h2 className="mb-6 flex items-center gap-2 text-2xl font-bold text-white">
          <Sparkles size={28} className="text-accent-400" />
          Find Recommendations
        </h2>

        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search Type Selection */}
          <div className="flex gap-4">
            {(['customer', 'product'] as const).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => {
                  setSearchType(type);
                  setRecommendations([]);
                  setSearched(false);
                }}
                className={`px-6 py-3 rounded-lg font-medium transition-all ${
                  searchType === type
                    ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg shadow-primary-500/50'
                    : 'bg-white/10 text-slate-300 hover:bg-white/20'
                }`}
              >
                {type === 'customer' ? '👤 Find for Customer' : '📦 Find for Product'}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
              <input
                type="text"
                placeholder={searchType === 'customer' ? 'Enter Customer ID...' : 'Enter Product ID...'}
                value={searchId}
                onChange={(e) => setSearchId(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg pl-12 pr-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !searchId.trim()}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>
      </Card>

      {error && <ErrorAlert message={error} />}

      {/* Results */}
      {loading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {searched && !loading && (
        <>
          {recommendations.length > 0 ? (
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-white">
                {searchType === 'customer'
                  ? `Recommendations for Customer #${searchId}`
                  : `Items Similar to Product #${searchId}`}
              </h3>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {recommendations.map((rec, idx) => (
                  <Card key={idx} variant="hover" className="relative overflow-hidden">
                    {/* Rank Badge */}
                    <div className="absolute top-4 right-4">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-accent-500 text-xs font-bold text-white">
                        {idx + 1}
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <Badge label="Recommended" variant="success" />
                      </div>

                      <div>
                        <h4 className="text-lg font-bold text-white">
                          {searchType === 'customer'
                            ? `Product #${rec?.product_id || rec?.id}`
                            : `Product #${rec?.product_id || rec?.id}`}
                        </h4>
                        <p className="mt-2 text-sm text-slate-400">
                          {rec?.category || 'General Category'}
                        </p>
                      </div>

                      <div className="space-y-2 pt-2 border-t border-white/10">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-400">Confidence Score</span>
                          <span className="text-lg font-bold text-primary-400">
                            {(rec?.score || rec?.similarity || 0.85).toFixed(3)}
                          </span>
                        </div>

                        <div className="h-2 w-full rounded-full bg-white/10">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-primary-500 to-accent-500"
                            style={{
                              width: `${((rec?.score || rec?.similarity || 0.85) * 100).toFixed(0)}%`,
                            }}
                          ></div>
                        </div>
                      </div>

                      {rec?.reason && (
                        <div className="rounded-lg bg-white/5 p-3 text-xs text-slate-300">
                          <p className="font-semibold text-slate-200">Why?</p>
                          <p className="mt-1">{rec.reason}</p>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card>
              <div className="py-12 text-center">
                <p className="text-slate-400">No recommendations found for this {searchType}.</p>
                <p className="mt-2 text-sm text-slate-500">Try a different ID or check if the data exists in the system.</p>
              </div>
            </Card>
          )}
        </>
      )}

      {!searched && !loading && (
        <Card className="py-12 text-center">
          <Sparkles size={48} className="mx-auto mb-4 text-accent-400" />
          <p className="text-slate-400">
            {searchType === 'customer'
              ? 'Search for a customer ID to get personalized product recommendations'
              : 'Search for a product ID to find similar items'}
          </p>
        </Card>
      )}
    </div>
  );
}
