import requests

def test_login():
    url = "http://127.0.0.1:3000/auth/login"
    payload = {
        "email": "admin@admin.com",
        "password": "15441109" # Contraseña del log del usuario
    }
    
    try:
        print(f"Enviando POST a {url}")
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error de conexión: {e}")

if __name__ == "__main__":
    test_login()

