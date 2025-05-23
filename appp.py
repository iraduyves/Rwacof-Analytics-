from flask import Flask, jsonify, send_file, request
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import logging
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# More detailed ATC classification with disease prevalence by season
ATC_CATEGORIES = {
    "M01AB": {
        "description": "Anti-inflammatory and antirheumatic products, non-steroids, Acetic acid derivatives",
        "examples": ["DICLOFENAC", "INDOMETHACIN", "KETOROLAC"],
        "seasonal_factor": {"Itumba": 1.2, "Icyi": 0.9, "Umuhindo": 1.3, "Urugaryi": 1.0}
    },
    "M01AE": {
        "description": "Anti-inflammatory and antirheumatic products, non-steroids, Propionic acid derivatives",
        "examples": ["IBUPROFEN", "NAPROXEN", "KETOPROFEN"],
        "seasonal_factor": {"Itumba": 1.2, "Icyi": 0.8, "Umuhindo": 1.3, "Urugaryi": 0.9}
    },
    "N02BA": {
        "description": "Other analgesics and antipyretics, Salicylic acid and derivatives",
        "examples": ["ASPIRIN", "DIFLUNISAL"],
        "seasonal_factor": {"Itumba": 1.1, "Icyi": 0.9, "Umuhindo": 1.2, "Urugaryi": 1.0}
    },
    "N02BE/B": {
        "description": "Other analgesics and antipyretics, Pyrazolones and Anilides",
        "examples": ["PARACETAMOL", "METAMIZOLE"],
        "seasonal_factor": {"Itumba": 1.3, "Icyi": 0.8, "Umuhindo": 1.4, "Urugaryi": 1.1}
    },
    "N05B": {
        "description": "Psycholeptics, Anxiolytics",
        "examples": ["DIAZEPAM", "LORAZEPAM", "ALPRAZOLAM"],
        "seasonal_factor": {"Itumba": 1.0, "Icyi": 1.0, "Umuhindo": 1.0, "Urugaryi": 1.1}
    },
    "N05C": {
        "description": "Psycholeptics, Hypnotics and sedatives",
        "examples": ["ZOLPIDEM", "ZOPICLONE", "TEMAZEPAM"],
        "seasonal_factor": {"Itumba": 0.9, "Icyi": 1.0, "Umuhindo": 0.9, "Urugaryi": 1.2}
    },
    "R03": {
        "description": "Drugs for obstructive airway diseases",
        "examples": ["SALBUTAMOL", "BUDESONIDE_FORMOTEROL", "MONTELUKAST"],
        "seasonal_factor": {"Itumba": 1.5, "Icyi": 0.7, "Umuhindo": 1.6, "Urugaryi": 1.1}
    },
    "R06": {
        "description": "Antihistamines for systemic use",
        "examples": ["LORATADINE", "CETIRIZINE", "DIPHENHYDRAMINE"],
        "seasonal_factor": {"Itumba": 1.4, "Icyi": 0.8, "Umuhindo": 1.5, "Urugaryi": 0.9}
    }
}

# Create a drug database with more realistic attributes
DRUG_DATABASE = {}
for atc_code, data in ATC_CATEGORIES.items():
    for drug in data["examples"]:
        base_price = round(np.random.uniform(2.5, 50.0), 2)
        effectiveness = np.random.randint(3, 6)
        time_on_market = np.random.randint(6, 120)
        
        DRUG_DATABASE[drug] = {
            "atc_code": atc_code,
            "base_price": base_price,
            "effectiveness": effectiveness,
            "time_on_market": time_on_market,
            "base_demand": np.random.randint(100, 1000),
            "typical_prescription_duration": np.random.randint(3, 30),  # Days
            "shelf_life": np.random.randint(12, 36)  # Months
        }

# Rwanda provinces and healthcare centers
RWANDA_PROVINCES = ["Kigali", "Northern", "Eastern", "Southern", "Western"]
HEALTHCARE_CENTERS = {
    "Kigali": ["CHUK", "King Faisal Hospital", "Kibagabaga Hospital", "Nyarugenge Health Center", "Rwanda Military Hospital"],
    "Northern": ["Ruhengeri Hospital", "Byumba Hospital", "Kinihira Hospital"],
    "Eastern": ["Rwamagana Hospital", "Kibungo Hospital", "Nyagatare Health Center"],
    "Southern": ["CHUB", "Kabutare Hospital", "Kigeme Hospital"],
    "Western": ["Kibuye Hospital", "Gisenyi Hospital", "Kabaya Hospital"]
}

# Demographic data for different provinces (estimated)
DEMOGRAPHIC_DATA = {
    "Kigali": {
        "population_density": "high",  # Urban center
        "age_distribution": {"0-14": 0.35, "15-64": 0.62, "65+": 0.03},
        "income_level": "higher", 
        "education_level": "higher",
        "disease_prevalence": {
            "M01AB": 1.1,  # Higher rates of inflammatory conditions in urban areas
            "M01AE": 1.1,
            "N02BA": 1.0,
            "N02BE/B": 1.05,
            "N05B": 1.3,   # Higher anxiety rates in urban settings
            "N05C": 1.2,   # Sleep disorders more common in urban areas
            "R03": 1.15,   # Higher respiratory issues due to urban pollution
            "R06": 1.2     # More allergies in urban areas
        }
    },
    "Northern": {
        "population_density": "medium",
        "age_distribution": {"0-14": 0.38, "15-64": 0.58, "65+": 0.04},
        "income_level": "medium",
        "education_level": "medium",
        "disease_prevalence": {
            "M01AB": 1.05,
            "M01AE": 1.05,
            "N02BA": 1.0,
            "N02BE/B": 1.0,
            "N05B": 0.9,
            "N05C": 0.9,
            "R03": 0.95,
            "R06": 0.9
        }
    },
    "Eastern": {
        "population_density": "low",
        "age_distribution": {"0-14": 0.4, "15-64": 0.56, "65+": 0.04},
        "income_level": "lower",
        "education_level": "lower",
        "disease_prevalence": {
            "M01AB": 1.0,
            "M01AE": 1.0,
            "N02BA": 1.1,  # Higher use of basic analgesics in lower-income areas
            "N02BE/B": 1.1,
            "N05B": 0.85,
            "N05C": 0.85,
            "R03": 1.05,   # Different respiratory disease patterns in rural areas
            "R06": 0.85
        }
    },
    "Southern": {
        "population_density": "medium-low",
        "age_distribution": {"0-14": 0.39, "15-64": 0.57, "65+": 0.04},
        "income_level": "medium-low",
        "education_level": "medium-low",
        "disease_prevalence": {
            "M01AB": 1.0,
            "M01AE": 1.0,
            "N02BA": 1.05,
            "N02BE/B": 1.05,
            "N05B": 0.9,
            "N05C": 0.9,
            "R03": 1.0,
            "R06": 0.9
        }
    },
    "Western": {
        "population_density": "medium",
        "age_distribution": {"0-14": 0.38, "15-64": 0.58, "65+": 0.04},
        "income_level": "medium",
        "education_level": "medium",
        "disease_prevalence": {
            "M01AB": 1.0,
            "M01AE": 1.0,
            "N02BA": 1.0,
            "N02BE/B": 1.0,
            "N05B": 0.95,
            "N05C": 0.95,
            "R03": 1.0,
            "R06": 0.95
        }
    }
}

# Rwanda holidays for realism
RWANDA_HOLIDAYS = [
    datetime(2024, 1, 1),   # New Year's Day
    datetime(2024, 1, 2),   # Day after New Year
    datetime(2024, 2, 1),   # Heroes' Day
    datetime(2024, 4, 7),   # Genocide Memorial Day (week-long impact)
    datetime(2024, 4, 8),
    datetime(2024, 4, 9),
    datetime(2024, 4, 10),
    datetime(2024, 4, 11),
    datetime(2024, 4, 12),
    datetime(2024, 4, 13),
    datetime(2024, 5, 1),   # Labor Day
    datetime(2024, 7, 1),   # Independence Day
    datetime(2024, 7, 4),   # Liberation Day
    datetime(2024, 8, 15),  # Assumption Day
    datetime(2024, 12, 25), # Christmas Day
    datetime(2024, 12, 26)  # Boxing Day
]

# Rwanda-specific disease outbreaks (hypothetical)
DISEASE_OUTBREAKS = [
    {"start_date": datetime(2024, 3, 15), "end_date": datetime(2024, 4, 30), 
     "disease": "Respiratory Infection", "affected_atc": ["R03", "R06", "N02BE/B"], "intensity": 1.8},
    {"start_date": datetime(2024, 9, 1), "end_date": datetime(2024, 10, 15), 
     "disease": "Malaria Surge", "affected_atc": ["N02BE/B"], "intensity": 1.6},
    {"start_date": datetime(2024, 11, 10), "end_date": datetime(2024, 12, 20), 
     "disease": "Gastrointestinal Outbreak", "affected_atc": ["N02BA", "N02BE/B"], "intensity": 1.5}
]

def get_rwanda_season(month):
    """Return Rwanda's season for the given month."""
    if month in [3, 4, 5]:
        return "Itumba"      # Long rainy
    elif month in [6, 7, 8]:
        return "Icyi"        # Long dry
    elif month in [9, 10, 11]:
        return "Umuhindo"    # Short rainy
    else:
        return "Urugaryi"    # Short dry (Dec–Feb)

@lru_cache(maxsize=366)
def is_holiday_or_near(date):
    """Check if date is a holiday or within 3 days of one."""
    holiday_proximity = min((abs((date - h).days) for h in RWANDA_HOLIDAYS), default=100)
    if holiday_proximity <= 3:
        return 1
    return 0

def is_during_outbreak(date, atc_code):
    """Return outbreak intensity factor if date falls during an outbreak affecting the ATC code."""
    for outbreak in DISEASE_OUTBREAKS:
        if (outbreak["start_date"] <= date <= outbreak["end_date"] and 
                atc_code in outbreak["affected_atc"]):
            return outbreak["intensity"]
    return 1.0

def generate_supply_chain_delay(province, date):
    """Generate more realistic supply chain delays based on location and season."""
    base_weights = {
        "Kigali": [0.7, 0.2, 0.08, 0.02],
        "Northern": [0.5, 0.3, 0.15, 0.05],
        "Eastern": [0.5, 0.25, 0.15, 0.1],
        "Southern": [0.5, 0.25, 0.15, 0.1],
        "Western": [0.4, 0.3, 0.2, 0.1]
    }
    
    # Adjust weights for rainy seasons
    season = get_rwanda_season(date.month)
    weights = base_weights[province].copy()
    
    if season in ["Itumba", "Umuhindo"]:  # Rainy seasons
        # Shift weight from "None" to higher delay categories
        shift = 0.2 if season == "Itumba" else 0.15  # Long rainy has more impact
        weights[0] -= shift
        weights[1] += shift * 0.4
        weights[2] += shift * 0.4
        weights[3] += shift * 0.2
    
    return random.choices(["None", "Low", "Medium", "High"], weights=weights)[0]

def generate_drug_price(drug_name, date, province):
    """Generate price variations based on multiple factors."""
    base_price = DRUG_DATABASE[drug_name]["base_price"]
    
    # Geographic factor
    geo_factor = {
        "Kigali": 1.1,       # Higher prices in capital
        "Northern": 0.95,
        "Eastern": 0.9,
        "Southern": 0.92,
        "Western": 0.93
    }[province]
    
    # Time-based factor (subtle price increases over time)
    days_since_start = (date - datetime(2024, 1, 1)).days
    time_factor = 1 + (days_since_start / 365 * 0.05)  # Up to 5% increase over the year
    
    # Random fluctuation
    random_factor = random.uniform(0.97, 1.03)
    
    return round(base_price * geo_factor * time_factor * random_factor, 2)

def calculate_units_sold(base_demand, date, atc_code, drug_name, price, 
                         province, health_center, supply_delay, promotion):
    """Calculate units sold with multiple realistic factors."""
    # Get the seasonal factor for this drug category
    season = get_rwanda_season(date.month)
    seasonal_factor = ATC_CATEGORIES[atc_code]["seasonal_factor"][season]
    
    # Base calculation
    units = base_demand * seasonal_factor
    
    # Apply disease outbreak factor if applicable
    outbreak_factor = is_during_outbreak(date, atc_code)
    units *= outbreak_factor
    
    # Apply demographic factor based on province and drug type
    demographic_factor = DEMOGRAPHIC_DATA[province]["disease_prevalence"][atc_code]
    units *= demographic_factor
    
    # Holiday effect
    holiday_effect = 1 + (is_holiday_or_near(date) * 0.15)
    units *= holiday_effect
    
    # Day of week patterns (weekends have lower hospital visits)
    day_of_week = date.weekday()
    if day_of_week >= 5:  # Weekend
        units *= 0.7
    
    # Price elasticity effect - adjusted by income level
    avg_price = DRUG_DATABASE[drug_name]["base_price"]
    price_ratio = price / avg_price
    
    # Income-adjusted price elasticity
    income_elasticity_factor = {
        "higher": 0.3,     # Wealthy areas less sensitive to price
        "medium": 0.4,
        "medium-low": 0.45,
        "lower": 0.5       # Poorer areas more sensitive to price
    }[DEMOGRAPHIC_DATA[province]["income_level"]]
    
    if price_ratio > 1:
        units *= (1 - (price_ratio - 1) * income_elasticity_factor)
    else:
        units *= (1 + (1 - price_ratio) * (income_elasticity_factor * 0.6))
    
    # Promotion effect
    if promotion:
        units *= 1.2
    
    # Supply chain effect
    availability_factor = {
        "None": 1.0,
        "Low": 0.9,
        "Medium": 0.75,
        "High": 0.5
    }[supply_delay]
    units *= availability_factor
    
    # Center size factor (bigger hospitals use more)
    center_size_factor = 1.0
    if "Hospital" in health_center:
        if any(premium in health_center for premium in ["CHUK", "King Faisal", "CHUB"]):
            center_size_factor = 1.5
        else:
            center_size_factor = 1.2
    units *= center_size_factor

    units *= random.uniform(0.9, 1.1)
    
    return max(int(units), 0) 

def generate_dataset(start_date, end_date, include_trends=True, increase_noise=False, shuffle_target=False):
    logger.info(f"Generating data from {start_date} to {end_date}")
    rows = []
    date_range = pd.date_range(start_date, end_date)
    
    # Generate data for each province and health center
    for province in RWANDA_PROVINCES:
        # Extract demographic data for this province
        province_demographics = DEMOGRAPHIC_DATA[province]
        population_density = province_demographics["population_density"]
        age_distribution = province_demographics["age_distribution"]
        income_level = province_demographics["income_level"]
        
        for health_center in HEALTHCARE_CENTERS[province]:
            logger.info(f"Generating data for {health_center} in {province} province")
            
            # Determine health center type
            if "Hospital" in health_center:
                if any(premium in health_center for premium in ["CHUK", "King Faisal", "CHUB", "Rwanda Military Hospital"]):
                    center_type = "referral_hospital"
                else:
                    center_type = "district_hospital"
            else:
                center_type = "health_center"
            
            # For each drug
            for drug_name, drug_data in DRUG_DATABASE.items():
                atc_code = drug_data["atc_code"]
                base_demand = drug_data["base_demand"]
                
                # Adjust base demand by demographics and center type
                # Referral hospitals see more rare/complex cases
                if center_type == "referral_hospital":
                    if atc_code in ["N05B", "N05C", "R03"]:  # More specialized medications
                        base_demand *= 1.3
                elif center_type == "health_center":
                    if atc_code in ["N02BA", "N02BE/B", "M01AE"]:  # Common medications
                        base_demand *= 1.2
                    else:
                        base_demand *= 0.7  # Less specialized meds at health centers
                
                # Age distribution impacts on certain medications
                # More children -> more pediatric medications
                if age_distribution["0-14"] > 0.38:  # Higher than average children
                    if atc_code in ["N02BE/B", "R06"]:  # Pediatric-common meds
                        base_demand *= 1.15
                
                # More elderly -> more chronic disease medications
                if age_distribution["65+"] > 0.035:  # Higher than average elderly
                    if atc_code in ["M01AB", "M01AE", "N05C"]:  # Elderly-common meds
                        base_demand *= 1.1
                
                # Create artificial trends if requested
                if include_trends:
                    # Create some drugs with increasing or decreasing trends
                    trend_factor = random.choice([0.95, 0.98, 1.0, 1.0, 1.0, 1.02, 1.05])
                    base_demand_with_trend = base_demand
                
                # For each date
                for date in date_range:
                    # Apply trend if enabled
                    if include_trends:
                        days_passed = (date - start_date).days
                        base_demand_with_trend = base_demand * (trend_factor ** (days_passed/30))
                        current_base_demand = base_demand_with_trend
                    else:
                        current_base_demand = base_demand
                    
                    # Generate variable factors
                    supply_delay = generate_supply_chain_delay(province, date)
                    price = generate_drug_price(drug_name, date, province)
                    
                    # Promotion probability based on income level
                    promotion_prob = {
                        "higher": 0.4,     # More marketing in wealthy areas
                        "medium": 0.3,
                        "medium-low": 0.25,
                        "lower": 0.2       # Less marketing in poorer areas
                    }[income_level]
                    promotion = np.random.choice([0, 1], p=[1-promotion_prob, promotion_prob])
                    
                    effectiveness = drug_data["effectiveness"]
                    time_on_market = drug_data["time_on_market"]
                    competitors = np.random.randint(2, 8)
                    
                    # Calculate availability score
                    availability_score = round({
                        "None": np.random.uniform(0.9, 1.0),
                        "Low": np.random.uniform(0.7, 0.9),
                        "Medium": np.random.uniform(0.5, 0.7),
                        "High": np.random.uniform(0.3, 0.5)
                    }[supply_delay], 2)
                    
                    # Calculate units sold
                    units_sold = calculate_units_sold(
                        current_base_demand, date, atc_code, drug_name, 
                        price, province, health_center, supply_delay, promotion
                    )
                    
                    # Generate realistic timestamps
                    stock_entry_timestamp = date - timedelta(days=random.randint(5, 30))
                    expiration_date = date + timedelta(days=random.randint(30, drug_data["shelf_life"]*30))
                    
                    # Available stock adjusted by center type and region
                    base_stock_buffer = {
                        "referral_hospital": random.randint(100, 300),
                        "district_hospital": random.randint(50, 150),
                        "health_center": random.randint(10, 100)
                    }[center_type]
                    
                    # Remote areas keep more stock to account for supply chain issues
                    if population_density == "low":
                        base_stock_buffer = int(base_stock_buffer * 1.3)
                    
                    available_stock = units_sold + base_stock_buffer
                    
                    # Create sale timestamp at a realistic hour (7AM to 9PM)
                    sale_hour = random.randint(7, 21)
                    sale_timestamp = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=sale_hour, minutes=random.randint(0, 59))
                    
                    rows.append({
                        "Drug_ID": drug_name,
                        "ATC_Code": atc_code,
                        "Date": date,
                        "Province": province,
                        "Population_Density": population_density,
                        "Income_Level": income_level,
                        "Health_Center": health_center,
                        "Center_Type": center_type,
                        "units_sold": units_sold,
                        "Price_Per_Unit": price,
                        "Availability_Score": availability_score,
                        "Supply_Chain_Delay": supply_delay,
                        "Season": get_rwanda_season(date.month),
                        "Effectiveness_Rating": effectiveness,
                        "Promotion": promotion,
                        "Holiday_Week": is_holiday_or_near(date),
                        "Disease_Outbreak": round(is_during_outbreak(date, atc_code), 2),
                        "Competitor_Count": competitors,
                        "Time_On_Market": time_on_market,
                        "sale_timestamp": sale_timestamp,
                        "stock_entry_timestamp": stock_entry_timestamp,
                        "expiration_date": expiration_date,
                        "available_stock": available_stock
                    })
    
    logger.info(f"Generated {len(rows)} data points")
    return pd.DataFrame(rows)

@app.route("/api/synthetic_sales", methods=["GET"])
def synthetic_sales():
    """API endpoint to generate synthetic sales data."""
    try:
        # Get parameters from request
        start_date_str = request.args.get('start_date', '2024-01-01')
        end_date_str = request.args.get('end_date', '2024-12-31')
        include_trends = request.args.get('include_trends', 'true').lower() == 'true'
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # Generate data
        df = generate_dataset(start_date, end_date, include_trends)
        
        # Save to CSV
        csv_filename = "synthetic_pharma_sales.csv"
        df.to_csv(csv_filename, index=False)
        
        return jsonify({
            "message": "Dataset generated successfully!",
            "row_count": len(df),
            "start_date": start_date_str,
            "end_date": end_date_str,
            "file_saved": csv_filename
        })
    
    except Exception as e:
        logger.error(f"Error generating synthetic sales: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/download_csv", methods=["GET"])
def download_csv():
    """API endpoint to download the generated CSV file."""
    try:
        file_path = "synthetic_pharma_sales.csv"
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            logger.error("CSV file not found")
            return jsonify({"error": "File not found!"}), 404
    except Exception as e:
        logger.error(f"Error downloading CSV: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate_sample", methods=["GET"])
def generate_sample():
    """Generate a small sample dataset for testing."""
    try:
        # Generate one week of data
        sample_start = datetime(2024, 1, 1)
        sample_end = datetime(2024, 1, 7)
        
        df = generate_dataset(sample_start, sample_end)
        
        return jsonify({
            "message": "Sample dataset generated successfully!",
            "row_count": len(df),
            "sample_data": df.head(50).to_dict(orient='records')
        })
    
    except Exception as e:
        logger.error(f"Error generating sample: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True,port=5001)
