import { ref, onUnmounted } from 'vue'

export interface WsMessage {
  type: string
  data: Record<string, unknown>
}

export function useWebSocket(path = '/ws/live') {
  const connected = ref(false)
  const lastMessage = ref<WsMessage | null>(null)
  const listeners = new Map<string, Set<(data: Record<string, unknown>) => void>>()

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let retryDelay = 1000

  function connect() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}${path}`)

    ws.onopen = () => {
      connected.value = true
      retryDelay = 1000
    }

    ws.onmessage = (ev) => {
      try {
        const msg: WsMessage = JSON.parse(ev.data)
        lastMessage.value = msg
        const handlers = listeners.get(msg.type)
        if (handlers) {
          handlers.forEach((fn) => fn(msg.data))
        }
      } catch { /* ignore non-json */ }
    }

    ws.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      retryDelay = Math.min(retryDelay * 1.5, 10000)
      connect()
    }, retryDelay)
  }

  function on(type: string, fn: (data: Record<string, unknown>) => void) {
    if (!listeners.has(type)) listeners.set(type, new Set())
    listeners.get(type)!.add(fn)
    return () => listeners.get(type)?.delete(fn)
  }

  function close() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
  }

  connect()

  onUnmounted(close)

  return { connected, lastMessage, on, close }
}
