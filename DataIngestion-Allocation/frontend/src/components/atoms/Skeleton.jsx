import React from 'react';

export function Skeleton({ width = 'w-full', height = 'h-4', rounded = true, className = '' }) {
  return (
    <div 
      className={`bg-gray-200 animate-pulse ${width} ${height} ${rounded ? 'rounded' : ''} ${className}`}
    />
  );
}
