export class PipelineWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  private attempt = 0
  private maxAttempts = 5

  constructor(
    private url: string,
    private onMessage: (data: any) => void,
    private onStatusChange?: (status: 'connected' | 'disconnected' | 'reconnecting') => void,
  ) {}

  connect() {
    this.onStatusChange?.('reconnecting')
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.attempt = 0
      this.onStatusChange?.('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.onMessage(data)
      } catch { /* ignore parse errors */ }
    }

    this.ws.onclose = () => {
      this.onStatusChange?.('disconnected')
      this.scheduleReconnect()
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  private scheduleReconnect() {
    if (this.attempt >= this.maxAttempts) return
    const delay = Math.min(1000 * Math.pow(2, this.attempt), 30000)
    this.attempt++
    this.reconnectTimeout = setTimeout(() => this.connect(), delay)
  }

  disconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout)
    this.ws?.close()
    this.ws = null
  }
}
