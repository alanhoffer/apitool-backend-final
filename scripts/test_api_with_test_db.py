#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar la API con la base de datos de testing.
Prueba los nuevos endpoints y funcionalidades implementadas.
"""
import sys
import os
import requests
import json
from typing import Optional

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar para usar DB de testing
os.environ["DB_NAME"] = "apitool1_test"

# URL base de la API (ajustar según tu configuración)
BASE_URL = "http://localhost:8000"  # Cambiar si la API está en otro puerto

class Colors:
    """Colores para la salida en consola."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message: str):
    """Imprime mensaje de éxito."""
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {message}")

def print_error(message: str):
    """Imprime mensaje de error."""
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {message}")

def print_info(message: str):
    """Imprime mensaje informativo."""
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {message}")

def print_warning(message: str):
    """Imprime mensaje de advertencia."""
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}")

def test_endpoint(method: str, endpoint: str, headers: Optional[dict] = None, 
                 data: Optional[dict] = None, expected_status: int = 200) -> Optional[dict]:
    """Prueba un endpoint y retorna la respuesta."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            print_error(f"Método HTTP no soportado: {method}")
            return None
        
        if response.status_code == expected_status:
            print_success(f"{method} {endpoint} - Status: {response.status_code}")
            try:
                return response.json()
            except:
                return {"message": response.text}
        else:
            print_error(f"{method} {endpoint} - Status: {response.status_code} (esperado: {expected_status})")
            print_error(f"Respuesta: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error(f"No se pudo conectar a {BASE_URL}")
        print_info("Asegúrate de que la API esté corriendo")
        return None
    except Exception as e:
        print_error(f"Error al probar {endpoint}: {e}")
        return None

def main():
    """Ejecuta las pruebas de la API."""
    print("=" * 70)
    print("PRUEBAS DE API CON BASE DE DATOS DE TESTING")
    print("=" * 70)
    print()
    print_info(f"URL base: {BASE_URL}")
    print_info("Base de datos: apitool1_test")
    print()
    
    # Verificar que la API esté corriendo
    print("1. Verificando que la API esté corriendo...")
    health = test_endpoint("GET", "/health")
    if not health:
        print_error("La API no está disponible. Inicia el servidor primero.")
        print_info("Ejecuta: uvicorn app.main:app --reload")
        return False
    print()
    
    # 1. Registro de usuario
    print("2. Probando registro de usuario...")
    register_data = {
        "name": "Test",
        "surname": "User",
        "email": "test_api@example.com",
        "password": "password123"
    }
    register_response = test_endpoint("POST", "/auth/register", data=register_data, expected_status=200)
    if not register_response:
        print_warning("No se pudo registrar usuario. Puede que ya exista.")
    else:
        test_token = register_response.get("access_token")
        test_user_id = register_response.get("user_id")
        print_success(f"Usuario registrado. ID: {test_user_id}")
    print()
    
    # 2. Login
    print("3. Probando login...")
    login_data = {
        "email": "test_api@example.com",
        "password": "password123"
    }
    login_response = test_endpoint("POST", "/auth/login", data=login_data)
    if login_response:
        test_token = login_response.get("access_token")
        auth_headers = {"Authorization": f"Bearer {test_token}"}
        print_success("Login exitoso")
    else:
        print_error("No se pudo hacer login. Usando token de registro si existe.")
        if 'test_token' not in locals():
            print_error("No hay token disponible. Abortando pruebas.")
            return False
        auth_headers = {"Authorization": f"Bearer {test_token}"}
    print()
    
    # 3. Crear apiary con nuevos campos (latitude, longitude)
    print("4. Probando crear apiary con latitude/longitude...")
    apiary_data = {
        "name": "Apiary Test",
        "hives": 10,
        "status": "normal",
        "latitude": -34.603722,
        "longitude": -58.381592
    }
    create_apiary_response = test_endpoint("POST", "/apiarys", headers=auth_headers, data=apiary_data)
    if create_apiary_response:
        apiary_id = create_apiary_response.get("id")
        print_success(f"Apiary creado. ID: {apiary_id}")
        if create_apiary_response.get("latitude") and create_apiary_response.get("longitude"):
            print_success("Latitude y longitude guardados correctamente")
    print()
    
    # 4. Actualizar settings con tasks
    print("5. Probando actualizar settings con campo tasks...")
    if 'apiary_id' in locals():
        tasks_data = [
            {"id": "1234567890", "text": "Llevar alzas", "completed": False},
            {"id": "1234567891", "text": "Revisar colmenas", "completed": True}
        ]
        settings_data = {
            "apiaryId": apiary_id,
            "apiaryUserId": test_user_id,
            "tasks": json.dumps(tasks_data)
        }
        update_settings_response = test_endpoint("PUT", f"/apiarys/settings/{apiary_id}", 
                                                headers=auth_headers, data=settings_data)
        if update_settings_response:
            print_success("Settings actualizados con tasks")
    print()
    
    # 5. Registrar dispositivo
    print("6. Probando registro de dispositivo...")
    device_data = {
        "deviceName": "iPhone 13 Pro Test",
        "modelName": "iPhone14,2",
        "brand": "Apple",
        "manufacturer": "Apple",
        "platform": "ios",
        "osVersion": "17.0",
        "deviceType": "PHONE",
        "appVersion": "1.0.0",
        "buildVersion": "2",
        "pushToken": "ExponentPushToken[test123]"
    }
    device_response = test_endpoint("POST", "/users/devices", headers=auth_headers, data=device_data, expected_status=201)
    if device_response:
        device_id = device_response.get("id")
        print_success(f"Dispositivo registrado. ID: {device_id}")
    print()
    
    # 6. Obtener dispositivos
    print("7. Probando obtener dispositivos...")
    devices_response = test_endpoint("GET", "/users/devices", headers=auth_headers)
    if devices_response and "devices" in devices_response:
        devices = devices_response["devices"]
        print_success(f"Dispositivos obtenidos: {len(devices)}")
        if devices:
            device = devices[0]
            print_info(f"  - {device.get('deviceName')} ({device.get('platform')})")
    print()
    
    # 7. Forgot password
    print("8. Probando forgot password...")
    forgot_password_response = test_endpoint("POST", "/auth/forgot-password", 
                                           data={"email": "test_api@example.com"})
    if forgot_password_response:
        print_success("Forgot password ejecutado (token generado en logs)")
    print()
    
    # 8. Update profile
    print("9. Probando actualizar perfil...")
    profile_data = {
        "name": "Test Updated"
    }
    update_profile_response = test_endpoint("PUT", "/users/profile", headers=auth_headers, data=profile_data)
    if update_profile_response:
        print_success(f"Perfil actualizado: {update_profile_response.get('name')}")
    print()
    
    # 9. Change password
    print("10. Probando cambiar contraseña...")
    change_password_data = {
        "currentPassword": "password123",
        "newPassword": "newpassword123"
    }
    change_password_response = test_endpoint("PUT", "/users/password", headers=auth_headers, data=change_password_data)
    if change_password_response:
        print_success("Contraseña cambiada exitosamente")
    print()
    
    # 10. Endpoints de estadísticas
    print("11. Probando endpoints de estadísticas...")
    stats_endpoints = [
        "/apiarys/harvested/stats",
        "/apiarys/harvesting/count",
        "/apiarys/harvested/count",
        "/apiarys/harvested/counts",
        "/apiarys/harvested/today/counts",
        "/apiarys/harvested/today/boxes"
    ]
    for endpoint in stats_endpoints:
        test_endpoint("GET", endpoint, headers=auth_headers)
    print()
    
    print("=" * 70)
    print_success("PRUEBAS COMPLETADAS")
    print("=" * 70)
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por el usuario.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

