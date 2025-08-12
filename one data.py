from minio import Minio
import os

# MinIO client
client = Minio(
    "localhost:9000",  
    access_key="minioadmin",  
    secret_key="minioadmin",  
    secure=False
)


bucket_name = "raw"
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)

# Upload all datasets
datasets = [
    "care_reception.csv",
    "event.csv",
    "participation.csv",
    "patients.csv"
]

for file in datasets:
    client.fput_object(bucket_name, f"data/{file}", file)
    print(f"Uploaded {file} to MinIO bucket {bucket_name}")
# process_unify.py
import io
import pandas as pd
from minio import Minio

# --- MinIO Configuration ---
MINIO_HOST = "127.0.0.1:9000"
MINIO_ACCESS = "minioadmin"
MINIO_SECRET = "minioadmin"
BUCKET_RAW = "raw"
BUCKET_PROCESSED = "processed"

client = Minio(MINIO_HOST, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)

def read_csv_from_minio(bucket, object_name):
    try:
        response = client.get_object(bucket, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return pd.read_csv(io.BytesIO(data))
    except Exception as e:
        print(f"❌ Could not load {object_name} from bucket '{bucket}': {e}")
        return pd.DataFrame()

# 1) Load datasets (correct paths)
care_reception = read_csv_from_minio(BUCKET_RAW, "data/care_reception.csv")
event          = read_csv_from_minio(BUCKET_RAW, "data/event.csv")
participation  = read_csv_from_minio(BUCKET_RAW, "data/participation.csv")
patients       = read_csv_from_minio(BUCKET_RAW, "data/patients.csv")

# 2) Normalize column names
def normalize_cols(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    df.columns = df.columns.str.replace(r'[^\w]', '_', regex=True)
    return df

for df in [care_reception, event, participation, patients]:
    if not df.empty:
        normalize_cols(df)

print("\n--- Columns after normalization ---")
print("participation:", participation.columns.tolist())
print("patients:", patients.columns.tolist())
print("event:", event.columns.tolist())
print("care_reception:", care_reception.columns.tolist())

# 3) Merge participation + patients
if 'patient_id' in participation.columns and 'id' in patients.columns:
    merged = pd.merge(participation, patients, left_on='patient_id', right_on='id', how='left', suffixes=('_part', '_pat'))
else:
    print("⚠ Missing patient_id or id, skipping this merge")
    merged = participation.copy()

# 4) Merge with event
if 'event_id' in merged.columns and 'id' in event.columns:
    merged = pd.merge(merged, event, left_on='event_id', right_on='id', how='left', suffixes=('', '_event'))
else:
    print("⚠ Missing event_id or event.id, skipping this merge")

# 5) Merge with care_reception
if 'participation_id' in care_reception.columns and 'id' in merged.columns:
    merged = pd.merge(merged, care_reception, left_on='id', right_on='participation_id', how='left', suffixes=('', '_care'))
else:
    print("⚠ Missing participation_id key for care_reception merge")

# 6) Add full_name & DOB
if 'first_name' in merged.columns and 'last_name' in merged.columns:
    merged['full_name'] = merged['first_name'].fillna('') + " " + merged['last_name'].fillna('')
if 'date_of_birth' in merged.columns:
    merged['date_of_birth'] = pd.to_datetime(merged['date_of_birth'], errors='coerce')

# 7) Final cleanup
merged = merged.drop_duplicates()

# 8) Save & upload unified table
output_file = "unified_data.csv"
merged.to_csv(output_file, index=False)
client.fput_object(BUCKET_PROCESSED, "unified/unified_data.csv", output_file)

print(f"\n✅ Unified dataset created with {len(merged)} rows and {len(merged.columns)} columns.")


import pandas as pd

file_path = r"C:\Users\meena\OneDrive\Documents\Desktop\Minio_data\dataset\Assessment_Data\unified_with_patient_info.csv"

# Read CSV, disable low_memory warning
df = pd.read_csv(file_path, low_memory=False)

# Force 'full_name' to string before stripping spaces
df['full_name'] = df['full_name'].astype(str).str.strip()


import pandas as pd

# Load datasets
care_reception = pd.read_csv("care_reception.csv")
patients = pd.read_csv("patients.csv")

print("Care Reception columns:", care_reception.columns.tolist())
print("Patients columns:", patients.columns.tolist())

# Merge care_reception.patient_id with patients.id
merged_df = care_reception.merge(
    patients,
    left_on="patient_id",
    right_on="id",
    how="inner"
)

# Create full name column
merged_df["full_name"] = merged_df["first_name"].fillna('') + " " + merged_df["last_name"].fillna('')

# Extract only required columns
patients_info = merged_df[["full_name", "date_of_birth"]]

# Drop duplicates
patients_info = patients_info.drop_duplicates()

# Validate: remove rows where DOB or name is missing
patients_info = patients_info.dropna(subset=["full_name", "date_of_birth"])
patients_info = patients_info[patients_info["full_name"].str.strip() != ""]

# Save to CSV
patients_info.to_csv("patients_info.csv", index=False)

print("✅ Patients info extracted and saved to patients_info.csv")
print(patients_info.head())
import pandas as pd

# Load datasets
care_reception = pd.read_csv("care_reception.csv")
patients = pd.read_csv("patients.csv")

print("Care Reception columns:", care_reception.columns.tolist())
print("Patients columns:", patients.columns.tolist())

# Merge care_reception.patient_id with patients.id
merged_df = care_reception.merge(
    patients,
    left_on="patient_id",
    right_on="id",
    how="inner"
)

# Create full name column
merged_df["full_name"] = merged_df["first_name"].fillna('') + " " + merged_df["last_name"].fillna('')

# Extract only required columns
patients_info = merged_df[["full_name", "date_of_birth"]]

# Drop duplicates
patients_info = patients_info.drop_duplicates()

# Validate: remove rows where DOB or name is missing
patients_info = patients_info.dropna(subset=["full_name", "date_of_birth"])
patients_info = patients_info[patients_info["full_name"].str.strip() != ""]

# Save to CSV
patients_info.to_csv("patients_info.csv", index=False)

print("✅ Patients info extracted and saved to patients_info.csv")
print(patients_info.head())
import pandas as pd

# Load datasets
care_reception = pd.read_csv("care_reception.csv")
patients = pd.read_csv("patients.csv")

print("Care Reception columns:", care_reception.columns.tolist())
print("Patients columns:", patients.columns.tolist())

# Merge care_reception.patient_id with patients.id
merged_df = care_reception.merge(
    patients,
    left_on="patient_id",
    right_on="id",
    how="inner"
)

# Create full name column
merged_df["full_name"] = merged_df["first_name"].fillna('') + " " + merged_df["last_name"].fillna('')

# Extract only required columns
patients_info = merged_df[["full_name", "date_of_birth"]]

# Drop duplicates
patients_info = patients_info.drop_duplicates()

# Validate: remove rows where DOB or name is missing
patients_info = patients_info.dropna(subset=["full_name", "date_of_birth"])
patients_info = patients_info[patients_info["full_name"].str.strip() != ""]

# Save to CSV
patients_info.to_csv("patients_info.csv", index=False)

print("✅ Patients info extracted and saved to patients_info.csv")
print(patients_info.head())


from minio import Minio
from minio.error import S3Error

# Initialize MinIO client
client = Minio(
    "127.0.0.1:9000",           # Replace with your MinIO server address
    access_key="minioadmin", 
    secret_key="minioadmin",
    secure=False                 # Set True if using HTTPS
)

bucket_name = "raw"             # Your target bucket name
local_file_path = r"C:\Users\meena\OneDrive\Documents\Desktop\Minio_data\dataset\Assessment_Data\patients_info.csv"   # Full local path of the file
object_name = "processed/patients_info.csv"         # Path in the bucket (folder "processed/")

try:
    # Check if bucket exists, create if not
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created.")
    else:
        print(f"Bucket '{bucket_name}' already exists.")

    # Upload the file
    client.fput_object(bucket_name, object_name, local_file_path)
    print(f"Uploaded '{local_file_path}' as '{object_name}' in bucket '{bucket_name}'.")

except S3Error as err:
    print(f"MinIO error: {err}")



