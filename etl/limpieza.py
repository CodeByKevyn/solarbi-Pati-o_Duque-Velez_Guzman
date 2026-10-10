import os
import pandas as pd

BRONZE_PATH = "data/bronze/telemetria.csv"
SILVER_PATH = "data/silver/telemetria_limpia.csv"

def limpiar_datos():
    # 1. Leer datos crudos de Bronze
    df_bronze = pd.read_csv(BRONZE_PATH)
    filas_leidas = len(df_bronze)

    # 2. Regla 1: Duplicados
    df_sin_duplicados = df_bronze.drop_duplicates()
    rechazados_duplicados = filas_leidas - len(df_sin_duplicados)

    # 3. Regla 2: Datos faltantes (Nulos)
    df_sin_nulos = df_sin_duplicados.dropna(subset=['ts', 'dispositivo_id', 'p_ac_kw', 'irradiancia_wm2'])
    rechazados_nulos = len(df_sin_duplicados) - len(df_sin_nulos)

    # 4. Regla 3: Rango físico válido (p_ac_kw >= 0 e irradiancia_wm2 >= 0)
    df_validos = df_sin_nulos[
        (pd.to_numeric(df_sin_nulos['p_ac_kw'], errors='coerce') >= 0) & 
        (pd.to_numeric(df_sin_nulos['irradiancia_wm2'], errors='coerce') >= 0)
    ].copy()
    rechazados_rango = len(df_sin_nulos) - len(df_validos)

    # 5. Reporte de Métricas de Calidad
    filas_validas = len(df_validos)
    pct_datos_validos = round((filas_validas / filas_leidas) * 100, 2)

    print("==========================================")
    print("     REPORTE DE CALIDAD DE DATOS (SILVER) ")
    print("==========================================")
    print(f"• Filas leídas (Bronze):            {filas_leidas}")
    print(f"• Rechazadas por duplicados:         {rechazados_duplicados}")
    print(f"• Rechazadas por datos faltantes:    {rechazados_nulos}")
    print(f"• Rechazadas por rango inválido:     {rechazados_rango}")
    print(f"• Filas válidas (Silver):            {filas_validas}")
    print(f"• Porcentaje de datos válidos:       {pct_datos_validos}%")
    print("==========================================")

    # 6. Guardar datos limpios en la capa Silver
    os.makedirs("data/silver", exist_ok=True)
    df_validos.to_csv(SILVER_PATH, index=False)
    print(f"¡Éxito! Archivo guardado en {SILVER_PATH}")

if __name__ == "__main__":
    limpiar_datos()