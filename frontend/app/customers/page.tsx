'use client';

import React, { useEffect, useState } from 'react';
import { Users, TrendingUp, Package, Search, Filter } from 'lucide-react';
import { Card, LoadingSpinner, ErrorAlert, StatCard, Badge } from '@/components/ui';
import * as api from '@/services/api';
import { formatNumber, formatCurrency } from "@/utils/utils";
("@/utils/utils");
interface Customer {
  client_id: string;
  name: string;
  purchases: number;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [customersRes, statsRes] = await Promise.all([
          api.getDiagnosticCustomers(200),
          api.getDiagnosticStats(),
        ]);

        // Deduplicate customers (remove duplicates by client_id)
        const uniqueCustomers = Array.from(
          new Map(
            (customersRes.data?.clients || []).map((c: Customer) => [c.client_id, c])
          ).values()
        ) as Customer[];

        setCustomers(uniqueCustomers);
        setStats(statsRes.data || {});
      } catch (err: any) {
        setError(err.message || 'Failed to load customer data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredCustomers = customers.filter((customer) => {
    // Search filter - if searchTerm is empty, all customers pass search
    const matchesSearch =
      !searchTerm ||
      (customer.name?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false) ||
      customer.client_id.toLowerCase().includes(searchTerm.toLowerCase());

    // Purchases filter based on type
    let matchesPurchases = true;
    if (filterType === 'no-purchases') {
      matchesPurchases = customer.purchases === 0;
    } else if (filterType === 'less-than-5') {
      matchesPurchases = customer.purchases > 0 && customer.purchases < 5;
    } else if (filterType === 'more-than-5') {
      matchesPurchases = customer.purchases > 5;
    }
    // 'all' doesn't filter by purchases

    return matchesSearch && matchesPurchases;
  });

  const customersWithPurchases = customers.filter((c) => c.purchases > 0).length;
  const avgPurchases =
    customers.length > 0
      ? (customers.reduce((sum, c) => sum + c.purchases, 0) / customers.length).toFixed(2)
      : 0;

  const statsData = stats || {};

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
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Unique Customers"
          value={formatNumber(statsData.unique_customer_ids || customers.length || 0)}
          icon={<Users className="text-primary-400" size={24} />}
        />
        <StatCard
          label="Total Purchases"
          value={formatNumber(statsData.total_purchases || 0)}
          icon={<Package className="text-green-400" size={24} />}
        />
        <StatCard
          label="Average Purchases/Customer"
          value={avgPurchases}
          icon={<TrendingUp className="text-blue-400" size={24} />}
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
                placeholder="Search by customer name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-lg bg-slate-700 px-4 py-2 pl-10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Filter size={20} className="text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="rounded-lg bg-slate-700 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-400"
            >
              <option value="all">All Customers</option>
              <option value="no-purchases">No Purchases</option>
              <option value="less-than-5">Less Than 5 Purchases</option>
              <option value="more-than-5">More Than 5 Purchases</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Customers Table */}
      <Card>
        <h2 className="mb-6 flex items-center gap-2 text-2xl font-bold text-white">
          <Users size={28} className="text-primary-400" />
          Customer List ({filteredCustomers.length} of {customers.length})
        </h2>

        {filteredCustomers.length === 0 ? (
          <div className="py-12 text-center text-gray-400">
            <Users size={48} className="mx-auto mb-4 opacity-50" />
            <p>No customers found matching your filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="min-w-full border-collapse">
              <thead className="sticky top-0 bg-slate-800 z-10">
                <tr className="border-b border-slate-600">
                  <th className="px-6 py-3 text-left text-sm font-semibold text-white">
                    Customer ID
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-white">
                    Name
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-white">
                    Total Purchases
                  </th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-white">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((customer, idx) => (
                  <tr
                    key={`${customer.client_id}-${idx}`}
                    className="border-b border-slate-700 hover:bg-slate-700/50 transition-colors"
                  >
                    <td className="px-6 py-4 text-white font-mono text-sm">
                      {customer.client_id}
                    </td>
                    <td className="px-6 py-4 text-white">
                      {customer.name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-center text-white">
                      <span className="inline-block rounded-lg bg-slate-700 px-3 py-1">
                        {customer.purchases}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {customer.purchases === 0 ? (
                        <Badge variant="secondary">No Purchases</Badge>
                      ) : customer.purchases === 1 ? (
                        <Badge variant="warning">1 Purchase</Badge>
                      ) : (
                        <Badge variant="success">{customer.purchases} Purchases</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}