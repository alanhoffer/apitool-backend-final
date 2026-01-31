# Guía de Implementación de Notificaciones en React (Web)

Esta guía te muestra cómo integrar el sistema de notificaciones del backend en tu aplicación React.

## 📋 Tabla de Contenidos

1. [Instalación de Dependencias](#1-instalación-de-dependencias)
2. [Configuración de la API](#2-configuración-de-la-api)
3. [Hook para Notificaciones](#3-hook-para-notificaciones)
4. [Componente de Notificaciones](#4-componente-de-notificaciones)
5. [Integración en la App](#5-integración-en-la-app)
6. [Opcional: Web Push Notifications](#6-opcional-web-push-notifications)

---

## 1. Instalación de Dependencias

```bash
npm install axios
# O si usas yarn
yarn add axios
```

---

## 2. Configuración de la API

Crea un archivo para configurar tu cliente HTTP con autenticación.

### Archivo: `src/services/api.ts`

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el token en cada petición
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 3. Hook para Notificaciones

Crea un hook personalizado para manejar las notificaciones.

### Archivo: `src/hooks/useNotifications.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'INFO' | 'ALERT' | 'WARNING';
  isRead: boolean;
  createdAt: string;
}

export const useNotifications = (unreadOnly: boolean = false) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/notifications', {
        params: { unread_only: unreadOnly },
      });
      setNotifications(response.data);
      
      // Calcular notificaciones no leídas
      const unread = response.data.filter((n: Notification) => !n.isRead).length;
      setUnreadCount(unread);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar notificaciones');
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  }, [unreadOnly]);

  const markAsRead = useCallback(async (notificationId: number) => {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      
      // Actualizar el estado local
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === notificationId ? { ...n, isRead: true } : n
        )
      );
      
      // Actualizar contador
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err: any) {
      console.error('Error marking notification as read:', err);
      throw err;
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      // Marcar todas como leídas una por una
      const unreadNotifications = notifications.filter((n) => !n.isRead);
      await Promise.all(
        unreadNotifications.map((n) => api.put(`/notifications/${n.id}/read`))
      );
      
      // Actualizar estado
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, isRead: true }))
      );
      setUnreadCount(0);
    } catch (err: any) {
      console.error('Error marking all as read:', err);
      throw err;
    }
  }, [notifications]);

  useEffect(() => {
    fetchNotifications();
    
    // Refrescar notificaciones cada 30 segundos
    const interval = setInterval(fetchNotifications, 30000);
    
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  return {
    notifications,
    loading,
    error,
    unreadCount,
    refresh: fetchNotifications,
    markAsRead,
    markAllAsRead,
  };
};
```

---

## 4. Componente de Notificaciones

Crea componentes para mostrar las notificaciones.

### Archivo: `src/components/NotificationBell.tsx`

```typescript
import React, { useState, useRef, useEffect } from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { NotificationDropdown } from './NotificationDropdown';
import './NotificationBell.css';

export const NotificationBell: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { unreadCount } = useNotifications(true);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="notification-bell-container" ref={dropdownRef}>
      <button
        className="notification-bell-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Notificaciones"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount}</span>
        )}
      </button>
      {isOpen && <NotificationDropdown onClose={() => setIsOpen(false)} />}
    </div>
  );
};
```

### Archivo: `src/components/NotificationBell.css`

```css
.notification-bell-container {
  position: relative;
}

.notification-bell-button {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  color: #333;
  transition: color 0.2s;
}

.notification-bell-button:hover {
  color: #007bff;
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #dc3545;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}
```

### Archivo: `src/components/NotificationDropdown.tsx`

```typescript
import React from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { NotificationItem } from './NotificationItem';
import './NotificationDropdown.css';

interface NotificationDropdownProps {
  onClose: () => void;
}

export const NotificationDropdown: React.FC<NotificationDropdownProps> = ({
  onClose,
}) => {
  const {
    notifications,
    loading,
    error,
    markAsRead,
    markAllAsRead,
  } = useNotifications(false);

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead();
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  return (
    <div className="notification-dropdown">
      <div className="notification-dropdown-header">
        <h3>Notificaciones</h3>
        {notifications.some((n) => !n.isRead) && (
          <button
            className="mark-all-read-button"
            onClick={handleMarkAllAsRead}
          >
            Marcar todas como leídas
          </button>
        )}
      </div>

      <div className="notification-dropdown-content">
        {loading && (
          <div className="notification-loading">Cargando...</div>
        )}

        {error && (
          <div className="notification-error">{error}</div>
        )}

        {!loading && !error && notifications.length === 0 && (
          <div className="notification-empty">
            No tienes notificaciones
          </div>
        )}

        {!loading &&
          !error &&
          notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkAsRead={markAsRead}
            />
          ))}
      </div>

      <div className="notification-dropdown-footer">
        <button onClick={onClose}>Cerrar</button>
      </div>
    </div>
  );
};
```

### Archivo: `src/components/NotificationDropdown.css`

```css
.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 400px;
  max-height: 500px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.notification-dropdown-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-dropdown-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.mark-all-read-button {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
}

.mark-all-read-button:hover {
  text-decoration: underline;
}

.notification-dropdown-content {
  overflow-y: auto;
  flex: 1;
}

.notification-loading,
.notification-error,
.notification-empty {
  padding: 24px;
  text-align: center;
  color: #6b7280;
}

.notification-error {
  color: #dc3545;
}

.notification-dropdown-footer {
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  text-align: center;
}

.notification-dropdown-footer button {
  background: #f3f4f6;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  color: #374151;
}

.notification-dropdown-footer button:hover {
  background: #e5e7eb;
}
```

### Archivo: `src/components/NotificationItem.tsx`

```typescript
import React from 'react';
import { Notification } from '../hooks/useNotifications';
import './NotificationItem.css';

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: number) => void;
}

export const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
}) => {
  const getTypeIcon = () => {
    switch (notification.type) {
      case 'ALERT':
        return '⚠️';
      case 'WARNING':
        return '⚠️';
      case 'INFO':
      default:
        return 'ℹ️';
    }
  };

  const getTypeColor = () => {
    switch (notification.type) {
      case 'ALERT':
        return '#dc3545';
      case 'WARNING':
        return '#ffc107';
      case 'INFO':
      default:
        return '#007bff';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Ahora';
    if (minutes < 60) return `Hace ${minutes} min`;
    if (hours < 24) return `Hace ${hours} h`;
    if (days < 7) return `Hace ${days} días`;
    return date.toLocaleDateString('es-ES');
  };

  const handleClick = () => {
    if (!notification.isRead) {
      onMarkAsRead(notification.id);
    }
  };

  return (
    <div
      className={`notification-item ${!notification.isRead ? 'unread' : ''}`}
      onClick={handleClick}
      style={{
        borderLeftColor: getTypeColor(),
      }}
    >
      <div className="notification-icon">{getTypeIcon()}</div>
      <div className="notification-content">
        <div className="notification-title">{notification.title}</div>
        <div className="notification-message">{notification.message}</div>
        <div className="notification-date">{formatDate(notification.createdAt)}</div>
      </div>
      {!notification.isRead && (
        <div className="notification-dot" style={{ backgroundColor: getTypeColor() }} />
      )}
    </div>
  );
};
```

### Archivo: `src/components/NotificationItem.css`

```css
.notification-item {
  display: flex;
  padding: 12px 16px;
  border-left: 3px solid;
  cursor: pointer;
  transition: background-color 0.2s;
  gap: 12px;
}

.notification-item:hover {
  background-color: #f9fafb;
}

.notification-item.unread {
  background-color: #eff6ff;
}

.notification-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
  margin-bottom: 4px;
}

.notification-date {
  font-size: 11px;
  color: #9ca3af;
}

.notification-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}
```

---

## 5. Integración en la App

### Archivo: `src/App.tsx` (ejemplo)

```typescript
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { NotificationBell } from './components/NotificationBell';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>Mi App de Apicultura</h1>
          <NotificationBell />
        </header>
        
        <Routes>
          {/* Tus rutas aquí */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
```

---

## 6. Opcional: Web Push Notifications

Si quieres recibir notificaciones del navegador incluso cuando la app está cerrada, puedes implementar Web Push Notifications.

### Instalación

```bash
npm install web-push
```

### Nota Importante

El backend actual usa **Expo Push Notifications** que es para aplicaciones móviles. Para Web Push Notifications necesitarías:

1. **Modificar el backend** para soportar Web Push (VAPID keys)
2. **Registrar un Service Worker** en el frontend
3. **Solicitar permisos** del navegador

Si necesitas esta funcionalidad, puedo ayudarte a implementarla. Por ahora, el sistema actual funciona perfectamente para mostrar notificaciones dentro de la aplicación.

---

## 📝 Resumen de Endpoints

- `GET /notifications?unread_only=false` - Obtener notificaciones
- `PUT /notifications/{id}/read` - Marcar como leída
- `POST /users/push-token` - Registrar token (para móviles)

---

## 🎨 Personalización

Puedes personalizar los estilos CSS según tu diseño. Los componentes están diseñados para ser flexibles y fáciles de modificar.

---

## ✅ Checklist de Implementación

- [ ] Instalar dependencias
- [ ] Configurar API client
- [ ] Crear hook `useNotifications`
- [ ] Crear componente `NotificationBell`
- [ ] Crear componente `NotificationDropdown`
- [ ] Crear componente `NotificationItem`
- [ ] Integrar en el header/navbar
- [ ] Probar con el backend
- [ ] Personalizar estilos

---

¡Listo! Ahora tienes un sistema completo de notificaciones en tu app React. 🎉

