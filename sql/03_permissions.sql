\getenv app_user APP_DB_USER
\getenv app_password APP_DB_PASSWORD
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE :"DBNAME" TO :"app_user";
GRANT USAGE ON SCHEMA public TO :"app_user";
GRANT SELECT ON assets,sensors,sensor_thresholds,telemetry,alarms TO :"app_user";
GRANT INSERT ON telemetry,alarms TO :"app_user";
GRANT UPDATE ON alarms TO :"app_user";
-- SELECT FOR UPDATE de um sensor requer UPDATE em ao menos uma coluna.
GRANT UPDATE (enabled) ON sensors TO :"app_user";
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO :"app_user";
