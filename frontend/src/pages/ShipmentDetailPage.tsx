import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { shipmentsApi } from '@/api'
import {
  ArrowLeft, Package, AlertTriangle, Clock, CheckCircle2,
  MapPin, Calendar, Truck, Info, Plus, Trash2, Edit3, X
} from 'lucide-react'
import {
  StatusBadge, RiskBadge, ModeIcon, RiskBar, Spinner, ErrorState
} from '@/components/ui'
import type { Shipment, TrackingEvent, ShipmentStatus } from '@/types'
import { format, formatDistanceToNow } from 'date-fns'
import { useState } from 'react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const STATUS_OPTIONS: ShipmentStatus[] = [
  'pending', 'in_transit', 'customs', 'delayed', 'delivered', 'cancelled',
]

function TrackingTimeline({ events }: { events: TrackingEvent[] }) {
  return (
    <div className="space-y-0">
      {events.map((ev, i) => (
        <div key={ev.id} className="flex gap-4">
          {/* Timeline line + dot */}
          <div className="flex flex-col items-center">
            <div className={clsx(
              'w-3 h-3 rounded-full border-2 mt-1 flex-shrink-0',
              i === 0
                ? 'border-brand-400 bg-brand-500'
                : 'border-slate-600 bg-surface-900'
            )} />
            {i < events.length - 1 && (
              <div className="w-px flex-1 bg-white/10 mt-1 mb-1" />
            )}
          </div>
          {/* Event content */}
          <div className={clsx('pb-6', i === events.length - 1 && 'pb-0')}>
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={ev.status} />
              {ev.is_simulated && (
                <span className="text-xs text-amber-500 font-mono">[SIMULATED]</span>
              )}
            </div>
            <p className="text-sm text-slate-200 mt-1">{ev.description ?? '—'}</p>
            <div className="flex items-center gap-3 mt-1">
              {ev.location && (
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <MapPin size={10} /> {ev.location}
                </span>
              )}
              <span className="text-xs text-slate-500">
                {format(new Date(ev.event_time), 'MMM d, yyyy HH:mm')}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function RiskFactorsPanel({ factors, score, level }: {
  factors: string | null; score: number; level: string
}) {
  const parsed: string[] = (() => {
    if (!factors) return []
    try { return JSON.parse(factors) } catch { return [factors] }
  })()

  return (
    <div className="glass rounded-xl p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <AlertTriangle size={16} className="text-amber-400" />
        Risk Analysis
      </h3>
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <RiskBadge level={level as any} score={score} />
        </div>
        <RiskBar score={score} />
      </div>
      {parsed.length > 0 && (
        <ul className="space-y-1.5">
          {parsed.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
              <div className="w-1 h-1 rounded-full bg-slate-500 mt-1.5 flex-shrink-0" />
              {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function AddEventModal({
  shipmentId,
  onClose,
}: { shipmentId: number; onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    status: 'in_transit' as ShipmentStatus,
    location: '',
    description: '',
    is_simulated: true,
  })

  const mutation = useMutation({
    mutationFn: () => shipmentsApi.addEvent(shipmentId, form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['shipment', shipmentId] })
      toast.success('Tracking event added')
      onClose()
    },
    onError: () => toast.error('Failed to add event'),
  })

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass rounded-xl w-full max-w-md p-6 animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-slate-100">Add Tracking Event</h3>
          <button onClick={onClose} className="btn-ghost p-1.5 rounded-md">
            <X size={16} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Status</label>
            <select
              className="select"
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as ShipmentStatus }))}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Location</label>
            <input
              className="input"
              placeholder="e.g. Hamburg Port, Germany"
              value={form.location}
              onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            />
          </div>
          <div>
            <label className="label">Description</label>
            <input
              className="input"
              placeholder="e.g. Cargo offloaded, awaiting clearance"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_simulated"
              checked={form.is_simulated}
              onChange={(e) => setForm((f) => ({ ...f, is_simulated: e.target.checked }))}
              className="rounded"
            />
            <label htmlFor="is_simulated" className="text-sm text-slate-400">
              Mark as simulated data
            </label>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button
            className="btn-primary flex-1"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? <Spinner size={14} /> : null}
            Add Event
          </button>
        </div>
      </div>
    </div>
  )
}

export function ShipmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showAddEvent, setShowAddEvent] = useState(false)

  const { data: shipment, isLoading, error } = useQuery<Shipment>({
    queryKey: ['shipment', Number(id)],
    queryFn: () => shipmentsApi.get(Number(id)),
  })

  const deleteMutation = useMutation({
    mutationFn: () => shipmentsApi.delete(Number(id)),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['shipments'] })
      toast.success('Shipment deleted')
      navigate('/shipments')
    },
    onError: () => toast.error('Failed to delete shipment'),
  })

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size={32} /></div>
  if (error || !shipment) return <ErrorState message="Shipment not found" />

  const handleDelete = () => {
    if (confirm(`Delete shipment ${shipment.tracking_number}? This cannot be undone.`)) {
      deleteMutation.mutate()
    }
  }

  return (
    <div className="animate-fade-in max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link to="/shipments" className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 text-sm mb-2">
            <ArrowLeft size={14} /> Shipments
          </Link>
          <h1 className="page-title">{shipment.title}</h1>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className="font-mono text-brand-400 text-sm">{shipment.tracking_number}</span>
            <StatusBadge status={shipment.status} />
            <RiskBadge level={shipment.risk_level} score={shipment.risk_score} />
            {shipment.has_eta_conflict && (
              <span className="flex items-center gap-1 text-amber-400 text-xs">
                <AlertTriangle size={12} /> ETA Conflict
              </span>
            )}
            {shipment.is_stale && (
              <span className="flex items-center gap-1 text-slate-400 text-xs">
                <Clock size={12} /> Stale data
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            className="btn-secondary"
            onClick={() => setShowAddEvent(true)}
          >
            <Plus size={14} /> Add Event
          </button>
          <button
            className="btn-danger"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Shipment info */}
          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Package size={16} className="text-brand-400" />
              Shipment Details
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-slate-500 text-xs mb-0.5">Origin</p>
                <p className="text-slate-200 flex items-center gap-1">
                  <MapPin size={12} className="text-slate-400" />
                  {shipment.origin_location}
                  {shipment.origin_country && ` (${shipment.origin_country})`}
                </p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-0.5">Destination</p>
                <p className="text-slate-200 flex items-center gap-1">
                  <MapPin size={12} className="text-brand-400" />
                  {shipment.destination_location}
                  {shipment.destination_country && ` (${shipment.destination_country})`}
                </p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-0.5">Mode</p>
                <p className="text-slate-200 flex items-center gap-1.5 capitalize">
                  <ModeIcon mode={shipment.mode} size={14} /> {shipment.mode}
                </p>
              </div>
              <div>
                <p className="text-slate-500 text-xs mb-0.5">Carrier</p>
                <p className="text-slate-200">{shipment.carrier ?? '—'}</p>
              </div>
              {shipment.etd && (
                <div>
                  <p className="text-slate-500 text-xs mb-0.5">ETD</p>
                  <p className="text-slate-200 flex items-center gap-1">
                    <Calendar size={12} className="text-slate-400" />
                    {format(new Date(shipment.etd), 'MMM d, yyyy')}
                  </p>
                </div>
              )}
              {shipment.eta && (
                <div>
                  <p className="text-slate-500 text-xs mb-0.5">ETA</p>
                  <p className="text-slate-200 flex items-center gap-1">
                    <Calendar size={12} className="text-brand-400" />
                    {format(new Date(shipment.eta), 'MMM d, yyyy')}
                    <span className="text-slate-500 text-xs">
                      ({formatDistanceToNow(new Date(shipment.eta), { addSuffix: true })})
                    </span>
                  </p>
                </div>
              )}
              {shipment.actual_delivery && (
                <div>
                  <p className="text-slate-500 text-xs mb-0.5">Actual Delivery</p>
                  <p className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 size={12} />
                    {format(new Date(shipment.actual_delivery), 'MMM d, yyyy HH:mm')}
                  </p>
                </div>
              )}
              {shipment.weight_kg && (
                <div>
                  <p className="text-slate-500 text-xs mb-0.5">Weight</p>
                  <p className="text-slate-200">{shipment.weight_kg.toLocaleString()} kg</p>
                </div>
              )}
              {shipment.value_usd && (
                <div>
                  <p className="text-slate-500 text-xs mb-0.5">Declared Value</p>
                  <p className="text-slate-200">${shipment.value_usd.toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>

          {/* ETA Conflict warning */}
          {shipment.has_eta_conflict && (
            <div className="glass rounded-xl p-4 border border-amber-500/20">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-amber-300">ETA Conflict Detected</p>
                  <p className="text-xs text-slate-400 mt-0.5">{shipment.eta_conflict_reason}</p>
                </div>
              </div>
            </div>
          )}

          {/* Tracking timeline */}
          <div className="glass rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <Truck size={16} className="text-brand-400" />
                Tracking History
              </h3>
              <button
                className="btn-ghost text-xs gap-1"
                onClick={() => setShowAddEvent(true)}
              >
                <Plus size={12} /> Add
              </button>
            </div>
            {shipment.tracking_events && shipment.tracking_events.length > 0 ? (
              <TrackingTimeline events={shipment.tracking_events} />
            ) : (
              <p className="text-slate-500 text-sm text-center py-6">No tracking events yet</p>
            )}
          </div>
        </div>

        {/* Right: Risk + Meta */}
        <div className="space-y-6">
          <RiskFactorsPanel
            factors={shipment.risk_factors}
            score={shipment.risk_score}
            level={shipment.risk_level}
          />

          <div className="glass rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Info size={16} className="text-brand-400" />
              Metadata
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-300">{format(new Date(shipment.created_at), 'MMM d, yyyy')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Last Update</span>
                <span className="text-slate-300">{format(new Date(shipment.last_update_at), 'MMM d, HH:mm')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Stale</span>
                <span className={shipment.is_stale ? 'text-amber-400' : 'text-emerald-400'}>
                  {shipment.is_stale ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showAddEvent && (
        <AddEventModal
          shipmentId={Number(id)}
          onClose={() => setShowAddEvent(false)}
        />
      )}
    </div>
  )
}
