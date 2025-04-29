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
    const token = localStorage.getItem('authToken') || "2a0900171d53dd190ced3bae7b5054006b1d2363";

    this.socket = new WebSocket(`${this.wsUrl}?token=${token}`);

    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.onConnect();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing message:', error);
        this.onError('Invalid message format');
      }
    };

    this.socket.onclose = (event) => {
      if (event.wasClean) {
        console.log(`Connection closed cleanly, code=${event.code}, reason=${event.reason}`);
      } else {
        console.warn('Connection died');
        this.reconnect();
      }
      this.onDisconnect(event);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.onError('WebSocket error');
    };
  }

  // Базовые обработчики событий (можно переопределять)
  onConnect() {
    console.log('Connected to notifications server');
  }

  onDisconnect(event) {
    console.log('Disconnected from server', event);
  }

  onError(error) {
    console.error('Notification error:', error);
  }

  handleMessage(data) {
    switch(data.type) {
      case 'notification':
        console.log('New notification:', data.data);
        this.onNotification(data.data);
        break;
      case 'error':
        console.error('Server error:', data.data.message);
        this.onError(data.data.message);
        break;
      case 'read_confirmation':
        console.log('Notification marked as read:', data.data.notification_id);
        this.onReadConfirmation(data.data.notification_id);
        break;
      default:
        console.warn('Unknown message type:', data.type);
    }
  }

  // Методы для работы с уведомлениями
  markAsRead(notificationId) {
    if (this.isConnected()) {
      this.socket.send(JSON.stringify({
        type: 'mark_as_read',
        notification_id: notificationId
      }));
      return true;
    }
    return false;
  }

  markAllAsRead() {
    if (this.isConnected()) {
      this.socket.send(JSON.stringify({
        type: 'mark_all_read'
      }));
      return true;
    }
    return false;
  }

  markAsHidden(notificationId) {
    if (this.isConnected()) {
      this.socket.send(JSON.stringify({
        type: 'mark_as_hidden',
        notification_id: notificationId
      }));
      return true;
    }
    return false;
  }

  markAllAsHidden() {
    if (this.isConnected()) {
      this.socket.send(JSON.stringify({
        type: 'mark_all_hidden'
      }));
      return true;
    }
    return false;
  }

  // Вспомогательные методы
  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
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

  // Обработчики, которые можно переопределить при наследовании
  onNotification(notification) {
    // Пример: показываем уведомление в UI
    alert(`New notification: ${notification.message}`);
  }

  onReadConfirmation(notificationId) {
    // Пример: обновляем UI
    console.log(`Notification ${notificationId} was marked as read on server`);
  }
}

// Создаем глобальный объект для доступа из консоли
const notificationSocket = new NotificationWebSocket();

// Добавляем удобные алиасы для тестирования из консоли
window.ns = {
  markRead: (id) => notificationSocket.markAsRead(id),
  markAllRead: () => notificationSocket.markAllAsRead(),
  markHidden: (id) => notificationSocket.markAsHidden(id),
  markAllHidden: () => notificationSocket.markAllAsHidden(),
  close: () => notificationSocket.close(),
  status: () => notificationSocket.isConnected() ? 'connected' : 'disconnected'
};

console.log('Доступные команды для работы с WebSocket:');
console.log('ns.markRead(id) - пометить уведомление как прочитанное');
console.log('ns.markAllRead() - пометить все уведомления как прочитанные');
console.log('ns.markHidden(id) - скрыть уведомление');
console.log('ns.markAllHidden() - скрыть все уведомления');
console.log('ns.close() - закрыть соединение');
console.log('ns.status() - проверить статус соединения');
// notificationSocket.close();