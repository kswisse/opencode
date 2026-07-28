'use client'

import { useEffect, useState } from 'react'

interface PipelineState {
  steps: Record<string, string>
  status: 'connected' | 'disconnected' | 'reconnecting'
  error: string | null
}

export function usePipeline(videoId: string | undefined): PipelineState {
  const [state, setState] = useState<PipelineState>({
    steps: {},
    status: 'disconnected',
    error: null,
  })

  useEffect(() => {
    if (!videoId) return

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || `ws://localhost:8000/ws/videos/${videoId}`
    let ws: WebSocket
    let reconnectTimer: ReturnType<typeof setTimeout>
    let attempt = 0
    let mounted = true

    function connect() {
      setState(prev => ({ ...prev, status: 'reconnecting' }))
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        if (!mounted) { ws.close(); return }
        attempt = 0
        setState(prev => ({ ...prev, status: 'connected' }))
      }

      ws.onmessage = (event) => {
        if (!mounted) return
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'pipeline.step_update' && data.step_name) {
            setState(prev => ({
              ...prev,
              steps: { ...prev.steps, [data.step_name]: data.step_status },
            }))
          } else if (data.type === 'pipeline.failed' && data.error) {
            setState(prev => ({ ...prev, error: data.error }))
          }
        } catch { /* ignore */ }
      }

      ws.onclose = () => {
        if (!mounted) return
        setState(prev => ({ ...prev, status: 'disconnected' }))
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000)
        attempt++
        reconnectTimer = setTimeout(connect, delay)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      mounted = false
      clearTimeout(reconnectTimer)
      ws?.close()
    }
  }, [videoId])

  return state
}
