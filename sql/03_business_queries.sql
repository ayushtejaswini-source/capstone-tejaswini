USE careclick;

SELECT COUNT(*)                                   AS total_appointments,
       SUM(no_show)                               AS no_shows,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)  AS no_show_rate_pct
FROM appointments;

SELECT a.clinic,
       c.city,
       COUNT(*)                                     AS total_appointments,
       SUM(a.no_show)                               AS no_shows,
       ROUND(100.0 * SUM(a.no_show) / COUNT(*), 2)  AS no_show_rate_pct
FROM appointments a
JOIN clinics c ON c.clinic_name = a.clinic
GROUP BY a.clinic, c.city
ORDER BY no_show_rate_pct DESC;

SELECT lead_quartile,
       MIN(lead_days)                               AS min_lead_days,
       MAX(lead_days)                               AS max_lead_days,
       COUNT(*)                                     AS total_appointments,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)    AS no_show_rate_pct
FROM appointments
GROUP BY lead_quartile
ORDER BY lead_quartile;

SELECT CASE WHEN lead_days = 0  THEN '1) same day'
            WHEN lead_days <= 3  THEN '2) 1-3 days'
            WHEN lead_days <= 7  THEN '3) 4-7 days'
            WHEN lead_days <= 14 THEN '4) 8-14 days'
            WHEN lead_days <= 30 THEN '5) 15-30 days'
            ELSE                      '6) 31+ days' END AS lead_bucket,
       COUNT(*)                                     AS total_appointments,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)    AS no_show_rate_pct
FROM appointments
GROUP BY lead_bucket
ORDER BY lead_bucket;

WITH monthly AS (
    SELECT DATE_FORMAT(appointment_date, '%Y-%m') AS month,
           COUNT(*)                               AS total_appointments,
           SUM(no_show)                           AS no_shows
    FROM appointments
    GROUP BY DATE_FORMAT(appointment_date, '%Y-%m')
)
SELECT month,
       total_appointments,
       no_shows,
       ROUND(100.0 * no_shows / total_appointments, 2) AS no_show_rate_pct,
       ROUND(100.0 * no_shows / total_appointments
             - LAG(100.0 * no_shows / total_appointments) OVER (ORDER BY month), 2) AS change_vs_prev_month_pts
FROM monthly
ORDER BY month;

WITH clinic_rates AS (
    SELECT c.city,
           a.clinic,
           COUNT(*)                                 AS total_appointments,
           SUM(a.no_show)                           AS no_shows,
           100.0 * SUM(a.no_show) / COUNT(*)        AS rate
    FROM appointments a
    JOIN clinics c ON c.clinic_name = a.clinic
    GROUP BY c.city, a.clinic
)
SELECT city,
       clinic,
       total_appointments,
       ROUND(rate, 2)                                                       AS no_show_rate_pct,
       RANK() OVER (PARTITION BY city ORDER BY rate DESC)                   AS rank_in_city,
       ROUND(rate - 100.0 * SUM(no_shows) OVER (PARTITION BY city)
                    / SUM(total_appointments) OVER (PARTITION BY city), 2)  AS pts_vs_city_avg
FROM clinic_rates
ORDER BY city, rank_in_city;

SELECT lead_quartile,
       sms_received,
       COUNT(*)                                     AS total_appointments,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)    AS no_show_rate_pct
FROM appointments
GROUP BY lead_quartile, sms_received
ORDER BY lead_quartile, sms_received;

SELECT specialty,
       COUNT(*)                                          AS total_appointments,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)         AS no_show_rate_pct,
       DENSE_RANK() OVER (ORDER BY 1.0 * SUM(no_show) / COUNT(*) DESC) AS rank_overall
FROM appointments
GROUP BY specialty
ORDER BY rank_overall;

SELECT CASE WHEN previous_no_shows >= 3 THEN '3+' ELSE CAST(previous_no_shows AS CHAR) END AS past_no_shows,
       COUNT(*)                                     AS total_appointments,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)    AS no_show_rate_pct
FROM appointments
GROUP BY past_no_shows
ORDER BY past_no_shows;

SELECT CASE WHEN previous_no_shows >= 2 AND lead_days >= 8 AND sms_received = 0
            THEN 'rule-flagged risky' ELSE 'not flagged' END AS segment,
       COUNT(*)                                     AS total_appointments,
       SUM(no_show)                                 AS no_shows,
       ROUND(100.0 * SUM(no_show) / COUNT(*), 2)    AS no_show_rate_pct
FROM appointments
GROUP BY segment
ORDER BY segment;
