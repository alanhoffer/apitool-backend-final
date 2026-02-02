# Análisis de Mejoras para la API

## 🔒 SEGURIDAD

### 1. **JWT_SECRET hardcodeado**
**Problema:** `app/constants.py` tiene `JWT_SECRET = "123123"` hardcodeado
**Riesgo:** CRÍTICO - Cualquiera puede generar tokens válidos
**Solución:**
- Mover a variables de entorno
- Generar secret aleatorio y seguro
- Rotar secret periódicamente

### 2. **CORS demasiado permisivo**
**Problema:** `allow_origins=["*"]` permite cualquier origen
**Riesgo:** MEDIO - Vulnerable a CSRF
**Solución:**
- Especificar orígenes permitidos en configuración
- Usar variables de entorno para producción/desarrollo

### 3. **Credenciales de BD en código**
**Problema:** `app/config.py` tiene credenciales hardcodeadas
**Riesgo:** ALTO - Exposición de credenciales
**Solución:**
- Mover todas las credenciales a `.env`
- Agregar `.env` a `.gitignore` (verificar que esté)

### 4. **Falta rate limiting**
**Problema:** No hay límites de requests por usuario/IP
**Riesgo:** MEDIO - Vulnerable a ataques DDoS/brute force
**Solución:**
- Implementar rate limiting con `slowapi` o `fastapi-limiter`
- Limitar especialmente endpoints de auth

### 5. **Validación de permisos inconsistente**
**Problema:** Algunos endpoints verifican ownership, otros no
**Riesgo:** MEDIO - Posible acceso no autorizado
**Solución:**
- Crear decorador `@require_ownership` para reutilizar
- Centralizar lógica de verificación

---

## 🛡️ MANEJO DE ERRORES Y TRANSACCIONES

### 6. **Falta manejo de transacciones**
**Problema:** No hay rollback en caso de errores
**Riesgo:** ALTO - Datos inconsistentes
**Ejemplo:** `apiary_service.py` línea 220: si falla después de `commit()`, no hay rollback
**Solución:**
```python
try:
    self.db.commit()
except Exception:
    self.db.rollback()
    raise
```

### 7. **Excepciones genéricas**
**Problema:** Muchos `except Exception` sin especificar
**Riesgo:** MEDIO - Dificulta debugging
**Solución:**
- Especificar excepciones concretas
- Logging apropiado de errores

### 8. **Falta validación de tipos en form data**
**Problema:** `int(form.get("hives"))` puede fallar si viene string inválido
**Riesgo:** MEDIO - Errores 500 inesperados
**Solución:**
- Validar y convertir con try/except
- Usar Pydantic para validación automática

### 9. **Manejo de errores de BD inconsistente**
**Problema:** Algunos servicios retornan `None`, otros lanzan excepciones
**Riesgo:** MEDIO - Comportamiento impredecible
**Solución:**
- Estandarizar: siempre lanzar excepciones HTTP apropiadas
- Crear excepciones custom si es necesario

---

## ✅ VALIDACIONES

### 10. **Validación de entrada débil**
**Problema:** Validaciones básicas en schemas, pero no en todos los campos
**Ejemplo:** `hives` puede ser negativo, `name` puede estar vacío
**Solución:**
- Agregar validadores Pydantic (`Field(gt=0)`, `Field(min_length=1)`)
- Validar rangos de valores

### 11. **Falta validación de archivos**
**Problema:** Solo valida tipo MIME, no tamaño máximo
**Riesgo:** MEDIO - Posible DoS con archivos grandes
**Solución:**
- Limitar tamaño máximo (ej: 10MB)
- Validar antes de procesar

### 12. **Validación de email**
**Problema:** No se valida formato de email en registro
**Riesgo:** BAJO - Datos inválidos en BD
**Solución:**
- Usar `EmailStr` de Pydantic
- Validar formato antes de guardar

---

## 🔄 CÓDIGO DUPLICADO

### 13. **Verificación de ownership repetida**
**Problema:** Mismo código en múltiples endpoints:
```python
if apiary.userId != user_id:
    raise HTTPException(...)
```
**Solución:**
- Crear dependency `verify_apiary_ownership`
- Reutilizar en todos los endpoints

### 14. **Construcción manual de ApiaryDetail**
**Problema:** Se repite en `create_apiary` y `update_apiary`
**Solución:**
- Crear método helper `_to_apiary_detail(apiary)`
- O usar `from_attributes=True` en schema

### 15. **Parsing de form data repetido**
**Problema:** Mismo código para convertir form a `UpdateApiary`
**Solución:**
- Crear función helper `parse_form_to_update_apiary(form)`

---

## ⚡ PERFORMANCE

### 16. **N+1 queries potenciales**
**Problema:** Algunos queries no usan `joinedload` cuando deberían
**Solución:**
- Revisar todos los queries que acceden relaciones
- Usar `joinedload` o `selectinload` apropiadamente

### 17. **Falta paginación en algunos endpoints**
**Problema:** `get_apiarys` puede retornar muchos registros
**Solución:**
- Agregar paginación con `page` y `limit`
- Retornar metadata (total, page, limit)

### 18. **Queries sin índices**
**Problema:** Algunos campos usados en `filter()` pueden no tener índices
**Solución:**
- Revisar queries frecuentes
- Agregar índices en BD si es necesario

### 19. **Falta caché**
**Problema:** Datos que no cambian frecuentemente se consultan cada vez
**Ejemplo:** Weather API, recomendaciones
**Solución:**
- Implementar caché con Redis o in-memory
- TTL apropiado según tipo de dato

---

## 📁 ESTRUCTURA Y ORGANIZACIÓN

### 20. **Endpoints duplicados/similares**
**Problema:** 
- `/stats/boxes` y `/harvested/stats` hacen lo mismo
- Varios endpoints de "harvested" con lógica similar
**Solución:**
- Consolidar o documentar diferencias claramente
- Considerar query params en lugar de múltiples endpoints

### 21. **Falta versionado de API**
**Problema:** No hay `/v1/` en rutas
**Riesgo:** Difícil hacer breaking changes
**Solución:**
- Agregar versionado: `/api/v1/apiarys`
- Planificar migración

### 22. **Mensajes de error inconsistentes**
**Problema:** Algunos dicen "not exists", otros "not found"
**Solución:**
- Estandarizar mensajes de error
- Crear constantes para mensajes comunes

### 23. **Falta logging estructurado**
**Problema:** Logging básico, no estructurado
**Solución:**
- Usar logging estructurado (JSON)
- Incluir request_id, user_id, etc.

---

## 📚 DOCUMENTACIÓN

### 24. **Falta documentación OpenAPI completa**
**Problema:** Algunos endpoints no tienen descripciones
**Solución:**
- Agregar `description` a todos los endpoints
- Documentar parámetros y respuestas
- Agregar ejemplos

### 25. **Falta documentación de errores**
**Problema:** No se documentan códigos de error posibles
**Solución:**
- Agregar `responses` con códigos de error
- Documentar qué significa cada error

---

## 🧪 TESTING

### 26. **Cobertura de tests limitada**
**Problema:** Solo hay algunos tests básicos
**Solución:**
- Agregar tests para casos edge
- Tests de integración para flujos completos
- Tests de seguridad (auth, permissions)

### 27. **Falta fixtures para tests**
**Problema:** Tests pueden ser difíciles de mantener
**Solución:**
- Crear fixtures reutilizables en `conftest.py`
- Factories para crear datos de prueba

---

## 🔧 CONFIGURACIÓN Y DEPLOY

### 28. **Timezone no configurado**
**Problema:** `func.current_date()` puede usar timezone del servidor
**Riesgo:** Datos inconsistentes según ubicación
**Solución:**
- Configurar timezone explícito
- Usar UTC consistentemente

### 29. **Falta health check endpoint**
**Problema:** No hay forma de verificar que la API está funcionando
**Solución:**
- Agregar `/health` endpoint
- Verificar conexión a BD

### 30. **Falta métricas/monitoring**
**Problema:** No hay métricas de performance
**Solución:**
- Agregar Prometheus metrics
- Logging de requests lentos

---

## 🎯 PRIORIDADES

### 🔴 CRÍTICO (Hacer inmediatamente)
1. JWT_SECRET a variables de entorno
2. Credenciales de BD a .env
3. Manejo de transacciones con rollback

### 🟠 ALTO (Próximas semanas)
4. Rate limiting
5. Validaciones de entrada más estrictas
6. Estandarizar manejo de errores
7. Eliminar código duplicado (ownership checks)

### 🟡 MEDIO (Próximos meses)
8. Paginación
9. Caché para datos estáticos
10. Documentación OpenAPI completa
11. Tests más completos

### 🟢 BAJO (Mejoras continuas)
12. Versionado de API
13. Métricas y monitoring
14. Optimización de queries

---

## 📝 NOTAS ADICIONALES

- El código está bien estructurado en general (routers, services, models)
- La separación de responsabilidades es buena
- Algunos endpoints tienen lógica que podría estar en servicios
- Considerar usar dependency injection más extensivamente
- Revisar si todos los campos de modelos son necesarios (algunos pueden ser NULL pero no deberían)


