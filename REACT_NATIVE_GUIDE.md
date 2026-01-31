# Guía de Implementación Frontend (React Native + Expo)

Esta guía detalla cómo integrar las nuevas funcionalidades del backend (Notificaciones Push y Recomendaciones Estacionales) en tu app móvil.

## 1. Instalación de Dependencias

Necesitas instalar `expo-notifications` y `expo-device` para manejar las notificaciones.

```bash
npx expo install expo-notifications expo-device
```

---

## 2. Configuración de Notificaciones Push

Crea un hook o utilitario para registrar el dispositivo y enviar el token a tu backend.

### Archivo: `src/hooks/usePushNotifications.ts`

```typescript
import { useState, useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import api from '../services/api'; // Tu instancia de axios

// Configuración básica de cómo mostrar la notificación si la app está abierta
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export const usePushNotifications = () => {
  const [expoPushToken, setExpoPushToken] = useState<string | undefined>('');
  const [notification, setNotification] = useState<Notifications.Notification | undefined>(undefined);
  const notificationListener = useRef<Notifications.Subscription>();
  const responseListener = useRef<Notifications.Subscription>();

  async function registerForPushNotificationsAsync() {
    let token;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }

    if (Device.isDevice) {
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }
      if (finalStatus !== 'granted') {
        alert('¡Se necesitan permisos para recibir alertas sobre tus apiarios!');
        return;
      }
      
      // Obtener el token (Project ID se obtiene de app.json si usas EAS)
      token = (await Notifications.getExpoPushTokenAsync({
        projectId: Constants.expoConfig?.extra?.eas?.projectId,
      })).data;
      
      console.log("Expo Push Token:", token);
    } else {
      alert('Debes usar un dispositivo físico para Push Notifications');
    }

    return token;
  }

  useEffect(() => {
    registerForPushNotificationsAsync().then(token => {
      setExpoPushToken(token);
      if (token) {
        // ENVIAR EL TOKEN AL BACKEND
        api.post('/users/push-token', { token: token })
           .catch(err => console.error("Error enviando token al backend:", err));
      }
    });

    // Escuchar notificaciones recibidas
    notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
      setNotification(notification);
    });

    // Escuchar cuando el usuario toca la notificación
    responseListener.current = Notifications.addNotificationResponseReceivedListener(response => {
      console.log(response);
      // Aquí puedes navegar a la pantalla de detalle del apiario
    });

    return () => {
      Notifications.removeNotificationSubscription(notificationListener.current!);
      Notifications.removeNotificationSubscription(responseListener.current!);
    };
  }, []);

  return { expoPushToken, notification };
};
```

**Uso:** Simplemente llama a `usePushNotifications()` en tu `App.tsx` o pantalla principal.

---

## 3. Componente de Recomendaciones Estacionales

Muestra este componente en tu **Home Screen** (Pantalla de Inicio).

### Archivo: `src/components/SeasonalTipCard.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import api from '../services/api';

interface SeasonalTip {
  id: number;
  title: string;
  content: string;
  category: string;
}

interface RecommendationsResponse {
  current_season: string;
  current_month: number;
  tips: SeasonalTip[];
}

export const SeasonalTipCard = () => {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/recommendations')
      .then(response => setData(response.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <ActivityIndicator />;
  if (!data || data.tips.length === 0) return null;

  // Mostramos el primer tip disponible
  const tip = data.tips[0];

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.season}>{data.current_season.toUpperCase()}</Text>
        <Text style={styles.category}>{tip.category}</Text>
      </View>
      <Text style={styles.title}>{tip.title}</Text>
      <Text style={styles.content}>{tip.content}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginVertical: 10,
    elevation: 3, // Sombra en Android
    shadowColor: '#000', // Sombra en iOS
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  season: {
    color: '#d97706', // Color ámbar/miel
    fontWeight: 'bold',
    fontSize: 12,
  },
  category: {
    color: '#6b7280',
    fontSize: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 6,
    color: '#1f2937',
  },
  content: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 20,
  }
});
```

---

## 4. Pantalla de Notificaciones

Si quieres mostrar el historial de alertas ("Campanita").

Necesitas crear el endpoint `GET /notifications` en el backend primero (ya tenemos el servicio `get_user_notifications`, solo falta exponerlo en el router).

### Archivo: `src/screens/NotificationsScreen.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { FlatList, View, Text, StyleSheet } from 'react-native';
import api from '../services/api';
import { format } from 'date-fns'; // O tu librería de fechas favorita

export const NotificationsScreen = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Nota: Asegúrate de crear este endpoint en el backend
    api.get('/notifications') 
       .then(res => setNotifications(res.data))
       .catch(console.error);
  }, []);

  const renderItem = ({ item }) => (
    <View style={[styles.item, !item.isRead && styles.unread]}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.message}>{item.message}</Text>
      <Text style={styles.date}>{format(new Date(item.createdAt), 'dd/MM/yyyy')}</Text>
    </View>
  );

  return (
    <FlatList
      data={notifications}
      renderItem={renderItem}
      keyExtractor={item => item.id.toString()}
      contentContainerStyle={{ padding: 16 }}
    />
  );
};

const styles = StyleSheet.create({
  item: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  unread: {
    backgroundColor: '#eff6ff', // Azul muy claro para no leídas
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  title: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  message: {
    marginTop: 4,
    color: '#4b5563',
  },
  date: {
    marginTop: 8,
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'right',
  }
});
```


