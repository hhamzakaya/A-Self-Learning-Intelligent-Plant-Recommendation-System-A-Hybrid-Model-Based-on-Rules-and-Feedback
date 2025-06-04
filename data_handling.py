import pandas as pd
import pyodbc
import logging
import datetime
import joblib
from sklearn.preprocessing import OrdinalEncoder

# Profiling library import: try pandas_profiling, fallback to ydata_profiling
try:
    from pandas_profiling import ProfileReport
except ImportError:
    from ydata_profiling import ProfileReport

# Logger configuration
dlogging = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --------------------------------------------------------------
# Database Connection
# --------------------------------------------------------------
def sql_connect():
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=LAPTOP-7GK6MUOG\\SQLEXPRESS;"
            "DATABASE=Smart_Plant_Recomandation_System;"
            "Trusted_Connection=yes;"
        )
        logging.info(" Database connection established.")
        return conn
    except Exception as e:
        logging.error(f" Database connection failed: {e}")
        raise

# --------------------------------------------------------------
# Plant Data Functions
# --------------------------------------------------------------
def load_plants() -> pd.DataFrame:
    """
    Load plant records and perform basic cleaning.
    """
    conn = None
    try:
        conn = sql_connect()
        df = pd.read_sql("SELECT * FROM plants", conn)
        logging.info(f" {len(df)} plant records loaded.")

        # Basic cleaning: lowercase columns, strip whitespace\ n        df.columns = df.columns.str.strip().str.lower()
        # Convert empty strings and whitespace-only strings to NaN
        df.replace({'': pd.NA, ' ': pd.NA}, inplace=True)
        # Standardize plant_name
        if 'plant_name' in df.columns:
            df['plant_name'] = df['plant_name'].fillna('Unknown').astype(str).str.strip().str.title()
        return df
    except Exception as e:
        logging.error(f" Failed to load plant data: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()
            logging.info(" Database connection closed after loading plants.")

# --------------------------------------------------------------
# Feedback Data Handling
# --------------------------------------------------------------
def fetch_feedback_data() -> pd.DataFrame:
    """
    Fetch feedback records including timestamp.
    """
    conn = sql_connect()
    query = '''
        SELECT
            area_size, sunlight_need, environment_type, climate_type,
            watering_frequency, fertilizer_frequency, pesticide_frequency,
            has_pet, has_child, suggested_plant, user_feedback, created_at
        FROM Feedback
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    logging.info(f"Fetched {len(df)} feedback records.")
    return df


def clean_feedback_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicates, handle nulls, strip whitespace, ensure correct types.
    """
    df_clean = df.drop_duplicates().copy()

    # Categorical columns for cleaning
    cat_cols = [
        'area_size', 'sunlight_need', 'environment_type', 'climate_type',
        'watering_frequency', 'fertilizer_frequency', 'pesticide_frequency',
        'has_pet', 'has_child', 'suggested_plant'
    ]
    for col in cat_cols:
        if col in df_clean.columns:
                df_clean[col] = (
                df_clean[col]
                  .fillna('Unknown')                
                  .astype(str)
                  .str.strip()                     
                  .replace('', 'Unknown')           
                  .str.title()                     
            )

    
    df_clean['user_feedback'] = pd.to_numeric(df_clean['user_feedback'], errors='coerce').fillna(0).astype(int).clip(0,1)
    return df_clean


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time_of_day and is_weekend features based on created_at.
    """
    df_time = df.copy()
    df_time['created_at'] = pd.to_datetime(df_time['created_at'], errors='coerce')
    df_time['hour'] = df_time['created_at'].dt.hour

    def _time_of_day(h: int) -> str:
        if pd.isna(h):
            return 'Unknown'
        if 6 <= h < 12:
            return 'Morning'
        elif 12 <= h < 18:
            return 'Afternoon'
        elif 18 <= h < 24:
            return 'Evening'
        else:
            return 'Night'

    df_time['time_of_day'] = df_time['hour'].apply(_time_of_day)
    df_time['is_weekend'] = df_time['created_at'].dt.weekday.isin([5,6]).astype(int)
    return df_time


def generate_data_profile(df: pd.DataFrame, output_path: str = 'feedback_profile.html'):
    """
    Save a profiling report to HTML.
    """
    profile = ProfileReport(df, title="Feedback Data Profile", explorative=True)
    profile.to_file(output_path)
    logging.info(f"Data profile report saved to {output_path}")


def encode_categorical(df: pd.DataFrame, encoder_path: str = 'models/encoder.pkl') -> pd.DataFrame:
    """
    Encode categorical features using OrdinalEncoder and save encoder.
    """
    enc_cols = [
        'area_size', 'sunlight_need', 'environment_type', 'climate_type',
        'watering_frequency', 'fertilizer_frequency', 'pesticide_frequency',
        'has_pet', 'has_child', 'suggested_plant', 'time_of_day'
    ]
    df_enc = df.copy()
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    df_enc[enc_cols] = encoder.fit_transform(df_enc[enc_cols])
    # Persist encoder
    joblib.dump(encoder, encoder_path)
    logging.info(f"OrdinalEncoder saved to {encoder_path}")
    return df_enc

# --------------------------------------------------------------

def add_feedback(user_input: dict, suggested_plant: str, user_feedback: int) -> None:
    """
    Kullanıcının geri bildirimini Feedback tablosuna yazar.
    user_input: render_preference_form() çıktısı dict
    suggested_plant: str, önerilen bitki adı
    user_feedback: int, 1=beğendi, 0=beğenmedi
    """
    conn = sql_connect()
    cursor = conn.cursor()

  
    insert_sql = """
    INSERT INTO Feedback (
        area_size,
        sunlight_need,
        environment_type,
        climate_type,
        watering_frequency,
        fertilizer_frequency,
        pesticide_frequency,
        has_pet,
        has_child,
        suggested_plant,
        user_feedback
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        user_input["area_size"],
        user_input["sunlight_need"],
        user_input["environment_type"],
        user_input["climate_type"],
        user_input["watering_frequency"],
        user_input["fertilizer_frequency"],
        user_input["pesticide_frequency"],
        user_input["has_pet"],
        user_input["has_child"],
        suggested_plant,
        user_feedback
    )

    cursor.execute(insert_sql, params)
    conn.commit()
    cursor.close()
    conn.close()
