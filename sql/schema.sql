-- Creación del esquema para la tabla Silver de telemetría solar
CREATE TABLE IF NOT EXISTS telemetria (
    ts TIMESTAMP NOT NULL,
    dispositivo_id INT NOT NULL,
    p_ac_kw NUMERIC(8,3),
    irradiancia_wm2 NUMERIC(8,1),
    temp_modulo_c NUMERIC(5,1),
    CONSTRAINT pk_telemetria PRIMARY KEY (ts, dispositivo_id)
);