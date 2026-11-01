import api from './client'
import type { AuthToken, User } from '@/types'

export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post<AuthToken>('/auth/register', data).then((r) => r.data),

  login: (email: string, password: string) =>
    api.post<AuthToken>('/auth/login', { email, password }).then((r) => r.data),

  me: () => api.get<User>('/auth/me').then((r) => r.data),
}

export const shipmentsApi = {
  list: (params: Record<string, unknown>) =>
    api.get('/shipments', { params }).then((r) => r.data),

  get: (id: number) => api.get(`/shipments/${id}`).then((r) => r.data),

  create: (data: Record<string, unknown>) =>
    api.post('/shipments', data).then((r) => r.data),

  update: (id: number, data: Record<string, unknown>) =>
    api.patch(`/shipments/${id}`, data).then((r) => r.data),

  delete: (id: number) => api.delete(`/shipments/${id}`),

  getEvents: (id: number) =>
    api.get(`/shipments/${id}/events`).then((r) => r.data),

  addEvent: (id: number, data: Record<string, unknown>) =>
    api.post(`/shipments/${id}/events`, data).then((r) => r.data),
}

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats').then((r) => r.data),
}

export const notificationsApi = {
  list: () => api.get('/notifications').then((r) => r.data),

  markRead: (id: number, is_read: boolean) =>
    api.patch(`/notifications/${id}`, { is_read }).then((r) => r.data),

  markAllRead: () => api.post('/notifications/mark-all-read'),
}
