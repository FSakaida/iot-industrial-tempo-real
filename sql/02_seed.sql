INSERT INTO assets VALUES
('MOTOR-07','Motor principal 07','Linha A',5),
('COMP-02','Compressor 02','Utilidades',4),
('BOMBA-03','Bomba 03','Linha B',3);
INSERT INTO sensors(id,asset_id,sensor_type,unit,sample_seconds) VALUES
('S-M07-TEMP-01','MOTOR-07','temperature','C',2),
('S-M07-VIB-01','MOTOR-07','vibration','mm/s',2),
('S-C02-PRES-01','COMP-02','pressure','bar',5),
('S-C02-TEMP-01','COMP-02','temperature','C',5),
('S-B03-CURR-01','BOMBA-03','current','A',5),
('S-B03-FLOW-01','BOMBA-03','flow','L/min',5);
INSERT INTO sensor_thresholds(sensor_id,warn_high,critical_high) VALUES
('S-M07-TEMP-01',75,85),('S-M07-VIB-01',4.5,7),('S-C02-PRES-01',8.2,9);
