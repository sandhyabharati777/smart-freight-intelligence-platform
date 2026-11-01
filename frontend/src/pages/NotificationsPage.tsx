import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/api'
import { Bell, BellOff, CheckCheck, AlertTriangle, Info, Activity, Clock, Truck } from 'lucide-react'
import { Spinner, EmptyState, ErrorState } from '@/components/ui'
import type { Notification, NotificationType } from '@/types'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'
import toast from 'react-hot-toast'

const TYPE_CONFIG: Record<NotificationType, { icon: React.ComponentType<any>; color: string; bg: string }> = {
  eta_conflict:   { icon: AlertTriangle, color: 'text-amber-400',  bg: 'bg-amber-500/10' },
  delay_risk:     { icon: Activity,      color: 'text-red-400',    bg: 'bg-red-500/10'   },
  status_change:  { icon: Truck,         color: 'text-blue-400',   bg: 'bg-blue-500/10'  },
  stale_update:   { icon: Clock,         color: 'text-slate-400',  bg: 'bg-slate-500/10' },
  system:         { icon: Info,          color: 'text-brand-400',  bg: 'bg-brand-500/10' },
}

export function NotificationsPage() {
  const qc = useQueryClient()

  const { data: notifications, isLoading, error } = useQuery<Notification[]>({
    queryKey: ['notifications'],
    queryFn: notificationsApi.list,
    refetchInterval: 30_000,
  })

  const markReadMutation = useMutation({
    mutationFn: ({ id, is_read }: { id: number; is_read: boolean }) =>
      notificationsApi.markRead(id, is_read),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const markAllMutation = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('All notifications marked as read')
    },
  })

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size={32} /></div>
  if (error) return <ErrorState message="Failed to load notifications" />

  const items = notifications ?? []
  const unread = items.filter((n) => !n.is_read)

  return (
    <div className="animate-fade-in max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <Bell size={24} className="text-brand-400" />
            Notifications
          </h1>
          <p className="page-subtitle">
            {unread.length > 0 ? `${unread.length} unread` : 'All caught up!'}
          </p>
        </div>
        {unread.length > 0 && (
          <button
            id="mark-all-read-btn"
            className="btn-secondary"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            {markAllMutation.isPending ? <Spinner size={14} /> : <CheckCheck size={16} />}
            Mark all read
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState
          title="No notifications"
          subtitle="You'll receive alerts for ETA conflicts, delays, and status changes"
          icon={BellOff}
        />
      ) : (
        <div className="space-y-2">
          {items.map((notif) => {
            const cfg = TYPE_CONFIG[notif.type] ?? TYPE_CONFIG.system
            const Icon = cfg.icon
            return (
              <div
                key={notif.id}
                className={clsx(
                  'glass rounded-xl p-4 flex items-start gap-4 transition-all duration-200',
                  !notif.is_read && 'border-white/15'
                )}
              >
                <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0', cfg.bg)}>
                  <Icon size={18} className={cfg.color} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={clsx('text-sm font-medium', notif.is_read ? 'text-slate-400' : 'text-slate-100')}>
                      {notif.title}
                    </p>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {!notif.is_read && (
                        <span className="w-2 h-2 rounded-full bg-brand-500 flex-shrink-0" />
                      )}
                      <span className="text-xs text-slate-500">
                        {formatDistanceToNow(new Date(notif.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{notif.message}</p>
                </div>
                <button
                  className="btn-ghost p-1.5 rounded-md flex-shrink-0 text-slate-500 hover:text-slate-200"
                  title={notif.is_read ? 'Mark as unread' : 'Mark as read'}
                  onClick={() => markReadMutation.mutate({ id: notif.id, is_read: !notif.is_read })}
                >
                  {notif.is_read ? <BellOff size={14} /> : <CheckCheck size={14} />}
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
