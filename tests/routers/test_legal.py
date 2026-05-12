def test_privacy_policy_page_available(client):
    response = client.get("/legal/privacy-policy")

    assert response.status_code == 200
    assert "Politica de privacidad" in response.text


def test_support_page_available(client):
    response = client.get("/legal/support")

    assert response.status_code == 200
    assert "Soporte de Apitool" in response.text
