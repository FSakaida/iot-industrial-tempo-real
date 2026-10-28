-- Último valor, plano real, histórico, agregação, contagem e alarmes.
SELECT a.id,a.production_line,s.id,s.unit,s.sample_seconds FROM assets a JOIN sensors s ON s.asset_id=a.id;
SELECT * FROM timescaledb_information.hypertables;
SHOW timescaledb.license;
SELECT sensor_id,count(*),min(time),max(time) FROM telemetry GROUP BY sensor_id;
SELECT DISTINCT ON(sensor_id) sensor_id,time,value,quality FROM telemetry ORDER BY sensor_id,time DESC;
SELECT time,value FROM telemetry WHERE sensor_id='S-M07-TEMP-01' AND time >= now()-interval '60 minutes' ORDER BY time;
SELECT time_bucket('1 minute',time) AS bucket,sensor_id,avg(value),min(value),max(value) FROM telemetry WHERE time >= now()-interval '2 hours' GROUP BY bucket,sensor_id ORDER BY bucket;
SELECT count(*) FROM telemetry;
SELECT * FROM alarms ORDER BY opened_at DESC LIMIT 20;
SELECT avg(extract(epoch FROM received_at-time)) AS avg_lag_seconds FROM telemetry WHERE time>=now()-interval '5 minutes';
EXPLAIN (ANALYZE,BUFFERS) SELECT time,value FROM telemetry WHERE sensor_id='S-M07-TEMP-01' AND time>=now()-interval '1 hour' ORDER BY time DESC LIMIT 100;
