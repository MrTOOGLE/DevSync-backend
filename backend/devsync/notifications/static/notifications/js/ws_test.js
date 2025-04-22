class NotificationWebSocket {
  constructor() {
    this.wsUrl = 'ws://localhost/ws/notifications/';
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;

    this.connect();
  }

  connect() {
    const token = "2a0900171d53dd190ced3bae7b5054006b1d2363";

    this.socket = new WebSocket(`${this.wsUrl}?token=${token}`);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received notification:', data);

      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    this.socket.onclose = (event) => {
      if (event.wasClean) {
        console.log(`Connection closed cleanly, code=${event.code}, reason=${event.reason}`);
      } else {
        console.warn('Connection died');
        this.reconnect();
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting attempt ${this.reconnectAttempts}...`);

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  close() {
    if (this.socket) {
      this.socket.close();
    }
  }

  markAsRead(notificationId) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'mark_as_read',
        notification_id: notificationId
      }));
    }
  }
}

const notificationSocket = new NotificationWebSocket();

// notificationSocket.close();