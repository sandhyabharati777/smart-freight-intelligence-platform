import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/api'
import {
  Package, Truck, CheckCircle2, AlertTriangle,
  Clock, XCircle, BarChart3, Activity, TrendingUp, Zap
} from 'lucide-react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { StatCard, Spinner, ErrorState, RiskBar } from '@/components/ui'
import type { DashboardStats } from '@/types'

const STATUS_COLORS: Record<string, string> = {
  pending:    '#94a3b8',
  in_transit: '#60a5fa',
  customs:    '#fbbf24',
  delayed:    '#f87171',
  delivered:  '#34d399',
  cancelled:  '#f43f5e',
}

const RISK_COLORS: Record<string, string> = {
  low:      '#10b981',
  medium:   '#f59e0b',
  high:     '#ef4444',
  critical: '#dc2626',
}

const MODE_LABELS: Record<string, string> = {
  air: 'Air', sea: 'Sea', road: 'Road', rail: 'Rail', multimodal: 'Multi',
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs">
      <p className="text-slate-300 font-medium mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.fill ?? p.color }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}

export function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.stats,
    refetchInterval: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size={32} />
      </div>
    )
  }
  if (error || !stats) return <ErrorState message="Could not load dashboard metrics" />

  const statusChartData = Object.entries(stats.by_status).map(([k, v]) => ({
    name: k.replace('_', ' '),
    value: v,
    fill: STATUS_COLORS[k] ?? '#94a3b8',
  }))

  const modeChartData = Object.entries(stats.by_mode).map(([k, v]) => ({
    name: MODE_LABELS[k] ?? k,
    shipments: v,
    fill: '#6366f1',
  }))

  const riskChartData = Object.entries(stats.by_risk).map(([k, v]) => ({
    name: k,
    value: v,
    fill: RISK_COLORS[k] ?? '#94a3b8',
  }))

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title flex items-center gap-2">
          <BarChart3 size={24} className="text-brand-400" />
          Dashboard
        </h1>
        <p className="page-subtitle">Real-time freight intelligence overview</p>
      </div>

      {/* Top stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Shipments" value={stats.total_shipments} icon={Package} color="brand" />
        <StatCard label="In Transit"      value={stats.in_transit}       icon={Truck}         color="blue" trend="Active shipments" />
        <StatCard label="Delivered"       value={stats.delivered}        icon={CheckCircle2}  color="green" trend={`${stats.on_time_rate}% on-time`} />
        <StatCard label="Delayed"         value={stats.delayed}          icon={AlertTriangle} color="red" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Pending"        value={stats.pending}           icon={Clock}        color="slate" />
        <StatCard label="High Risk"      value={stats.high_risk_count}   icon={Zap}          color="red"   trend="High + Critical" />
        <StatCard label="ETA Conflicts"  value={stats.eta_conflict_count} icon={AlertTriangle} color="amber" />
        <StatCard label="New (7 days)"   value={stats.recent_shipments_7d} icon={TrendingUp}   color="brand" />
      </div>

      {/* Risk overview */}
      <div className="glass rounded-xl p-5 mb-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <Activity size={16} className="text-brand-400" />
          Average Fleet Risk Score
        </h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <RiskBar score={stats.avg_risk_score} />
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-slate-100">{Math.round(stats.avg_risk_score * 100)}%</p>
            <p className="text-xs text-slate-400">avg risk</p>
          </div>
        </div>
        {stats.stale_count > 0 && (
          <div className="mt-4 flex items-center gap-2 text-amber-400 text-xs">
            <AlertTriangle size={14} />
            {stats.stale_count} shipment{stats.stale_count !== 1 ? 's' : ''} have stale tracking data (no updates in 48h+)
          </div>
        )}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Status breakdown pie */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">By Status</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={statusChartData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {statusChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {statusChartData.map((d) => (
              <div key={d.name} className="flex items-center gap-1 text-xs text-slate-400">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.fill }} />
                {d.name} ({d.value})
              </div>
            ))}
          </div>
        </div>

        {/* Mode bar chart */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">By Transport Mode</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={modeChartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="shipments" radius={[4, 4, 0, 0]}>
                {modeChartData.map((entry, i) => (
                  <Cell key={i} fill="#6366f1" fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk distribution pie */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Risk Distribution</h2>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={riskChartData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {riskChartData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {riskChartData.map((d) => (
              <div key={d.name} className="flex items-center gap-1 text-xs text-slate-400">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.fill }} />
                {d.name} ({d.value})
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
