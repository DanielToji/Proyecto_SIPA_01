from app.core.database import engine
from sqlalchemy import text

conn = engine.connect()

print("=" * 60)
print("PASO 1: BD y schema actuales")
print("=" * 60)
result = conn.execute(text("SELECT current_database(), current_schema()"))
print(result.fetchone())

print()
print("=" * 60)
print("PASO 2: Columnas de etapa_productiva.fichas")
print("=" * 60)
result = conn.execute(text("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'etapa_productiva'
      AND table_name = 'fichas'
    ORDER BY ordinal_position
"""))
for row in result:
    print(f"  {row[0]:<30} {row[1]}")

print()
print("=" * 60)
print("PASO 3: Todos los schemas que tienen tabla 'fichas'")
print("=" * 60)
result = conn.execute(text("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_name = 'fichas'
"""))
for row in result:
    print(f"  schema={row[0]:<30} tabla={row[1]}")

print()
print("=" * 60)
print("PASO 4: Prueba SELECT nivel FROM etapa_productiva.fichas")
print("=" * 60)
try:
    result = conn.execute(text("SELECT nivel FROM etapa_productiva.fichas LIMIT 1"))
    print("  OK FUNCIONA:", result.fetchall())
except Exception as e:
    print("  FALLA:", str(e))

conn.close()
