import pandas as pd
from sqlalchemy import create_engine, text

# 1. RUTAS DE ARCHIVOS
SILVER_PATH = "data/silver/telemetria_limpia.csv"

# 2. CONFIGURACIÓN DE BASE DE DATOS
DB_USER = "postgres"
DB_PASS = "casa4512"  # <-- IMPORTANTE: Cambia por tu contraseña si usas otra (ej. admin123)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "solarbi"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def ejecutar_pipeline_completo():
    engine = create_engine(DATABASE_URL)

    # -------------------------------------------------------------
    # PASO A: CREAR ESQUEMAS Y TABLAS EXIGIDAS
    # -------------------------------------------------------------
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dwh;"))

        # Tabla Silver (lecturas de 5 minutos)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver.lectura_5min (
                ts TIMESTAMP NOT NULL,
                dispositivo_id INT NOT NULL,
                p_ac_kw NUMERIC(8,3),
                irradiancia_wm2 NUMERIC(8,1),
                temp_modulo_c NUMERIC(5,1),
                CONSTRAINT pk_lectura_5min PRIMARY KEY (ts, dispositivo_id)
            );
        """))

        # Tabla Gold / DWH (resumen diario de energía)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dwh.fact_energia_dia (
                fecha DATE NOT NULL,
                dispositivo_id INT NOT NULL,
                energia_kwh NUMERIC(10,3),
                pct_datos_validos NUMERIC(5,2),
                CONSTRAINT pk_fact_energia_dia PRIMARY KEY (fecha, dispositivo_id)
            );
        """))
        conn.commit()

    # -------------------------------------------------------------
    # PASO B: CARGAR CAPA SILVER (silver.lectura_5min)
    # -------------------------------------------------------------
    df_silver = pd.read_csv(SILVER_PATH)

    query_silver = text("""
        INSERT INTO silver.lectura_5min (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
        VALUES (:ts, :dispositivo_id, :p_ac_kw, :irradiancia_wm2, :temp_modulo_c)
        ON CONFLICT (ts, dispositivo_id)
        DO UPDATE SET
            p_ac_kw = EXCLUDED.p_ac_kw,
            irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
            temp_modulo_c = EXCLUDED.temp_modulo_c;
    """)

    registros_silver = df_silver.to_dict(orient="records")

    with engine.connect() as conn:
        conn.execute(query_silver, registros_silver)
        conn.commit()

    # -------------------------------------------------------------
    # PASO C: CALCULAR Y CARGAR CAPA GOLD (dwh.fact_energia_dia)
    # -------------------------------------------------------------
    df_gold_source = df_silver.copy()
    df_gold_source['ts'] = pd.to_datetime(df_gold_source['ts'])
    df_gold_source['fecha'] = df_gold_source['ts'].dt.date

    # Cálculo de energía por intervalo de 5 min: Potencia (kW) * (5 / 60) horas = kWh
    df_gold_source['energia_intervalo_kwh'] = df_gold_source['p_ac_kw'] * (5.0 / 60.0)

    # Agrupación diaria por dispositivo
    df_gold = df_gold_source.groupby(['fecha', 'dispositivo_id']).agg(
        energia_kwh=('energia_intervalo_kwh', 'sum'),
        cant_registros=('ts', 'count')
    ).reset_index()

    # Porcentaje de datos válidos (1 día = 24h * 12 intervalos = 288 mediciones esperadas)
    df_gold['pct_datos_validos'] = ((df_gold['cant_registros'] / 288.0) * 100.0).round(2)
    df_gold['energia_kwh'] = df_gold['energia_kwh'].round(3)

    query_gold = text("""
        INSERT INTO dwh.fact_energia_dia (fecha, dispositivo_id, energia_kwh, pct_datos_validos)
        VALUES (:fecha, :dispositivo_id, :energia_kwh, :pct_datos_validos)
        ON CONFLICT (fecha, dispositivo_id)
        DO UPDATE SET
            energia_kwh = EXCLUDED.energia_kwh,
            pct_datos_validos = EXCLUDED.pct_datos_validos;
    """)

    registros_gold = df_gold[['fecha', 'dispositivo_id', 'energia_kwh', 'pct_datos_validos']].to_dict(orient="records")

    with engine.connect() as conn:
        conn.execute(query_gold, registros_gold)
        conn.commit()

        # Conteo final en las tablas
        total_silver = conn.execute(text("SELECT COUNT(*) FROM silver.lectura_5min;")).scalar()
        total_gold = conn.execute(text("SELECT COUNT(*) FROM dwh.fact_energia_dia;")).scalar()

    # -------------------------------------------------------------
    # PASO D: REPORTE DE EJECUCIÓN
    # -------------------------------------------------------------
    print("==================================================")
    print("        EJECUCIÓN DEL PIPELINE ETL (SOLARBI)      ")
    print("==================================================")
    print(f"• Tabla 'silver.lectura_5min'   -> {total_silver} filas")
    print(f"• Tabla 'dwh.fact_energia_dia'  -> {total_gold} filas")
    print("==================================================")
    print("¡Proceso completado con éxito e idempotencia!")

if __name__ == "__main__":
    ejecutar_pipeline_completo()