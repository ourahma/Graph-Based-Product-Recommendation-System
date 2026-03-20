'use client';

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'hover';
}

export const Card: React.FC<CardProps> = ({ children, className = '', variant = 'default' }) => {
  return (
    <div
      className={`card ${
        variant === 'hover'
          ? 'hover:scale-105 hover:-translate-y-2 hover:shadow-accent-500/30'
          : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, change, icon }) => {
  return (
    <Card variant="hover">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <h3 className="mt-2 text-3xl font-bold text-white">{value}</h3>
          {change !== undefined && (
            <p className={`mt-2 text-sm ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {change >= 0 ? '+' : ''}{change}% from last month
            </p>
          )}
        </div>
        {icon && <div className="rounded-lg bg-white/10 p-3">{icon}</div>}
      </div>
    </Card>
  );
};

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-slate-700 border-t-primary-500"></div>
    </div>
  );
};

export const ErrorAlert: React.FC<{ message: string }> = ({ message }) => {
  return (
    <div className="rounded-lg bg-red-500/10 border border-red-500/50 p-4 text-red-400">
      <p className="font-medium">Error</p>
      <p className="text-sm">{message}</p>
    </div>
  );
};

export const Badge: React.FC<{
  label?: string;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'secondary';
  children?: React.ReactNode;
}> = ({ label, variant = 'primary', children }) => {
  const variants = {
    primary: 'bg-primary-500/20 text-primary-400 border-primary-500/50',
    success: 'bg-green-500/20 text-green-400 border-green-500/50',
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    danger: 'bg-red-500/20 text-red-400 border-red-500/50',
    info: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
    secondary: 'bg-slate-500/20 text-slate-300 border-slate-500/50',
  };

  return (
    <span className={`inline-block rounded-full border px-3 py-1 text-xs font-medium ${variants[variant]}`}>
      {label ?? children}
    </span>
  );
};
