def test_login_exitoso(client, auth_headers):
    """Verifica que un usuario válido puede autenticarse."""
    headers = auth_headers("admin@test.com", "Admin123!")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["rol_id"] == 1


def test_login_fallido_contraseña(client):
    """Credenciales inválidas retornan 401."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "incorrecta"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_login_fallido_usuario_inactivo(client, db_session):
    """Un usuario inactivo no puede autenticarse."""
    from app.models import Usuario
    user = db_session.query(Usuario).filter(Usuario.email == "admin@test.com").first()
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "Admin123!"}
    )
    assert response.status_code == 401

    user.is_active = True
    db_session.commit()