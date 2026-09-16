#  SIPA - Backend API

**Sistema de Vigilancia y Seguimiento de Etapa Productiva** para el SENA.

---

##  Tabla de Contenidos

- [Requisitos Previos](#-requisitos-previos)
- [Advertencia Importante](#️-advertencia-importante)
- [Instalación](#-instalación)
  - [1. Clonar el repositorio](#1-clonar-el-repositorio)
  - [2. Crear y activar entorno virtual](#2-crear-y-activar-entorno-virtual)
  - [3. Instalar dependencias](#3-instalar-dependencias)
  - [4. Configurar variables de entorno](#4-configurar-variables-de-entorno)
  - [5. Crear la base de datos](#5-crear-la-base-de-datos)
  - [6. Ejecutar el script SQL](#6-ejecutar-el-script-sql)
  - [7. Iniciar el servidor](#7-iniciar-el-servidor)

---

## Requisitos Previos

| Requisito | Versión | Descarga |
|-----------|---------|----------|
| **Python** | 3.12 o superior | [python.org](https://www.python.org/downloads/) |
| **PostgreSQL** | 14 o superior | [postgresql.org](https://www.postgresql.org/download/) |
| **Git** | Cualquier versión | [git-scm.com](https://git-scm.com/downloads) |

---

##  ADVERTENCIA IMPORTANTE

> El archivo `script_completo.sql` **ELIMINA y recrea** el esquema `etapa_productiva`.

- **Úsalo solo en desarrollo y pruebas**
-  **NO lo ejecutes en producción** (borrará todos los datos)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/hecto294/Backend_sipa_by_moxigua.git
cd Backend_sipa_by_moxigua
```

### 2. Crear y activar entorno virtual

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar el ejemplo
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:

**Windows**

```bash
notepad .env
```

**Linux/Mac**

```bash
nano .env
```

### 5. Crear la base de datos

Conéctate a PostgreSQL:

```bash
psql -U postgres
```

Ejecuta estos comandos dentro de `psql`:

```sql
CREATE DATABASE sipa_db;
\c sipa_db;
CREATE SCHEMA etapa_productiva;
\q
```

### 6. Ejecutar el script SQL

**Windows**

```bash
psql -U postgres -d sipa_db -f script_completo.sql
```

**Linux/Mac**

```bash
sudo -u postgres psql -d sipa_db -f script_completo.sql
```

### 7. Iniciar el servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor quedará disponible en [http://localhost:8000](http://localhost:8000).

---

##  Licencia

Este proyecto es de uso interno para el SENA. Ajusta esta sección según la licencia que corresponda.