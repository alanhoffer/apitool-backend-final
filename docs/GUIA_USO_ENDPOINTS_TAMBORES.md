# Guía de Uso - Endpoints de Tambores

Esta guía te ayudará a usar los endpoints de tambores en tu aplicación frontend (React Native/Expo o React Web).

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Autenticación](#autenticación)
3. [Endpoints Disponibles](#endpoints-disponibles)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [Manejo de Errores](#manejo-de-errores)
6. [Casos de Uso Comunes](#casos-de-uso-comunes)

---

## 🔧 Configuración Inicial

### Base URL

```typescript
const API_BASE_URL = 'http://localhost:3000'; // Desarrollo
// o
const API_BASE_URL = 'https://tu-api.com'; // Producción
```

### Configurar Cliente HTTP

#### React Native / Expo (usando axios)

```typescript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token de autenticación
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
```

#### React Web (usando fetch)

```typescript
const getAuthHeaders = async () => {
  const token = localStorage.getItem('authToken');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};
```

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante token JWT.

### Obtener Token

```typescript
// Login
const loginResponse = await api.post('/auth/login', {
  email: 'usuario@example.com',
  password: 'password123'
});

const token = loginResponse.data.access_token;

// Guardar token
await AsyncStorage.setItem('authToken', token); // React Native
// o
localStorage.setItem('authToken', token); // React Web
```

---

## 📡 Endpoints Disponibles

### 1. Crear Tambor
**POST** `/drums`

### 2. Obtener Todos los Tambores
**GET** `/drums?sold=false&page=1&limit=50`

### 3. Obtener Tambor por ID
**GET** `/drums/{id}`

### 4. Actualizar Tambor
**PUT** `/drums/{id}`

### 5. Marcar Tambor como Vendido
**PATCH** `/drums/{id}/sold`

### 6. Eliminar Tambor
**DELETE** `/drums/{id}`

### 7. Eliminar Todos los Tambores
**DELETE** `/drums?sold=false`

### 8. Obtener Estadísticas
**GET** `/drums/stats`

---

## 💻 Ejemplos de Uso

### Servicio de API (TypeScript)

```typescript
// services/drumService.ts

export interface Drum {
  id: number;
  userId: number;
  code: string;
  tare: number;
  weight: number;
  sold: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDrumRequest {
  code: string;
  tare: number;
  weight: number;
}

export interface UpdateDrumRequest {
  code?: string;
  tare?: number;
  weight?: number;
  sold?: boolean;
}

export interface DrumsListResponse {
  data: Drum[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface DrumStats {
  total: number;
  sold: number;
  not_sold: number;
  total_tare: number;
  total_weight: number;
  net_weight: number;
}

// ============================================
// 1. CREAR TAMBOR
// ============================================
export const createDrum = async (data: CreateDrumRequest): Promise<Drum> => {
  const response = await api.post('/drums', data);
  return response.data;
};

// Ejemplo de uso:
const newDrum = await createDrum({
  code: 'TAMBOR-001',
  tare: 15.5,
  weight: 45.2
});

console.log('Tambor creado:', newDrum);

// ============================================
// 2. OBTENER TODOS LOS TAMBORES
// ============================================
export const getDrums = async (params?: {
  sold?: boolean;
  page?: number;
  limit?: number;
}): Promise<DrumsListResponse> => {
  const response = await api.get('/drums', { params });
  return response.data;
};

// Ejemplos de uso:

// Obtener todos los tambores
const allDrums = await getDrums();
console.log('Todos los tambores:', allDrums.data);
console.log('Total:', allDrums.pagination.total);

// Obtener solo tambores no vendidos
const unsoldDrums = await getDrums({ sold: false });

// Obtener solo tambores vendidos
const soldDrums = await getDrums({ sold: true });

// Obtener con paginación
const page1 = await getDrums({ page: 1, limit: 10 });
const page2 = await getDrums({ page: 2, limit: 10 });

// ============================================
// 3. OBTENER TAMBOR POR ID
// ============================================
export const getDrumById = async (id: number): Promise<Drum> => {
  const response = await api.get(`/drums/${id}`);
  return response.data;
};

// Ejemplo de uso:
const drum = await getDrumById(1);
console.log('Tambor:', drum);

// ============================================
// 4. ACTUALIZAR TAMBOR
// ============================================
export const updateDrum = async (
  id: number,
  data: UpdateDrumRequest
): Promise<Drum> => {
  const response = await api.put(`/drums/${id}`, data);
  return response.data;
};

// Ejemplos de uso:

// Actualizar todos los campos
const updatedDrum = await updateDrum(1, {
  code: 'TAMBOR-001-UPDATED',
  tare: 16.0,
  weight: 46.5
});

// Actualizar solo algunos campos (parcial)
const partiallyUpdated = await updateDrum(1, {
  weight: 50.0
  // code y tare no se modifican
});

// ============================================
// 5. MARCAR TAMBOR COMO VENDIDO
// ============================================
export const markDrumAsSold = async (
  id: number,
  sold: boolean
): Promise<Drum> => {
  const response = await api.patch(`/drums/${id}/sold`, { sold });
  return response.data;
};

// Ejemplos de uso:

// Marcar como vendido
const soldDrum = await markDrumAsSold(1, true);

// Marcar como no vendido
const unsoldDrum = await markDrumAsSold(1, false);

// ============================================
// 6. ELIMINAR TAMBOR
// ============================================
export const deleteDrum = async (id: number): Promise<void> => {
  await api.delete(`/drums/${id}`);
};

// Ejemplo de uso:
await deleteDrum(1);
console.log('Tambor eliminado');

// ============================================
// 7. ELIMINAR TODOS LOS TAMBORES
// ============================================
export const deleteAllDrums = async (sold?: boolean): Promise<{ deleted_count: number }> => {
  const params = sold !== undefined ? { sold } : {};
  const response = await api.delete('/drums', { params });
  return response.data;
};

// Ejemplos de uso:

// Eliminar todos los tambores
const result1 = await deleteAllDrums();
console.log(`Se eliminaron ${result1.deleted_count} tambores`);

// Eliminar solo tambores vendidos
const result2 = await deleteAllDrums(true);
console.log(`Se eliminaron ${result2.deleted_count} tambores vendidos`);

// Eliminar solo tambores no vendidos
const result3 = await deleteAllDrums(false);
console.log(`Se eliminaron ${result3.deleted_count} tambores no vendidos`);

// ============================================
// 8. OBTENER ESTADÍSTICAS
// ============================================
export const getDrumsStats = async (): Promise<DrumStats> => {
  const response = await api.get('/drums/stats');
  return response.data;
};

// Ejemplo de uso:
const stats = await getDrumsStats();
console.log('Estadísticas:', {
  total: stats.total,
  vendidos: stats.sold,
  noVendidos: stats.not_sold,
  pesoNeto: stats.net_weight
});
```

---

## 🎨 Ejemplos de Componentes React

### Componente: Lista de Tambores

```typescript
// components/DrumList.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { getDrums, deleteDrum, markDrumAsSold } from '../services/drumService';
import { Drum } from '../services/drumService';

export const DrumList: React.FC = () => {
  const [drums, setDrums] = useState<Drum[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'sold' | 'unsold'>('all');

  useEffect(() => {
    loadDrums();
  }, [filter]);

  const loadDrums = async () => {
    try {
      setLoading(true);
      const params = filter === 'all' 
        ? undefined 
        : { sold: filter === 'sold' };
      
      const response = await getDrums(params);
      setDrums(response.data);
    } catch (error) {
      console.error('Error cargando tambores:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDrum(id);
      await loadDrums(); // Recargar lista
    } catch (error) {
      console.error('Error eliminando tambor:', error);
    }
  };

  const handleToggleSold = async (drum: Drum) => {
    try {
      await markDrumAsSold(drum.id, !drum.sold);
      await loadDrums(); // Recargar lista
    } catch (error) {
      console.error('Error actualizando tambor:', error);
    }
  };

  const calculateNetWeight = (drum: Drum) => {
    return drum.weight - drum.tare;
  };

  return (
    <View style={styles.container}>
      {/* Filtros */}
      <View style={styles.filters}>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'all' && styles.filterActive]}
          onPress={() => setFilter('all')}
        >
          <Text>Todos</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'unsold' && styles.filterActive]}
          onPress={() => setFilter('unsold')}
        >
          <Text>No Vendidos</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'sold' && styles.filterActive]}
          onPress={() => setFilter('sold')}
        >
          <Text>Vendidos</Text>
        </TouchableOpacity>
      </View>

      {/* Lista */}
      <FlatList
        data={drums}
        keyExtractor={(item) => item.id.toString()}
        refreshing={loading}
        onRefresh={loadDrums}
        renderItem={({ item }) => (
          <View style={styles.drumCard}>
            <View style={styles.drumHeader}>
              <Text style={styles.drumCode}>{item.code}</Text>
              <TouchableOpacity
                style={[styles.soldBadge, item.sold && styles.soldBadgeActive]}
                onPress={() => handleToggleSold(item)}
              >
                <Text style={styles.soldText}>
                  {item.sold ? 'Vendido' : 'No Vendido'}
                </Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.drumDetails}>
              <Text>Tara: {item.tare} kg</Text>
              <Text>Peso Total: {item.weight} kg</Text>
              <Text style={styles.netWeight}>
                Peso Neto: {calculateNetWeight(item)} kg
              </Text>
            </View>

            <View style={styles.drumActions}>
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={() => handleDelete(item.id)}
              >
                <Text style={styles.deleteButtonText}>Eliminar</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  filters: { flexDirection: 'row', marginBottom: 16, gap: 8 },
  filterButton: { padding: 8, borderRadius: 8, backgroundColor: '#e0e0e0' },
  filterActive: { backgroundColor: '#4CAF50' },
  drumCard: { 
    backgroundColor: '#fff', 
    padding: 16, 
    marginBottom: 12, 
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3
  },
  drumHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  drumCode: { fontSize: 18, fontWeight: 'bold' },
  soldBadge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, backgroundColor: '#e0e0e0' },
  soldBadgeActive: { backgroundColor: '#4CAF50' },
  soldText: { color: '#fff', fontSize: 12 },
  drumDetails: { marginBottom: 12 },
  netWeight: { fontWeight: 'bold', marginTop: 4 },
  drumActions: { flexDirection: 'row', justifyContent: 'flex-end' },
  deleteButton: { paddingHorizontal: 16, paddingVertical: 8, backgroundColor: '#f44336', borderRadius: 8 },
  deleteButtonText: { color: '#fff' }
});
```

### Componente: Formulario de Crear/Editar Tambor

```typescript
// components/DrumForm.tsx
import React, { useState } from 'react';
import { View, TextInput, Button, StyleSheet, Alert } from 'react-native';
import { createDrum, updateDrum, Drum } from '../services/drumService';

interface DrumFormProps {
  drum?: Drum; // Si existe, es edición
  onSuccess: () => void;
  onCancel: () => void;
}

export const DrumForm: React.FC<DrumFormProps> = ({ drum, onSuccess, onCancel }) => {
  const [code, setCode] = useState(drum?.code || '');
  const [tare, setTare] = useState(drum?.tare.toString() || '');
  const [weight, setWeight] = useState(drum?.weight.toString() || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    // Validaciones
    if (!code.trim()) {
      Alert.alert('Error', 'El código es requerido');
      return;
    }
    
    if (!tare || parseFloat(tare) <= 0) {
      Alert.alert('Error', 'La tara debe ser mayor a 0');
      return;
    }
    
    if (!weight || parseFloat(weight) <= 0) {
      Alert.alert('Error', 'El peso debe ser mayor a 0');
      return;
    }

    try {
      setLoading(true);
      
      if (drum) {
        // Actualizar
        await updateDrum(drum.id, {
          code: code.trim(),
          tare: parseFloat(tare),
          weight: parseFloat(weight)
        });
        Alert.alert('Éxito', 'Tambor actualizado correctamente');
      } else {
        // Crear
        await createDrum({
          code: code.trim(),
          tare: parseFloat(tare),
          weight: parseFloat(weight)
        });
        Alert.alert('Éxito', 'Tambor creado correctamente');
      }
      
      onSuccess();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Error al guardar tambor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Código del tambor"
        value={code}
        onChangeText={setCode}
        editable={!loading}
      />
      
      <TextInput
        style={styles.input}
        placeholder="Tara (kg)"
        value={tare}
        onChangeText={setTare}
        keyboardType="decimal-pad"
        editable={!loading}
      />
      
      <TextInput
        style={styles.input}
        placeholder="Peso Total (kg)"
        value={weight}
        onChangeText={setWeight}
        keyboardType="decimal-pad"
        editable={!loading}
      />

      <View style={styles.actions}>
        <Button
          title={drum ? 'Actualizar' : 'Crear'}
          onPress={handleSubmit}
          disabled={loading}
        />
        <Button
          title="Cancelar"
          onPress={onCancel}
          color="#999"
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { padding: 16 },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    fontSize: 16
  },
  actions: { marginTop: 16, gap: 8 }
});
```

### Componente: Estadísticas de Tambores

```typescript
// components/DrumStats.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { getDrumsStats, DrumStats } from '../services/drumService';

export const DrumStatsComponent: React.FC = () => {
  const [stats, setStats] = useState<DrumStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await getDrumsStats();
      setStats(data);
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Estadísticas de Tambores</Text>
      
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats.total}</Text>
          <Text style={styles.statLabel}>Total</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats.sold}</Text>
          <Text style={styles.statLabel}>Vendidos</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{stats.not_sold}</Text>
          <Text style={styles.statLabel}>No Vendidos</Text>
        </View>
      </View>

      <View style={styles.weightSection}>
        <View style={styles.weightRow}>
          <Text style={styles.weightLabel}>Tara Total:</Text>
          <Text style={styles.weightValue}>{stats.total_tare} kg</Text>
        </View>
        
        <View style={styles.weightRow}>
          <Text style={styles.weightLabel}>Peso Total:</Text>
          <Text style={styles.weightValue}>{stats.total_weight} kg</Text>
        </View>
        
        <View style={[styles.weightRow, styles.netWeightRow]}>
          <Text style={styles.netWeightLabel}>Peso Neto:</Text>
          <Text style={styles.netWeightValue}>{stats.net_weight} kg</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#f5f5f5' },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 16 },
  statsGrid: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 24 },
  statCard: { alignItems: 'center', backgroundColor: '#fff', padding: 16, borderRadius: 8, minWidth: 80 },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#4CAF50' },
  statLabel: { fontSize: 12, color: '#666', marginTop: 4 },
  weightSection: { backgroundColor: '#fff', padding: 16, borderRadius: 8 },
  weightRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  netWeightRow: { marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#e0e0e0' },
  weightLabel: { fontSize: 16 },
  weightValue: { fontSize: 16, fontWeight: '600' },
  netWeightLabel: { fontSize: 18, fontWeight: 'bold' },
  netWeightValue: { fontSize: 18, fontWeight: 'bold', color: '#4CAF50' }
});
```

---

## ⚠️ Manejo de Errores

### Códigos de Estado HTTP

- **200 OK**: Operación exitosa
- **201 Created**: Recurso creado exitosamente
- **400 Bad Request**: Datos inválidos
- **401 Unauthorized**: Token inválido o expirado
- **403 Forbidden**: No autorizado
- **404 Not Found**: Recurso no encontrado
- **422 Unprocessable Entity**: Error de validación

### Ejemplo de Manejo de Errores

```typescript
import { AxiosError } from 'axios';

const handleApiError = (error: AxiosError) => {
  if (error.response) {
    // El servidor respondió con un código de error
    const status = error.response.status;
    const message = error.response.data?.detail || 'Error desconocido';
    
    switch (status) {
      case 401:
        // Token expirado, redirigir a login
        console.log('Sesión expirada, redirigiendo a login...');
        // navigation.navigate('Login');
        break;
      case 403:
        Alert.alert('Error', 'No tienes permisos para realizar esta acción');
        break;
      case 404:
        Alert.alert('Error', 'Tambor no encontrado');
        break;
      case 422:
        Alert.alert('Error de Validación', message);
        break;
      default:
        Alert.alert('Error', `Error ${status}: ${message}`);
    }
  } else if (error.request) {
    // La petición se hizo pero no hubo respuesta
    Alert.alert('Error', 'No se pudo conectar con el servidor');
  } else {
    // Algo más causó el error
    Alert.alert('Error', error.message);
  }
};

// Uso:
try {
  await createDrum(data);
} catch (error) {
  handleApiError(error as AxiosError);
}
```

---

## 📱 Casos de Uso Comunes

### 1. Escanear Código de Barras y Crear Tambor

```typescript
import { BarCodeScanner } from 'expo-barcode-scanner';
import { createDrum } from '../services/drumService';

const handleBarCodeScanned = async ({ data }: { data: string }) => {
  try {
    // El usuario ingresa manualmente tara y peso
    const tare = await promptForTare(); // Función que muestra input
    const weight = await promptForWeight();
    
    const drum = await createDrum({
      code: data, // Código escaneado
      tare: parseFloat(tare),
      weight: parseFloat(weight)
    });
    
    Alert.alert('Éxito', `Tambor ${drum.code} creado correctamente`);
  } catch (error) {
    Alert.alert('Error', 'No se pudo crear el tambor');
  }
};
```

### 2. Lista con Búsqueda y Filtros

```typescript
const [searchQuery, setSearchQuery] = useState('');
const [filterSold, setFilterSold] = useState<boolean | undefined>(undefined);

const filteredDrums = drums.filter(drum => {
  const matchesSearch = drum.code.toLowerCase().includes(searchQuery.toLowerCase());
  const matchesFilter = filterSold === undefined || drum.sold === filterSold;
  return matchesSearch && matchesFilter;
});
```

### 3. Exportar Datos a CSV

```typescript
const exportToCSV = (drums: Drum[]) => {
  const headers = 'Código,Tara (kg),Peso Total (kg),Peso Neto (kg),Vendido,Fecha\n';
  const rows = drums.map(drum => {
    const netWeight = drum.weight - drum.tare;
    return `${drum.code},${drum.tare},${drum.weight},${netWeight},${drum.sold ? 'Sí' : 'No'},${drum.createdAt}\n`;
  }).join('');
  
  const csv = headers + rows;
  
  // En React Native, usar expo-file-system o react-native-fs
  // En React Web, descargar directamente
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'tambores.csv';
  a.click();
};
```

### 4. Sincronización Offline

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

const SYNC_QUEUE_KEY = 'drum_sync_queue';

// Guardar tambor localmente cuando no hay conexión
const createDrumOffline = async (drumData: CreateDrumRequest) => {
  const queue = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
  const queueArray = queue ? JSON.parse(queue) : [];
  
  queueArray.push({
    action: 'create',
    data: drumData,
    timestamp: new Date().toISOString()
  });
  
  await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queueArray));
};

// Sincronizar cuando hay conexión
const syncOfflineDrums = async () => {
  const queue = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
  if (!queue) return;
  
  const queueArray = JSON.parse(queue);
  
  for (const item of queueArray) {
    try {
      if (item.action === 'create') {
        await createDrum(item.data);
      }
      // Eliminar del queue después de sincronizar
    } catch (error) {
      console.error('Error sincronizando:', error);
      // Mantener en el queue para reintentar después
    }
  }
  
  // Limpiar queue después de sincronizar exitosamente
  await AsyncStorage.removeItem(SYNC_QUEUE_KEY);
};
```

---

## 🔄 Flujo Completo de Uso

### Flujo: Escanear y Registrar Tambor

```typescript
// 1. Escanear código de barras
const scannedCode = 'TAMBOR-001';

// 2. Mostrar formulario para ingresar tara y peso
const tare = 15.5; // Usuario ingresa
const weight = 45.2; // Usuario ingresa

// 3. Crear tambor
const drum = await createDrum({
  code: scannedCode,
  tare,
  weight
});

// 4. Mostrar confirmación
Alert.alert('Éxito', `Tambor ${drum.code} registrado`);

// 5. Actualizar lista
await loadDrums();
```

### Flujo: Vender Tambor

```typescript
// 1. Seleccionar tambor de la lista
const selectedDrum = drums[0];

// 2. Marcar como vendido
await markDrumAsSold(selectedDrum.id, true);

// 3. Actualizar lista (filtrar vendidos)
const unsoldDrums = await getDrums({ sold: false });

// 4. Actualizar estadísticas
const stats = await getDrumsStats();
console.log('Peso neto total:', stats.net_weight);
```

---

## 📊 Ejemplos de Respuestas

### Crear Tambor (POST /drums)

**Request:**
```json
{
  "code": "TAMBOR-001",
  "tare": 15.5,
  "weight": 45.2
}
```

**Response (201):**
```json
{
  "id": 1,
  "userId": 2,
  "code": "TAMBOR-001",
  "tare": 15.5,
  "weight": 45.2,
  "sold": false,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Listar Tambores (GET /drums)

**Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "userId": 2,
      "code": "TAMBOR-001",
      "tare": 15.5,
      "weight": 45.2,
      "sold": false,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1,
    "totalPages": 1
  }
}
```

### Estadísticas (GET /drums/stats)

**Response (200):**
```json
{
  "total": 10,
  "sold": 3,
  "not_sold": 7,
  "total_tare": 165.5,
  "total_weight": 485.2,
  "net_weight": 319.7
}
```

---

## ✅ Checklist de Implementación

- [ ] Configurar cliente HTTP con interceptores de autenticación
- [ ] Crear servicio de API para tambores
- [ ] Implementar componente de lista de tambores
- [ ] Implementar formulario de crear/editar tambor
- [ ] Implementar componente de estadísticas
- [ ] Agregar manejo de errores
- [ ] Implementar filtros (vendido/no vendido)
- [ ] Agregar paginación
- [ ] Implementar búsqueda por código
- [ ] Agregar funcionalidad de exportar datos
- [ ] Implementar sincronización offline (opcional)

---

## 🚀 Próximos Pasos

1. **Integrar con escáner de códigos de barras**: Usa `expo-barcode-scanner` o similar
2. **Agregar validaciones**: Verificar que el código no esté duplicado
3. **Implementar caché**: Guardar tambores localmente para acceso rápido
4. **Agregar notificaciones**: Avisar cuando se crea/actualiza un tambor
5. **Implementar búsqueda avanzada**: Filtrar por rango de fechas, peso, etc.

---

¡Listo para usar! 🎉




























