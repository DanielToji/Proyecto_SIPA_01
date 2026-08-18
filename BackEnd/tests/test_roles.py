from fastapi import status


def test_acceso_admin_puede_crear_usuario(client, auth_headers, seed_roles):
    """Admin puede crear usuarios."""
    headers = auth_headers("admin@test.com", "Admin123!")
    response = client.post(
        "/usuarios",
        headers=headers,
        json={
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "email": "nuevo@test.com",
            "password": "Nuevo123!",
            "rol_id": 4,
        }
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_instructor_no_puede_crear_usuario(client, auth_headers, seed_roles):
    """Instructor no tiene permiso para crear usuarios."""
    headers = auth_headers("instructor@test.com", "Instructor123!")
    response = client.post(
        "/usuarios",
        headers=headers,
        json={
            "nombre": "Otro",
            "apellido": "Usuario",
            "email": "otro@test.com",
            "password": "Otro123!",
            "rol_id": 4,
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_aprendiz_no_puede_listar_usuarios(client, auth_headers):
    """Aprendiz no puede listar usuarios."""
    headers = auth_headers("aprendiz@test.com", "Aprendiz123!")
    response = client.get("/usuarios", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN