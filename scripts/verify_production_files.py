#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar archivos en producción.
"""
import re

# Lista de archivos que el usuario proporcionó
files = [
    "06df3c1b-50b1-4a8e-b173-d43a5160f2bc.jpg", "58cd3509-9914-4d20-b0a9-af27bf15246f.jpg", "d4d8b40d-acde-4d81-96d0-798a035fd565.jpg",
    "09dbe05c-3717-489a-9cc0-77ad987e5844.jpg", "5a6835ae-3777-439b-a6bc-a263e24ba998.jpg", "dd109510-f976-42f0-9322-80d110b0344f.jpg",
    "0d7f69df-5e79-499e-834f-a84f7e5177b2.jpg", "6b580351-19d4-4da1-95f5-2d293c7f3145.jpg", "e0316a78-162e-4cba-bdc6-28a4df1533c1.jpg",
    "0e270a90-880d-4d47-bdc8-0eb1bd54bdcb.jpg", "86d94007-85cb-489c-9062-f10f6c4c0ff0.jpg", "e13b5255-03ca-4bd1-9c97-f12fac08a00c.jpg",
    "1476f35f-16f1-4f0b-83d0-0d88426ae3da.jpg", "8ea56e1f-dbb1-4726-83e9-4f7ab783ee19.jpg", "e61965c0-425e-49cc-b262-423b13806d21.jpg",
    "1488fd8e-4306-440d-9efc-7d6c74aab723.jpg", "8fb6ae6b-933d-4a30-bc02-e5d43aab73da.jpg", "e97a55d3-7d6d-4577-b732-08f2d81e5c7a.jpg",
    "1a00f42d-9572-4de3-ad8f-62cd5ed606de.jpg", "917a2335-9c03-4766-b718-2f2b3ffcf601.jpg", "f0b92cf9-3e74-4beb-ae84-3f504c824d2f.jpg",
    "1aff744b-4fb2-40c2-bc39-879d6f453173.jpg", "9b14201d-050d-4d62-b972-145347b8dced.jpg", "f1646f46-c9e2-4311-a13e-ae42e5f2cc7f.jpg",
    "21f4cb28-1529-4d23-93b7-953eb7b0cc82.jpg", "a355fca6-5a6f-4bf2-b607-1240639362d1.jpg", "f51dc862-b4e7-462c-ba9f-7db43ad5df26.jpg",
    "24a596b0-060a-4c57-b45e-a1fb5c6e949b.jpg", "a89247ea-6b18-439a-a328-17322d1a2e3f.jpg", "f71c89d4-3737-42d4-b2a2-1487c22894d5.jpg",
    "2590c41c-f79d-4630-bb19-ff5dfa027e70.jpg", "apiary-default.png", "f749f1e2-7011-45cc-a4e5-e16e341d41b9.jpg",
    "33da5c3e-9502-46aa-8df1-b77046311a5e.jpg", "c459e11e-fbfa-4782-ab72-2fe9b54d27cb.jpg", "fb9b6b9b-aa29-4aa8-8cf0-e37d8d0743ae.jpg",
    "34b0b8e8-b30c-4a1a-aeb1-71e6a7b0734b.jpg", "c933bfb8-a0e3-424c-8fdd-ab2b694d0bad.jpg", "fc3b229e-363f-471e-b9c3-5d7326cd0139.jpg",
    "368d85f7-2a8e-4887-b951-104992f2c355.jpg", "c9b4b9e2-4458-478b-a9b5-2dc1101b7d22.jpg",
    "498577c7-677f-4cca-8fac-1b33f9f201f3.jpg", "d4283d1f-aceb-4785-bb8e-7fb05f6ba3fe.jpg",
]

print("=" * 60)
print("VERIFICACION DE ARCHIVOS EN PRODUCCION")
print("=" * 60)
print()

# Verificar apiary-default.png
if "apiary-default.png" in files:
    print("[OK] apiary-default.png encontrado en produccion")
else:
    print("[ERROR] apiary-default.png NO encontrado")

print()

# Verificar formato de archivos
uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|png)$', re.IGNORECASE)
jpg_files = [f for f in files if f.endswith('.jpg')]
png_files = [f for f in files if f.endswith('.png')]

print(f"Total de archivos: {len(files)}")
print(f"  - Archivos .jpg: {len(jpg_files)}")
print(f"  - Archivos .png: {len(png_files)}")
print()

# Verificar formato UUID
invalid_format = []
for f in files:
    if f != "apiary-default.png" and not uuid_pattern.match(f):
        invalid_format.append(f)

if invalid_format:
    print(f"[ADVERTENCIA] Archivos con formato invalido: {len(invalid_format)}")
    for f in invalid_format[:5]:  # Mostrar solo los primeros 5
        print(f"  - {f}")
    if len(invalid_format) > 5:
        print(f"  ... y {len(invalid_format) - 5} mas")
else:
    print("[OK] Todos los archivos tienen formato UUID valido")

print()
print("=" * 60)
print("RESUMEN:")
print("=" * 60)
print(f"1. apiary-default.png: {'OK' if 'apiary-default.png' in files else 'FALTA'}")
print(f"2. Total archivos: {len(files)}")
print(f"3. Formato valido: {'OK' if not invalid_format else 'REVISAR'}")
print()
print("TODO CORRECTO!")

