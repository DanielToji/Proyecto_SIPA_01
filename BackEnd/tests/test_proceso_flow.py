from datetime import date, timedelta

from fastapi import status

from app.models import ProgramaFormacion, ModalidadEP, Ficha


def _crear_catalogos(db_session):
    """Crea programa, modalidad y ficha necesarios para un proceso."""
    programa = ProgramaFormacion(
        codigo="TEST01",
        nombre="Programa Test",
        is_active=True
    )
    db_session.add(programa)
    db_session.commit()

    modalidad = ModalidadEP(
        nombre="Contrato de Aprendizaje",
        descripcion="Test",
        is_active=True
    )
    db_session.add(modalidad)
    db_session.commit()

    ficha = Ficha(
        programa_id=programa.id,
        numero_ficha="1234567",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=180),
        is_active=True
    )
    db_session.add(ficha)
    db_session.commit()
    return programa, modalidad, ficha


def test_flujo_completo_proceso(client, auth_headers, db_session, seed_usuarios):
    """Crea proceso, sube bitácora y evalúa bitácora."""
    programa, modalidad, ficha = _crear_catalogos(db_session)

    # Obtener IDs de aprendiz e instructor
    from app.models import Usuario
    aprendiz = db_session.query(Usuario).filter(Usuario.email == "aprendiz@test.com").first()
    instructor = db_session.query(Usuario).filter(Usuario.email == "instructor@test.com").first()

    admin_headers = auth_headers("admin@test.com", "Admin123!")
    instructor_headers = auth_headers("instructor@test.com", "Instructor123!")
    aprendiz_headers = auth_headers("aprendiz@test.com", "Aprendiz123!")

    # 1. Admin crea proceso
    response = client.post(
        "/procesos",
        headers=admin_headers,
        json={
            "aprendiz_id": aprendiz.id,
            "ficha_id": ficha.id,
            "modalidad_id": modalidad.id,
            "instructor_id": instructor.id,
            "fecha_inicio": str(date.today()),
            "fecha_fin": str(date.today() + timedelta(days=180)),
        }
    )
    assert response.status_code == status.HTTP_201_CREATED, f"Creación proceso: {response.text}"
    proceso_id = response.json()["id"]

    # 2. Aprendiz sube bitácora
    response = client.post(
        "/bitacoras",
        headers=aprendiz_headers,
        json={
            "proceso_id": proceso_id,
            "numero_bitacora": 1,
            "periodo_reportado": "2024-08",
            "titulo": "Primera bitácora",
            "contenido": "Contenido de prueba suficiente longitud",
        }
    )
    assert response.status_code == status.HTTP_201_CREATED, f"Creación bitácora: {response.text}"
    bitacora_id = response.json()["id"]

    # 3. Instructor evalúa bitácora
    response = client.patch(
        f"/bitacoras/{bitacora_id}/evaluar",
        headers=instructor_headers,
        json={
            "estado": "APROBADA",
            "retroalimentacion": "Bien"
        }
    )
    assert response.status_code == status.HTTP_200_OK, f"Evaluación bitácora: {response.text}"
    assert response.json()["estado"] == "APROBADA"