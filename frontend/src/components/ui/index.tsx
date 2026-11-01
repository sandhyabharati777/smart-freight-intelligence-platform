import clsx from 'clsx'
import type { ShipmentStatus, RiskLevel, ShipmentMode } from '@/types'
import { 
  Plane, Ship, Truck, Train, GitMerge,
  AlertTriangle, CheckCircle2, Clock, XCircle,
  Package, Anchor
} from 'lucide-react'

const STATUS_CONFIG: Record<ShipmentStatus, { label: string; class: string }> = {
  pending:    { label: 'Pending',    class: 'badge-status-pending' },
  in_transit: { label: 'In Transit', class: 'badge-status-in_transit' },
  customs:    { label: 'Customs',    class: 'badge-status-customs' },
  delayed:    { label: 'Delayed',    class: 'badge-status-delayed' },
  delivered:  { label: 'Delivered',  class: 'badge-status-delivered' },
  cancelled:  { label: 'Cancelled',  class: 'badge-status-cancelled' },
}

const RISK_CONFIG: Record<RiskLevel, { label: string; class: string }> = {
  low:      { label: 'Low',      class: 'badge-risk-low' },
  medium:   { label: 'Medium',   class: 'badge-risk-medium' },
  high:     { label: 'High',     class: 'badge-risk-high' },
  critical: { label: 'Critical', class: 'badge-risk-critical' },
}

const MODE_ICONS: Record<ShipmentMode, React.ComponentType<{ size?: number; className?: string }>> = {
  air:        Plane,
  sea:        Anchor,
  road:       Truck,
  rail:       Train,
  multimodal: GitMerge,
}

export function StatusBadge({ status }: { status: ShipmentStatus }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, class: 'badge' }
  return <span className={cfg.class}>{cfg.label}</span>
}

export function RiskBadge({ level, score }: { level: RiskLevel; score?: number }) {
  const cfg = RISK_CONFIG[level] ?? { label: level, class: 'badge' }
  return (
    <span className={cfg.class}>
      {cfg.label}
      {score !== undefined && <span className="opacity-70 ml-1">({Math.round(score * 100)}%)</span>}
    </span>
  )
}

export function ModeIcon({ mode, size = 16 }: { mode: ShipmentMode; size?: number }) {
  const Icon = MODE_ICONS[mode] ?? Package
  return <Icon size={size} />
}

export function RiskBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = pct >= 70 ? 'bg-red-500' : pct >= 45 ? 'bg-orange-500' : pct >= 20 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>
    </div>
  )
}

export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <div
      className="inline-block animate-spin rounded-full border-2 border-white/20 border-t-brand-500"
      style={{ width: size, height: size }}
    />
  )
}

export function EmptyState({ title, subtitle, icon: Icon = Package }: {
  title: string; subtitle?: string; icon?: React.ComponentType<{ size?: number; className?: string }>
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4">
        <Icon size={28} className="text-slate-500" />
      </div>
      <h3 className="text-slate-300 font-medium">{title}</h3>
      {subtitle && <p className="text-slate-500 text-sm mt-1 max-w-xs">{subtitle}</p>}
    </div>
  )
}

export function ErrorState({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <AlertTriangle size={32} className="text-red-400 mb-3" />
      <p className="text-red-400 font-medium">Failed to load data</p>
      <p className="text-slate-500 text-sm mt-1">{message ?? 'Please try again'}</p>
    </div>
  )
}

export function StatCard({
  label, value, icon: Icon, trend, color = 'brand'
}: {
  label: string
  value: string | number
  icon?: React.ComponentType<{ size?: number; className?: string }>
  trend?: string
  color?: string
}) {
  const colorMap: Record<string, string> = {
    brand: 'text-brand-400',
    green: 'text-emerald-400',
    red: 'text-red-400',
    amber: 'text-amber-400',
    blue: 'text-blue-400',
    slate: 'text-slate-400',
  }
  return (
    <div className="stat-card group hover:border-white/20 transition-all duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="stat-label">{label}</p>
          <p className={clsx('stat-value mt-1', colorMap[color] ?? colorMap.brand)}>{value}</p>
          {trend && <p className="text-xs text-slate-500 mt-1">{trend}</p>}
        </div>
        {Icon && (
          <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-white/8 transition-colors">
            <Icon size={20} className={colorMap[color] ?? colorMap.brand} />
          </div>
        )}
      </div>
    </div>
  )
}
