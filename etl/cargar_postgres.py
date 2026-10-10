import pandas as pd
from sqlalchemy import create_engine, text

# Archivo limpio Silver
SILVER_PATH = "data/silver/telemetria_limpia.csv"

# CONFIGURACIÓN DE POSTGRESQL (Ajusta la clave 'postgres' si le pusiste otra a tu PostgreSQL)
DB_USER = "postgres"
DB_PASS = "casa4512"  # <-- PON AQUÍ TU CONTRASEÑA DE POSTGRESQL
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "solarbi"

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def cargar_datos_idempotente():
    engine = create_engine(DATABASE_URL)
    
    # 1. Crear tabla si no existe
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS telemetria (
                ts TIMESTAMP NOT NULL,
                dispositivo_id INT NOT NULL,
                p_ac_kw NUMERIC(8,3),
                irradiancia_wm2 NUMERIC(8,1),
                temp_modulo_c NUMERIC(5,1),
                CONSTRAINT pk_telemetria PRIMARY KEY (ts, dispositivo_id)
            );
        """))
        conn.commit()

    # 2. Leer datos de Silver
    df = pd.read_csv(SILVER_PATH)

    # 3. Carga Idempotente (ON CONFLICT DO UPDATE)
    query = text("""
        INSERT INTO telemetria (ts, dispositivo_id, p_ac_kw, irradiancia_wm2, temp_modulo_c)
        VALUES (:ts, :dispositivo_id, :p_ac_kw, :irradiancia_wm2, :temp_modulo_c)
        ON CONFLICT (ts, dispositivo_id) 
        DO UPDATE SET 
            p_ac_kw = EXCLUDED.p_ac_kw,
            irradiancia_wm2 = EXCLUDED.irradiancia_wm2,
            temp_modulo_c = EXCLUDED.temp_modulo_c;
    """)

    registros = df.to_dict(orient="records")
    
    with engine.connect() as conn:
        conn.execute(query, registros)
        conn.commit()
        
        # Verificar conteo final
        res = conn.execute(text("SELECT COUNT(*) FROM telemetria;")).scalar()

    print("==========================================")
    print("     CARGA EN POSTGRESQL (IDEMPOTENTE)    ")
    print("==========================================")
    print(f"• Registros procesados desde Silver: {len(df)}")
    print(f"• Total de filas en base de datos:  {res}")
    print("==========================================")
    print("¡Carga exitosa demostrando idempotencia!")

if __name__ == "__main__":
    cargar_datos_idempotente()