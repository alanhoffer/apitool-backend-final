#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar los nuevos endpoints implementados con la DB de testing.
"""
import sys
import os

# Configurar para usar DB de testing
os.environ["DB_NAME"] = "apitool1_test"
os.environ["TESTING"] = "1"

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.apiary_service import ApiaryService
from app.services.settings_service import SettingsService
from app.schemas.user import CreateUser, LoginUser
from app.schemas.apiary import CreateApiary
from app.schemas.settings import UpdateSettings
from app.schemas.device import CreateDevice
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UpdateProfileRequest, ChangePasswordRequest
from passlib.context import CryptContext
from decimal import Decimal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def print_success(msg):
    print(f"[OK] {msg}")

def print_error(msg):
    print(f"[ERROR] {msg}")

def print_info(msg):
    print(f"[INFO] {msg}")

async def test_auth_endpoints(db: Session):
    """Prueba los endpoints de autenticación."""
    print("\n" + "="*60)
    print("PRUEBAS: Endpoints de Autenticación")
    print("="*60)
    
    auth_service = AuthService(db)
    user_service = UserService(db)
    
    # 1. Crear usuario de prueba
    print_info("1. Creando usuario de prueba...")
    test_email = "test_endpoints@example.com"
    test_password = "password123"
    
    # Eliminar usuario si existe
    existing_user = user_service.get_user_by_email(test_email)
    if existing_user:
        user_service.delete_user(existing_user.id)
        print_info("Usuario existente eliminado")
    
    user_data = CreateUser(
        name="Test",
        surname="User",
        email=test_email,
        password=test_password
    )
    user_data.password = pwd_context.hash(user_data.password)
    created_user = user_service.create_user(user_data)
    
    if created_user:
        print_success(f"Usuario creado: {created_user.email} (ID: {created_user.id})")
        test_user_id = created_user.id
    else:
        print_error("No se pudo crear usuario")
        return None
    
    # 2. Login
    print_info("2. Probando login...")
    login_data = LoginUser(email=test_email, password=test_password)
    try:
        auth_result = await auth_service.sign_in(login_data)
        print_success(f"Login exitoso. Token generado.")
        token = auth_result.access_token
    except Exception as e:
        print_error(f"Login falló: {e}")
        return None
    
    # 3. Forgot password
    print_info("3. Probando forgot password...")
    try:
        forgot_result = await auth_service.forgot_password(
            ForgotPasswordRequest(email=test_email)
        )
        print_success(f"Forgot password: {forgot_result.get('message')}")
    except Exception as e:
        print_error(f"Forgot password falló: {e}")
    
    return test_user_id, token

def test_user_endpoints(db: Session, user_id: int, auth_service: AuthService):
    """Prueba los endpoints de usuario."""
    print("\n" + "="*60)
    print("PRUEBAS: Endpoints de Usuario")
    print("="*60)
    
    user_service = UserService(db)
    
    # 1. Update profile
    print_info("1. Probando update profile...")
    try:
        profile_data = UpdateProfileRequest(name="Test Updated")
        updated_user = user_service.update_profile(user_id, profile_data)
        if updated_user and updated_user.name == "Test Updated":
            print_success(f"Perfil actualizado: {updated_user.name}")
        else:
            print_error("Perfil no se actualizó correctamente")
    except Exception as e:
        print_error(f"Update profile falló: {e}")
    
    # 2. Change password
    print_info("2. Probando change password...")
    try:
        password_data = ChangePasswordRequest(
            currentPassword="password123",
            newPassword="newpassword123"
        )
        success = user_service.change_password(user_id, password_data, auth_service)
        if success:
            print_success("Contraseña cambiada exitosamente")
        else:
            print_error("No se pudo cambiar la contraseña")
    except Exception as e:
        print_error(f"Change password falló: {e}")

def test_device_endpoints(db: Session, user_id: int):
    """Prueba los endpoints de dispositivos."""
    print("\n" + "="*60)
    print("PRUEBAS: Endpoints de Dispositivos")
    print("="*60)
    
    user_service = UserService(db)
    
    # 1. Registrar dispositivo
    print_info("1. Probando registro de dispositivo...")
    device_data = CreateDevice(
        deviceName="iPhone 13 Pro Test",
        modelName="iPhone14,2",
        brand="Apple",
        manufacturer="Apple",
        platform="ios",
        osVersion="17.0",
        deviceType="PHONE",
        appVersion="1.0.0",
        buildVersion="2",
        pushToken="ExponentPushToken[test123]"
    )
    
    try:
        device = user_service.register_or_update_device(user_id, device_data)
        if device:
            print_success(f"Dispositivo registrado. ID: {device.id}")
            print_info(f"  - {device.deviceName} ({device.platform})")
            device_id = device.id
        else:
            print_error("No se pudo registrar dispositivo")
            return
    except Exception as e:
        print_error(f"Registro de dispositivo falló: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Obtener dispositivos
    print_info("2. Probando obtener dispositivos...")
    try:
        devices = user_service.get_user_devices(user_id)
        print_success(f"Dispositivos obtenidos: {len(devices)}")
        for dev in devices:
            print_info(f"  - {dev.deviceName} ({dev.platform}) - {dev.modelName}")
    except Exception as e:
        print_error(f"Obtener dispositivos falló: {e}")
    
    # 3. Actualizar dispositivo
    print_info("3. Probando actualizar dispositivo...")
    try:
        update_device_data = CreateDevice(
            deviceName="iPhone 13 Pro Test",
            platform="ios",
            appVersion="1.0.1",
            pushToken="ExponentPushToken[updated123]"
        )
        updated_device = user_service.register_or_update_device(user_id, update_device_data)
        if updated_device and updated_device.appVersion == "1.0.1":
            print_success(f"Dispositivo actualizado. AppVersion: {updated_device.appVersion}")
        else:
            print_error("Dispositivo no se actualizó correctamente")
    except Exception as e:
        print_error(f"Actualizar dispositivo falló: {e}")

async def test_apiary_endpoints(db: Session, user_id: int):
    """Prueba los endpoints de apiarios con nuevos campos."""
    print("\n" + "="*60)
    print("PRUEBAS: Endpoints de Apiarios (nuevos campos)")
    print("="*60)
    
    apiary_service = ApiaryService(db)
    
    # 1. Crear apiary con latitude/longitude
    print_info("1. Probando crear apiary con latitude/longitude...")
    apiary_data = CreateApiary(
        name="Apiary Test Location",
        hives=15,
        status="normal",
        latitude=-34.603722,
        longitude=-58.381592
    )
    
    try:
        apiary = await apiary_service.create_apiary(user_id, apiary_data, None)
        if apiary:
            print_success(f"Apiary creado. ID: {apiary.id}")
            if apiary.latitude and apiary.longitude:
                print_success(f"  - Location: ({apiary.latitude}, {apiary.longitude})")
            else:
                print_error("Latitude/longitude no se guardaron")
            apiary_id = apiary.id
        else:
            print_error("No se pudo crear apiary")
            return
    except Exception as e:
        print_error(f"Crear apiary falló: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Actualizar apiary con location
    print_info("2. Probando actualizar apiary con nueva location...")
    from app.schemas.apiary import UpdateApiary
    try:
        update_data = UpdateApiary(
            latitude=-34.611789,
            longitude=-58.396030
        )
        updated = await apiary_service.update_apiary(apiary_id, update_data, None)
        if updated and updated.latitude == Decimal("-34.611789"):
            print_success(f"Apiary actualizado. Nueva location: ({updated.latitude}, {updated.longitude})")
        else:
            print_error("Location no se actualizó correctamente")
    except Exception as e:
        print_error(f"Actualizar apiary falló: {e}")
    
    # 3. Actualizar settings con tasks
    print_info("3. Probando actualizar settings con campo tasks...")
    settings_service = SettingsService(db)
    try:
        tasks_data = [
            {"id": "1234567890", "text": "Llevar alzas", "completed": False},
            {"id": "1234567891", "text": "Revisar colmenas", "completed": True}
        ]
        settings_data = UpdateSettings(
            apiaryId=apiary_id,
            apiaryUserId=user_id,
            tasks=json.dumps(tasks_data)
        )
        updated_settings = settings_service.update_settings(apiary_id, settings_data)
        if updated_settings and updated_settings.tasks:
            print_success("Settings actualizados con tasks")
            print_info(f"  - Tasks: {updated_settings.tasks[:50]}...")
        else:
            print_error("Tasks no se guardaron")
    except Exception as e:
        print_error(f"Actualizar settings falló: {e}")
        import traceback
        traceback.print_exc()

def test_statistics_endpoints(db: Session, user_id: int):
    """Prueba los endpoints de estadísticas."""
    print("\n" + "="*60)
    print("PRUEBAS: Endpoints de Estadísticas")
    print("="*60)
    
    apiary_service = ApiaryService(db)
    
    endpoints = [
        ("get_box_stats", lambda: apiary_service.get_box_stats(user_id)),
        ("count_harvesting_apiaries", lambda: apiary_service.count_harvesting_apiaries(user_id)),
        ("count_harvested_apiaries", lambda: apiary_service.count_harvested_apiaries(user_id)),
        ("count_hives_in_harvested_apiaries", lambda: apiary_service.count_hives_in_harvested_apiaries(user_id)),
        ("count_harvested_today_apiaries_and_hives", lambda: apiary_service.count_harvested_today_apiaries_and_hives(user_id)),
        ("get_harvested_today_box_stats", lambda: apiary_service.get_harvested_today_box_stats(user_id)),
    ]
    
    for name, func in endpoints:
        try:
            result = func()
            print_success(f"{name}: {result}")
        except Exception as e:
            print_error(f"{name} falló: {e}")

async def main():
    """Ejecuta todas las pruebas."""
    print("="*60)
    print("PRUEBAS DE API CON BASE DE DATOS DE TESTING")
    print("="*60)
    print_info("Base de datos: apitool1_test")
    print()
    
    db = SessionLocal()
    try:
        # Pruebas de autenticación
        result = await test_auth_endpoints(db)
        if not result:
            print_error("No se pudo completar las pruebas de autenticación")
            return False
        
        user_id, token = result
        
        # Pruebas de usuario
        auth_service = AuthService(db)
        test_user_endpoints(db, user_id, auth_service)
        
        # Pruebas de dispositivos
        test_device_endpoints(db, user_id)
        
        # Pruebas de apiarios
        await test_apiary_endpoints(db, user_id)
        
        # Pruebas de estadísticas
        test_statistics_endpoints(db, user_id)
        
        print("\n" + "="*60)
        print_success("TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
        return True
        
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    import asyncio
    import json
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por el usuario.")
        sys.exit(1)

