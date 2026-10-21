import React from 'react';
import { mapStatus } from '../utils/status';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react';

interface StatusBadgeProps {
  status?: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const info = mapStatus(status);

  const sizeClasses = {
    sm: 'text-xs px-2.5 py-0.5 font-medium',
    md: 'text-xs px-3 py-1 font-semibold',
    lg: 'text-sm px-4 py-1.5 font-bold',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-3.5 h-3.5',
    lg: 'w-4 h-4',
  };

  const renderIcon = () => {
    if (!showIcon) return null;
    if (info.category === 'satisfied') {
      return <CheckCircle2 className={`${iconSizes[size]} shrink-0`} />;
    } else if (info.category === 'attention') {
      return <AlertTriangle className={`${iconSizes[size]} shrink-0`} />;
    }
    return <Info className={`${iconSizes[size]} shrink-0`} />;
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border transition-all ${sizeClasses[size]}`}
      style={{
        backgroundColor: info.bgColor,
        color: info.badgeColor,
        borderColor: info.borderColor,
      }}
      title={info.desc}
    >
      {renderIcon()}
      <span>{info.label}</span>
    </span>
  );
};
