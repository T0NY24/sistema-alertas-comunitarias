import React from 'react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ComponentType<{ className?: string }>;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
    loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
    title,
    value,
    icon: Icon,
    trend,
    color = 'blue',
    loading = false
}) => {
    const colorClasses = {
        blue: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
        green: 'text-green-400 bg-green-500/10 border-green-500/30',
        yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
        red: 'text-red-400 bg-red-500/10 border-red-500/30',
        purple: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    };

    const iconColorClasses = {
        blue: 'text-blue-400',
        green: 'text-green-400',
        yellow: 'text-yellow-400',
        red: 'text-red-400',
        purple: 'text-purple-400',
    };

    return (
        <div className="card hover:border-midnight-accent/50 transition-all duration-300 animate-fade-in">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                        {title}
                    </p>
                    {loading ? (
                        <div className="mt-2 h-8 w-24 bg-gray-700 animate-pulse rounded"></div>
                    ) : (
                        <p className="mt-2 text-3xl font-bold text-white">
                            {value}
                        </p>
                    )}
                    {trend && !loading && (
                        <div className="mt-2 flex items-center gap-1">
                            <span
                                className={`text-xs font-semibold ${trend.isPositive ? 'text-green-400' : 'text-red-400'
                                    }`}
                            >
                                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
                            </span>
                            <span className="text-xs text-gray-500">vs. anterior</span>
                        </div>
                    )}
                </div>
                <div className={`p-3 rounded-lg border ${colorClasses[color]}`}>
                    <Icon className={`w-6 h-6 ${iconColorClasses[color]}`} />
                </div>
            </div>
        </div>
    );
};
