import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { shipmentsApi } from '@/api'
import {
  Package, Search, SlidersHorizontal, Plus, ChevronLeft,
  ChevronRight, ArrowUpDown, AlertTriangle, Clock
} from 'lucide-react'
import {
  StatusBadge, RiskBadge, ModeIcon, Spinner, EmptyState, ErrorState
} from '@/components/ui'
import type { ShipmentFilters, PaginatedShipments, ShipmentListItem } from '@/types'
import { format } from 'date-fns'
import clsx from 'clsx'

const STATUSES = ['', 'pending', 'in_transit', 'customs', 'delayed', 'delivered', 'cancelled']
const MODES = ['', 'air', 'sea', 'road', 'rail', 'multimodal']
const RISK_LEVELS = ['', 'low', 'medium', 'high', 'critical']

function SortButton({ col, filters, setFilters }: {
  col: string
  filters: ShipmentFilters
  setFilters: (f: ShipmentFilters) => void
}) {
  const isActive = filters.sort_by === col
  return (
    <button
      onClick={() =>
        setFilters({
          ...filters,
          sort_by: col,
          sort_dir: isActive && filters.sort_dir === 'desc' ? 'asc' : 'desc',
          page: 1,
        })
      }
      className={clsx('ml-1 inline-flex', isActive ? 'text-brand-400' : 'text-slate-600 hover:text-slate-400')}
    >
      <ArrowUpDown size={12} />
    </button>
  )
}

export function ShipmentsPage() {
  const [filters, setFilters] = useState<ShipmentFilters>({
    page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc',
  })
  const [searchInput, setSearchInput] = useState('')

  const queryParams = {
    ...filters,
    search: filters.search || undefined,
    status: filters.status || undefined,
    mode: filters.mode || undefined,
    risk_level: filters.risk_level || undefined,
  }

  const { data, isLoading, error } = useQuery<PaginatedShipments>({
    queryKey: ['shipments', filters],
    queryFn: () => shipmentsApi.list(queryParams),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setFilters((f) => ({ ...f, search: searchInput, page: 1 }))
  }

  const setFilter = (key: keyof ShipmentFilters, value: any) =>
    setFilters((f) => ({ ...f, [key]: value, page: 1 }))

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Package size={24} className="text-brand-400" />
            Shipments
          </h1>
          <p className="page-subtitle">
            {data ? `${data.total} shipment${data.total !== 1 ? 's' : ''} total` : 'Manage your freight'}
          </p>
        </div>
        <Link id="new-shipment-btn" to="/shipments/new" className="btn-primary">
          <Plus size={16} />
          New Shipment
        </Link>
      </div>

      {/* Search + Filters */}
      <div className="glass rounded-xl p-4 mb-4">
        <form onSubmit={handleSearch} className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              id="shipment-search"
              type="text"
              className="input pl-9"
              placeholder="Search tracking #, title, location, carrier…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>

          <select
            className="select w-36"
            value={filters.status ?? ''}
            onChange={(e) => setFilter('status', e.target.value as any)}
          >
            <option value="">All Statuses</option>
            {STATUSES.filter(Boolean).map((s) => (
              <option key={s} value={s}>{s.replace('_', ' ')}</option>
            ))}
          </select>

          <select
            className="select w-36"
            value={filters.mode ?? ''}
            onChange={(e) => setFilter('mode', e.target.value as any)}
          >
            <option value="">All Modes</option>
            {MODES.filter(Boolean).map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          <select
            className="select w-36"
            value={filters.risk_level ?? ''}
            onChange={(e) => setFilter('risk_level', e.target.value as any)}
          >
            <option value="">All Risk Levels</option>
            {RISK_LEVELS.filter(Boolean).map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>

          <button type="submit" className="btn-primary">
            <Search size={14} /> Search
          </button>

          {(filters.search || filters.status || filters.mode || filters.risk_level) && (
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setSearchInput('')
                setFilters({ page: 1, page_size: 20, sort_by: 'created_at', sort_dir: 'desc' })
              }}
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size={32} /></div>
      ) : error ? (
        <ErrorState message="Failed to load shipments" />
      ) : !data?.items.length ? (
        <EmptyState
          title="No shipments found"
          subtitle="Create your first shipment or adjust your filters"
          icon={Package}
        />
      ) : (
        <>
          <div className="table-container mb-4">
            <table className="table">
              <thead>
                <tr>
                  <th>
                    Tracking #
                    <SortButton col="tracking_number" filters={filters} setFilters={setFilters} />
                  </th>
                  <th>Title / Route</th>
                  <th>Mode</th>
                  <th>
                    Status
                    <SortButton col="status" filters={filters} setFilters={setFilters} />
                  </th>
                  <th>
                    Risk
                    <SortButton col="risk_score" filters={filters} setFilters={setFilters} />
                  </th>
                  <th>
                    ETA
                    <SortButton col="eta" filters={filters} setFilters={setFilters} />
                  </th>
                  <th>
                    Updated
                    <SortButton col="updated_at" filters={filters} setFilters={setFilters} />
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((s: ShipmentListItem) => (
                  <tr key={s.id}>
                    <td>
                      <Link
                        to={`/shipments/${s.id}`}
                        className="font-mono text-brand-400 hover:text-brand-300 font-medium text-xs"
                      >
                        {s.tracking_number}
                      </Link>
                      <div className="flex gap-1 mt-0.5">
                        {s.has_eta_conflict && (
                          <span title="ETA Conflict" className="text-amber-400">
                            <AlertTriangle size={12} />
                          </span>
                        )}
                        {s.is_stale && (
                          <span title="Stale tracking data" className="text-slate-500">
                            <Clock size={12} />
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <p className="text-slate-200 text-sm font-medium truncate max-w-[180px]">{s.title}</p>
                      <p className="text-slate-500 text-xs truncate max-w-[180px]">
                        {s.origin_location} → {s.destination_location}
                      </p>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <ModeIcon mode={s.mode} size={14} />
                        <span className="text-xs capitalize">{s.mode}</span>
                      </div>
                    </td>
                    <td><StatusBadge status={s.status} /></td>
                    <td><RiskBadge level={s.risk_level} score={s.risk_score} /></td>
                    <td className="text-xs text-slate-400">
                      {s.eta ? format(new Date(s.eta), 'MMM d, yyyy') : '—'}
                    </td>
                    <td className="text-xs text-slate-400">
                      {format(new Date(s.updated_at), 'MMM d, HH:mm')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-between text-sm">
              <p className="text-slate-400">
                Page {data.page} of {data.pages} ({data.total} total)
              </p>
              <div className="flex gap-2">
                <button
                  className="btn-secondary"
                  disabled={data.page <= 1}
                  onClick={() => setFilter('page', data.page - 1)}
                >
                  <ChevronLeft size={16} /> Previous
                </button>
                <button
                  className="btn-secondary"
                  disabled={data.page >= data.pages}
                  onClick={() => setFilter('page', data.page + 1)}
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
