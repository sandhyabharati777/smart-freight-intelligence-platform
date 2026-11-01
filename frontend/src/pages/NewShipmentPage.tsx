import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { shipmentsApi } from '@/api'
import { Package, ArrowLeft, Info } from 'lucide-react'
import { Spinner } from '@/components/ui'
import toast from 'react-hot-toast'
import type { ShipmentMode, ShipmentStatus } from '@/types'

const MODES: ShipmentMode[] = ['air', 'sea', 'road', 'rail', 'multimodal']
const STATUSES: ShipmentStatus[] = ['pending', 'in_transit', 'customs', 'delayed', 'delivered', 'cancelled']

export function NewShipmentPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [form, setForm] = useState({
    tracking_number: '',
    title: '',
    description: '',
    origin_location: '',
    destination_location: '',
    origin_country: '',
    destination_country: '',
    carrier: '',
    mode: 'sea' as ShipmentMode,
    status: 'pending' as ShipmentStatus,
    eta: '',
    etd: '',
    weight_kg: '',
    value_usd: '',
  })

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const mutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = {
        tracking_number: form.tracking_number.trim().toUpperCase(),
        title: form.title,
        description: form.description || undefined,
        origin_location: form.origin_location,
        destination_location: form.destination_location,
        origin_country: form.origin_country || undefined,
        destination_country: form.destination_country || undefined,
        carrier: form.carrier || undefined,
        mode: form.mode,
        status: form.status,
        eta: form.eta || undefined,
        etd: form.etd || undefined,
        weight_kg: form.weight_kg ? Number(form.weight_kg) : undefined,
        value_usd: form.value_usd ? Number(form.value_usd) : undefined,
      }
      return shipmentsApi.create(payload)
    },
    onSuccess: (data: any) => {
      qc.invalidateQueries({ queryKey: ['shipments'] })
      qc.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast.success(`Shipment ${data.tracking_number} created!`)
      navigate(`/shipments/${data.id}`)
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail.map((d: any) => d.msg).join(', '))
      } else {
        toast.error(detail ?? 'Failed to create shipment')
      }
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <div className="animate-fade-in max-w-2xl">
      <div className="mb-6">
        <button
          onClick={() => navigate('/shipments')}
          className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 text-sm mb-2"
        >
          <ArrowLeft size={14} /> Shipments
        </button>
        <h1 className="page-title flex items-center gap-2">
          <Package size={24} className="text-brand-400" />
          New Shipment
        </h1>
        <p className="page-subtitle">Create a new shipment record and start tracking</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic info */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Basic Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="label">Tracking Number *</label>
              <input
                id="new-tracking-number"
                className="input font-mono uppercase"
                placeholder="e.g. SF-AIR-001"
                value={form.tracking_number}
                onChange={set('tracking_number')}
                required
                minLength={4}
              />
            </div>
            <div className="col-span-2">
              <label className="label">Title / Cargo Description *</label>
              <input
                id="new-title"
                className="input"
                placeholder="e.g. Electronics Components - PCBs"
                value={form.title}
                onChange={set('title')}
                required
              />
            </div>
            <div className="col-span-2">
              <label className="label">Description</label>
              <textarea
                className="input resize-none"
                rows={2}
                placeholder="Optional details about this shipment"
                value={form.description}
                onChange={set('description')}
              />
            </div>
          </div>
        </div>

        {/* Route */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Route & Carrier</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Origin Location *</label>
              <input className="input" placeholder="e.g. Shanghai, China" value={form.origin_location} onChange={set('origin_location')} required />
            </div>
            <div>
              <label className="label">Destination Location *</label>
              <input className="input" placeholder="e.g. Rotterdam, Netherlands" value={form.destination_location} onChange={set('destination_location')} required />
            </div>
            <div>
              <label className="label">Origin Country</label>
              <input className="input" placeholder="China" value={form.origin_country} onChange={set('origin_country')} />
            </div>
            <div>
              <label className="label">Destination Country</label>
              <input className="input" placeholder="Netherlands" value={form.destination_country} onChange={set('destination_country')} />
            </div>
            <div>
              <label className="label">Carrier</label>
              <input className="input" placeholder="e.g. DHL, FedEx, COSCO" value={form.carrier} onChange={set('carrier')} />
            </div>
            <div>
              <label className="label">Transport Mode</label>
              <select className="select" value={form.mode} onChange={set('mode')}>
                {MODES.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Dates & Status */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Dates & Status</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Status</label>
              <select className="select" value={form.status} onChange={set('status')}>
                {STATUSES.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
              </select>
            </div>
            <div />
            <div>
              <label className="label">ETD (Departure)</label>
              <input type="datetime-local" className="input" value={form.etd} onChange={set('etd')} />
            </div>
            <div>
              <label className="label">ETA (Arrival)</label>
              <input type="datetime-local" className="input" value={form.eta} onChange={set('eta')} />
            </div>
          </div>
        </div>

        {/* Cargo */}
        <div className="glass rounded-xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">Cargo Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Weight (kg)</label>
              <input type="number" className="input" placeholder="0.0" value={form.weight_kg} onChange={set('weight_kg')} min="0" step="0.01" />
            </div>
            <div>
              <label className="label">Declared Value (USD)</label>
              <input type="number" className="input" placeholder="0.00" value={form.value_usd} onChange={set('value_usd')} min="0" step="0.01" />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex gap-3">
          <button type="button" className="btn-secondary flex-1" onClick={() => navigate('/shipments')}>
            Cancel
          </button>
          <button id="create-shipment-submit" type="submit" className="btn-primary flex-1" disabled={mutation.isPending}>
            {mutation.isPending ? <Spinner size={16} /> : <Package size={16} />}
            {mutation.isPending ? 'Creating…' : 'Create Shipment'}
          </button>
        </div>
      </form>
    </div>
  )
}
