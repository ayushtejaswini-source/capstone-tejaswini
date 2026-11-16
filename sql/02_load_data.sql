USE careclick;

LOAD DATA LOCAL INFILE 'data/clinics.csv'
INTO TABLE clinics
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(clinic_id, clinic_name, city, latitude, longitude);

LOAD DATA LOCAL INFILE 'data/Appointments_clean.csv'
INTO TABLE appointments
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(appointment_id, patient_id, gender, age, scheduled_date, appointment_date, lead_days,
 lead_quartile, clinic, city, specialty, sms_received, insurance_covered,
 previous_no_shows, avg_temp_c, no_show);

SELECT COUNT(*) AS clinics_loaded FROM clinics;
SELECT COUNT(*) AS appointments_loaded, SUM(no_show) AS no_shows FROM appointments;
