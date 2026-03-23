'use client';

import React, { useEffect, useState } from 'react';
import { Package, TrendingUp, Star, Search, Filter } from 'lucide-react';
import { Card, LoadingSpinner, ErrorAlert, StatCard, Badge } from '@/components/ui';
import * as api from '@/services/api';
import { formatNumber } from '@/utils/utils';

interface Product {
  product_id: string;
  product_name: string;
  category?: string;
  price?: number;
  rating?: number;
  review_count?: number;
  purchase_count?: number;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch products from diagnostic endpoint
        const productsRes = await api.getDiagnosticProducts(500);
        
        const productsList = (productsRes.data?.products || []).map((p: any, idx: number) => ({
          product_id: p.product_id || String(idx),
          product_name: p.product_name || 'Unknown Product',
          category: p.category,
          price: p.price,
          rating: p.rating,
          review_count: p.review_count,
          purchase_count: p.purchase_count,
        }));

        const limitedList = productsList.slice(0, 500);
        setProducts(limitedList);
        setAllProducts(productsList);
      } catch (err: any) {
        console.error('Error fetching products:', err);
        setError(err.message || 'Failed to load product data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredProducts = products.filter((product) => {
    const matchesSearch =
      product.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.product_id.includes(searchTerm);
    
    const matchesCategory =
      selectedCategory === 'all' || product.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const categories = Array.from(
    new Set(allProducts.map((p) => p.category).filter(Boolean))
  ) as string[];

  const avgRating =
    allProducts.length > 0
      ? (allProducts.reduce((sum, p) => sum + (p.rating || 0), 0) / allProducts.length).toFixed(2)
      : 0;

  const totalReviews = allProducts.reduce((sum, p) => sum + (p.review_count || 0), 0);
  const totalPurchases = allProducts.reduce((sum, p) => sum + (p.purchase_count || 0), 0);

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

      {/* Header Stats */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Products"
          value={formatNumber(allProducts.length)}
          icon={<Package className="text-primary-400" size={24} />}
        />
        <StatCard
          label="Categories"
          value={formatNumber(categories.length)}
          icon={<TrendingUp className="text-accent-400" size={24} />}
        />
        <StatCard
          label="Total Purchases"
          value={formatNumber(totalPurchases)}
          icon={<TrendingUp className="text-green-400" size={24} />}
        />
        <StatCard
          label="Total Reviews"
          value={formatNumber(totalReviews)}
          icon={<Star className="text-yellow-400" size={24} />}
        />
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-3 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search by product name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg bg-slate-700 px-4 py-2 pl-10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="rounded-lg bg-slate-700 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Products Grid */}
      <Card>
        <h2 className="mb-6 flex items-center gap-2 text-2xl font-bold text-white">
          <Package size={28} className="text-primary-400" />
          Products ({filteredProducts.length} of {allProducts.length})
        </h2>

        {filteredProducts.length === 0 ? (
          <div className="py-12 text-center text-gray-400">
            <Package size={48} className="mx-auto mb-4 opacity-50" />
            <p>No products found matching your filters.</p>
          </div>
        ) : (
          <div className="max-h-[70vh] overflow-y-auto pr-2">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredProducts.map((product, idx) => (
              <div
                key={`${product.product_id}-${idx}`}
                className="rounded-lg border border-slate-600 bg-slate-700 p-6 hover:border-primary-400 transition-colors"
              >
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white truncate">
                      {product.product_name}
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">
                      ID: {product.product_id}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  {product.category && (
                    <div>
                      <p className="text-sm text-gray-400">Category</p>
                      <Badge variant="info">{product.category}</Badge>
                    </div>
                  )}

                  {product.rating !== undefined && (
                    <div className="flex items-center gap-2">
                      <Star size={16} className="text-yellow-400" />
                      <span className="text-white font-medium">
                        {product.rating.toFixed(2)}
                      </span>
                    </div>
                  )}

                  {product.purchase_count !== undefined && (
                    <div className="flex items-center gap-2 text-green-400">
                      <Package size={16} />
                      <span className="text-sm">
                        {product.purchase_count} purchases
                      </span>
                    </div>
                  )}

                  {product.review_count !== undefined && (
                    <div className="text-sm text-gray-400">
                      {product.review_count} reviews
                    </div>
                  )}

                  {product.price !== undefined && (
                    <div>
                      <p className="text-sm text-gray-400">Price</p>
                      <p className="text-lg font-semibold text-green-400">
                        ${product.price.toFixed(2)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
