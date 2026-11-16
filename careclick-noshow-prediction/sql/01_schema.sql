CREATE DATABASE IF NOT EXISTS careclick CHARACTER SET utf8mb4;
USE careclick;

DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS clinics;

CREATE TABLE clinics (
    clinic_id    CHAR(4)       NOT NULL,
    clinic_name  VARCHAR(60)   NOT NULL,
    city         VARCHAR(40)   NOT NULL,
    latitude     DECIMAL(8,4)  NOT NULL,
    longitude    DECIMAL(8,4)  NOT NULL,
    PRIMARY KEY (clinic_id),
    UNIQUE KEY uq_clinic_name (clinic_name)
) ENGINE=InnoDB;

CREATE TABLE appointments (
    appointment_id     INT              NOT NULL,
    patient_id         INT              NOT NULL,
    gender             VARCHAR(7)       NOT NULL,
    age                TINYINT UNSIGNED NOT NULL,
    scheduled_date     DATE             NOT NULL,
    appointment_date   DATE             NOT NULL,
    lead_days          SMALLINT UNSIGNED NOT NULL,
    lead_quartile      TINYINT UNSIGNED NOT NULL,
    clinic             VARCHAR(60)      NOT NULL,
    city               VARCHAR(40)      NOT NULL,
    specialty          VARCHAR(40)      NOT NULL,
    sms_received       TINYINT(1)       NOT NULL,
    insurance_covered  TINYINT(1)       NOT NULL,
    previous_no_shows  TINYINT UNSIGNED NOT NULL,
    avg_temp_c         DECIMAL(4,1)     NOT NULL,
    no_show            TINYINT(1)       NOT NULL,
    PRIMARY KEY (appointment_id),
    CONSTRAINT fk_appt_clinic FOREIGN KEY (clinic) REFERENCES clinics (clinic_name),
    KEY idx_appt_clinic (clinic),
    KEY idx_appt_date (appointment_date),
    KEY idx_appt_lead (lead_days)
) ENGINE=InnoDB;
