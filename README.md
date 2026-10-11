# SolarBI - Power BI y Grafana para el monitoreo de la planta solar

Inteligencia de Negocios - Grupo 01 - 2026-II
Institución Universitaria Pascual Bravo - Docente: Ramiro Grisales Montoya

## Integrantes

- Kevyn Alejandro Patiño Duque (@CodeByKevyn)
- Samuel Vélez Guzmán (@SamuelVelez-G)

## De qué trata

Con datos simulados de un inversor solar de 5 kWp armamos un flujo pequeño: datos crudos (Bronze), limpieza con reglas de calidad (Silver), carga en PostgreSQL y resumen diario (Gold). Sobre esa misma base hay dos tableros: uno en Power BI (energía y calidad de los datos) y otro en Grafana (potencia en el tiempo y fallas).

> One governed dataset, two views: Grafana for real-time operations and Power BI for business decisions.

## Estructura

```
data/bronze/   telemetria.csv (datos crudos, no se modifican)
data/silver/   telemetria_limpia.csv
etl/           simulador.py, limpieza.py, cargar_postgres.py, run_etl.py
sql/           schema.sql
powerbi/       solarbi_dashboard.pbix
docs/          PDF de la consulta y capturas
```

`cargar_postgres.py` y `schema.sql` son la primera versión de la carga (tabla `public.telemetria`). El flujo que vale es `run_etl.py`.

## Reglas de calidad (Silver)

1. Duplicados: se descartan las filas repetidas.
2. Datos faltantes: se descartan las filas sin ts, dispositivo, potencia o irradiancia.
3. Rango físico: potencia e irradiancia no pueden ser negativas.

Con los datos de ejemplo: 877 filas leídas, 13 duplicadas, 16 con faltantes y 21 fuera de rango, quedan 827 válidas (94,3 %). El porcentaje es filas válidas sobre filas leídas.

## Cómo reproducir

Se necesita Python 3 y PostgreSQL.

1. Instalar las librerías: `pip install pandas sqlalchemy psycopg2-binary`
2. Crear la base de datos en PostgreSQL: `CREATE DATABASE solarbi;`
3. Poner el usuario y la contraseña de PostgreSQL en `DB_USER` y `DB_PASS`, al inicio de `etl/run_etl.py`. Solo en la copia local, ese cambio no se sube.
4. (Opcional) `python etl/simulador.py` vuelve a generar Bronze. Como no tiene semilla los números cambian; los datos de ejemplo ya vienen en `data/`.
5. `python etl/limpieza.py` aplica las reglas y deja `data/silver/telemetria_limpia.csv`.
6. `python etl/run_etl.py` crea los esquemas `silver` y `dwh`, carga las lecturas de 5 minutos en `silver.lectura_5min` y calcula `dwh.fact_energia_dia`.

Si se ejecuta `run_etl.py` dos veces los conteos no cambian: 827 filas en Silver y 3 en Gold.

## Idempotencia

Las dos tablas se cargan con `INSERT ... ON CONFLICT DO UPDATE`. La clave de `silver.lectura_5min` es (ts, dispositivo_id) y la de `dwh.fact_energia_dia` es (fecha, dispositivo_id). Si la fila ya existe se actualiza, si no se inserta.

## Ejecución diaria a la medianoche

Solo está escrita, no implementada. Con cron:

```
0 0 * * * cd /ruta/al/repo && python etl/limpieza.py && python etl/run_etl.py
```

En el Programador de tareas de Windows sería una tarea diaria a las 00:00 que ejecute esos mismos dos comandos. `run_etl.py` lee el CSV que deja `limpieza.py`, por eso van juntos.

## Power BI

`powerbi/solarbi_dashboard.pbix` está conectado a las tablas de PostgreSQL (`silver.lectura_5min` y `dwh.fact_energia_dia`). Al actualizar los datos, Power BI pide la conexión a tu propio PostgreSQL.

## Grafana

Se instaló Grafana OSS 13.2.3 en Windows con el instalador .msi y la interfaz abre en `localhost:3000`, pero no se pudo agregar PostgreSQL como data source: Windows bloqueó el componente de PostgreSQL de Grafana (`gpx_grafana_postgresql_datasource_windows_amd64.exe`) porque no pudo confirmar quién lo publicó. En el equipo está activado Smart App Control y se decidió no desactivarlo. Las capturas del error están en `docs/capturas/` y se explican en el PDF (ruta alterna del taller: documentar el error y explorar play.grafana.org).

## Quién hizo qué

| Parte | Responsable |
|-------|-------------|
| Simulador, limpieza (Silver) y carga en PostgreSQL (Gold) | Kevyn |
| Tablero de Power BI | Kevyn |
| Tablero de Grafana | Samuel |
| README y organización del repositorio | Samuel |
| Consulta (Parte A) y PDF | Los dos |
