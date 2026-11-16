from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_APPOINTMENTS = 12_000
N_PATIENTS = 6_000
N_NOTES = 40

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
rng = np.random.default_rng(SEED)

clinics = pd.DataFrame(
    [
        ("CC01", "CareClick Indiranagar", "Bengaluru", 12.9784, 77.6408),
        ("CC02", "CareClick Whitefield", "Bengaluru", 12.9698, 77.7500),
        ("CC03", "CareClick Andheri", "Mumbai", 19.1136, 72.8697),
        ("CC04", "CareClick Bandra", "Mumbai", 19.0596, 72.8295),
        ("CC05", "CareClick Dwarka", "Delhi", 28.5921, 77.0460),
        ("CC06", "CareClick Saket", "Delhi", 28.5245, 77.2066),
        ("CC07", "CareClick T Nagar", "Chennai", 13.0418, 80.2341),
        ("CC08", "CareClick Adyar", "Chennai", 13.0012, 80.2565),
    ],
    columns=["clinic_id", "clinic_name", "city", "latitude", "longitude"],
)
clinics.to_csv(DATA / "clinics.csv", index=False)

patients = pd.DataFrame(
    {
        "patient_id": np.arange(700_001, 700_001 + N_PATIENTS),
        "gender": rng.choice(["M", "F"], N_PATIENTS, p=[0.44, 0.56]),
        "age": np.clip(rng.normal(38, 18, N_PATIENTS).round(), 1, 90).astype(int),
        "unreliability": rng.gamma(1.2, 0.6, N_PATIENTS),
    }
)

specialties = ["General Medicine", "Pediatrics", "Dermatology", "Cardiology", "Orthopedics", "Dental"]
spec_p = [0.34, 0.14, 0.14, 0.10, 0.12, 0.16]
spec_effect = {"General Medicine": 0.0, "Pediatrics": -0.30, "Dermatology": 0.25,
               "Cardiology": -0.40, "Orthopedics": 0.0, "Dental": 0.20}
clinic_effect = dict(zip(clinics.clinic_id, rng.normal(0, 0.28, len(clinics))))

appt = pd.DataFrame(
    {
        "appointment_id": np.arange(1_000_001, 1_000_001 + N_APPOINTMENTS),
        "patient_id": rng.choice(patients.patient_id, N_APPOINTMENTS),
        "clinic_id": rng.choice(clinics.clinic_id, N_APPOINTMENTS,
                                p=[0.15, 0.11, 0.14, 0.12, 0.11, 0.13, 0.12, 0.12]),
        "specialty": rng.choice(specialties, N_APPOINTMENTS, p=spec_p),
    }
)
appt = appt.merge(patients, on="patient_id", how="left").merge(
    clinics[["clinic_id", "clinic_name", "city"]], on="clinic_id", how="left")

all_days = pd.date_range("2026-01-05", "2026-09-30")
all_days = all_days[all_days.dayofweek != 6]
appt["appointment_date"] = rng.choice(all_days, N_APPOINTMENTS)
lead = np.where(rng.random(N_APPOINTMENTS) < 0.15, 0,
                np.minimum(1 + rng.gamma(1.4, 7.0, N_APPOINTMENTS).astype(int), 60))
appt["lead_days"] = lead
appt["scheduled_date"] = pd.to_datetime(appt["appointment_date"]) - pd.to_timedelta(lead, unit="D")

appt["sms_received"] = ((rng.random(N_APPOINTMENTS) < 0.62) & (lead >= 1)).astype(int)
appt["insurance_covered"] = (rng.random(N_APPOINTMENTS) < 0.48).astype(int)
appt["previous_no_shows"] = np.minimum(rng.poisson(appt["unreliability"].values * 0.9), 6)

def prob_no_show(intercept):
    age = appt["age"].values
    z = (
        intercept
        + 0.045 * np.minimum(appt["lead_days"].values, 45)
        - 0.60 * appt["sms_received"].values
        - 0.35 * appt["insurance_covered"].values
        + 0.55 * appt["previous_no_shows"].values
        + 0.35 * ((age >= 18) & (age <= 30))
        - 0.30 * (age >= 60)
        + appt["specialty"].map(spec_effect).values
        + appt["clinic_id"].map(clinic_effect).values
    )
    return 1 / (1 + np.exp(-z))

lo, hi = -6.0, 2.0
for _ in range(40):
    mid = (lo + hi) / 2
    if prob_no_show(mid).mean() > 0.20:
        hi = mid
    else:
        lo = mid
appt["no_show_true"] = (rng.random(N_APPOINTMENTS) < prob_no_show(mid)).astype(int)

raw = pd.DataFrame({"AppointmentID": appt["appointment_id"], "PatientId": appt["patient_id"]})

def pick(options, n):
    return options[rng.integers(0, len(options), n)]

gender_variants = {"M": ["M", "Male", "male", "m", "MALE"], "F": ["F", "Female", "female", "f", "FEMALE"]}
raw["Gender"] = [rng.choice(gender_variants[g]) for g in appt["gender"]]
raw.loc[rng.random(N_APPOINTMENTS) < 0.01, "Gender"] = ""

age = appt["age"].astype(float).copy()
r = rng.random(N_APPOINTMENTS)
age[r < 0.012] = np.nan
age[(r >= 0.012) & (r < 0.015)] = -1
age[(r >= 0.015) & (r < 0.017)] = 150
raw["Age"] = age

def messy_date(ts):
    k = rng.integers(0, 3)
    if k == 0:
        return ts.strftime("%Y-%m-%d")
    if k == 1:
        return ts.strftime("%d/%m/%Y")
    return ts.strftime("%d %b %Y")

raw["ScheduledDay"] = [messy_date(t) for t in appt["scheduled_date"]]
raw["AppointmentDay"] = [messy_date(t) for t in appt["appointment_date"]]

short = {"Indiranagar": ["CareClick Indiranagar", "careclick indiranagar ", "CC Indiranagar", "Indiranagar Clinic"],
         "Whitefield": ["CareClick Whitefield", "CARECLICK WHITEFIELD", "CC-Whitefield", "whitefield clinic"],
         "Andheri": ["CareClick Andheri", "careclick andheri", "CC Andheri ", "Andheri Clinic"],
         "Bandra": ["CareClick Bandra", "CARECLICK BANDRA", "CC Bandra", "bandra clinic "],
         "Dwarka": ["CareClick Dwarka", "careclick dwarka", "CC Dwarka", "Dwarka Clinic"],
         "Saket": ["CareClick Saket", "CARECLICK SAKET ", "CC-Saket", "saket clinic"],
         "T Nagar": ["CareClick T Nagar", "careclick t-nagar", "CC T Nagar", "TNagar Clinic"],
         "Adyar": ["CareClick Adyar", "CARECLICK ADYAR", "CC Adyar", "adyar clinic"]}
raw["Clinic"] = [rng.choice(short[n.replace("CareClick ", "")]) for n in appt["clinic_name"]]

city_variants = {"Bengaluru": ["Bengaluru", "Bangalore", "BENGALURU", "bengaluru"],
                 "Mumbai": ["Mumbai", "Bombay", "MUMBAI", "mumbai "],
                 "Delhi": ["Delhi", "New Delhi", "DELHI", "delhi"],
                 "Chennai": ["Chennai", "Madras", "CHENNAI", "chennai"]}
raw["City"] = [rng.choice(city_variants[c]) for c in appt["city"]]
raw.loc[rng.random(N_APPOINTMENTS) < 0.03, "City"] = ""

spec_variants = {"General Medicine": ["General Medicine", "general medicine", "Gen Medicine ", "GENERAL MEDICINE"],
                 "Pediatrics": ["Pediatrics", "paediatrics", "PEDIATRICS", "Pediatrics "],
                 "Dermatology": ["Dermatology", "dermatology", "Derma", "DERMATOLOGY"],
                 "Cardiology": ["Cardiology", "cardiology ", "CARDIOLOGY", "Cardio"],
                 "Orthopedics": ["Orthopedics", "orthopaedics", "Ortho", "ORTHOPEDICS"],
                 "Dental": ["Dental", "dental", "DENTAL", "Dentistry"]}
raw["Specialty"] = [rng.choice(spec_variants[s]) for s in appt["specialty"]]

def binary_messy(series, yes_no=True):
    out = []
    for v in series:
        k = rng.integers(0, 3)
        if k == 0:
            out.append("Yes" if v else "No")
        elif k == 1:
            out.append("Y" if v else "N")
        else:
            out.append(str(int(v)))
    return out

raw["SMS_received"] = binary_messy(appt["sms_received"])
raw["Insured"] = binary_messy(appt["insurance_covered"])
raw["PreviousNoShows"] = appt["previous_no_shows"]
raw["No-show"] = binary_messy(appt["no_show_true"])

bad = rng.choice(N_APPOINTMENTS, int(0.004 * N_APPOINTMENTS), replace=False)
raw.loc[bad, ["ScheduledDay", "AppointmentDay"]] = raw.loc[bad, ["AppointmentDay", "ScheduledDay"]].values
bad_mask = np.zeros(N_APPOINTMENTS, bool)
bad_mask[bad] = True
bad_mask &= (appt["lead_days"].values > 0)
dups = raw.sample(int(0.015 * N_APPOINTMENTS), random_state=SEED)
raw_out = pd.concat([raw, dups], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)
raw_out.to_csv(DATA / "Appointments.csv", index=False)

reasons = {
    "transport": [
        "Called patient. Says the bus strike meant no way to reach the clinic. Wants a new slot, mornings are best.",
        "Spoke to pt - auto-rickshaw never showed up and the metro was down. Apologetic, would like to rebook this week.",
        "Pt stuck in heavy traffic after a road accident near the clinic, gave up and went home. OK to rebook any time.",
    ],
    "work_conflict": [
        "Patient got pulled into an urgent meeting at the office and could not leave. Asked for an evening slot after 6pm.",
        "Spoke with pt: boss refused leave that day. Frustrated, says clinic hours do not suit working people. Needs a weekend slot.",
        "Called - patient on a work trip, forgot to cancel. Will let us know when back, no rebooking right now.",
    ],
    "forgot": [
        "Patient simply forgot about the appointment, did not see the reminder. Very sorry. Rebook for next week please.",
        "Pt says she lost track of the date. No SMS noticed. Wants us to call a day before next time. Afternoons preferred.",
        "Called patient, he mixed up the date with another day. Embarrassed, wants to reschedule soon.",
    ],
    "felt_better": [
        "Patient says symptoms went away on their own so they did not come. No need to rebook for now.",
        "Pt felt much better after home remedy and skipped the visit. Does not want to reschedule, will call if it returns.",
    ],
    "cost_insurance": [
        "Patient worried about the consultation fee and unsure if insurance covers it. Upset, wants cost explained before rebooking.",
        "Pt says insurance claim got rejected last time so avoided the visit. Wants to know the self-pay price first.",
    ],
    "illness": [
        "Patient had high fever and vomiting on the day, could not travel. Asked to rebook as soon as possible, mornings.",
        "Spoke to pt's son - patient was admitted with severe chest pain at another hospital. Urgent, please call back later.",
        "Pt down with flu and body ache that morning. Will rebook once recovered, maybe next week afternoon.",
    ],
    "family_emergency": [
        "Patient's father had a medical emergency, so they rushed to the hospital. Very stressed. Rebook later this month.",
        "Pt had a death in the family and travelled out of town. Will contact us when back.",
    ],
    "weather": [
        "Heavy rain and waterlogging on the road so patient could not come. Wants to reschedule, any afternoon works.",
        "Pt says the extreme heat made her avoid travelling in the afternoon. Wants an early morning slot next time.",
    ],
    "childcare": [
        "Mother had no one to look after the kids and could not bring them along. Asked for a Saturday morning slot.",
        "Patient says school pickup clashed with the slot and no childcare. Wants a slot after school hours.",
    ],
    "other": [
        "Patient did not give a clear reason, call was short. Did not ask to rebook.",
        "Unable to reach patient, voicemail left. No information on why they missed the appointment.",
    ],
}
reason_weights = {"transport": 0.14, "work_conflict": 0.14, "forgot": 0.20, "felt_better": 0.08, "cost_insurance": 0.08,
                  "illness": 0.12, "family_emergency": 0.05, "weather": 0.06, "childcare": 0.06, "other": 0.07}

eligible = appt.loc[(appt["no_show_true"] == 1) & (~bad_mask), "appointment_id"].values
chosen = rng.choice(eligible, N_NOTES, replace=False)
keys = list(reason_weights)
picked = rng.choice(keys, N_NOTES, p=list(reason_weights.values()))
notes = pd.DataFrame(
    {
        "note_id": [f"N{idx:03d}" for idx in range(1, N_NOTES + 1)],
        "appointment_id": chosen,
        "call_date": [(pd.Timestamp("2026-10-01") + pd.Timedelta(days=int(d))).strftime("%Y-%m-%d")
                      for d in rng.integers(0, 28, N_NOTES)],
        "note_text": [rng.choice(reasons[k]) for k in picked],
    }
)
notes.to_csv(DATA / "follow_up_notes.csv", index=False)

print(f"Appointments.csv     : {len(raw_out):,} rows (incl. {len(dups)} duplicates)")
print(f"True no-show rate    : {appt['no_show_true'].mean():.3f}")
print(f"clinics.csv          : {len(clinics)} clinics")
print(f"follow_up_notes.csv  : {len(notes)} notes")
