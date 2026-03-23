/**
 * PropOS — WebSocket Client
 * Real-time connection to the backend for live dashboard updates.
 */

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

type MessageHandler = (data: any) => void;

export class WSClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnects = 10;
  private reconnectDelay = 2000;

  connect(): void {
    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        console.log('[PropOS] WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const handlers = this.handlers.get(msg.type) || [];
          handlers.forEach(h => h(msg.data));
        } catch (e) {
          console.error('[PropOS] WS parse error', e);
        }
      };

      this.ws.onclose = () => {
        console.log('[PropOS] WebSocket closed');
        this.tryReconnect();
      };

      this.ws.onerror = (err) => {
        console.error('[PropOS] WebSocket error', err);
      };
    } catch (e) {
      console.error('[PropOS] WS connect error', e);
      this.tryReconnect();
    }
  }

  on(type: string, handler: MessageHandler): void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, []);
    }
    this.handlers.get(type)!.push(handler);
  }

  off(type: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(type) || [];
    this.handlers.set(type, handlers.filter(h => h !== handler));
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private tryReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnects) {
      console.error('[PropOS] Max reconnection attempts reached');
      return;
    }
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.min(this.reconnectAttempts, 5);
    console.log(`[PropOS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => this.connect(), delay);
  }
}

// Singleton
let _client: WSClient | null = null;
export function getWSClient(): WSClient {
  if (!_client) _client = new WSClient();
  return _client;
}
