import requests
import ee
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scs_runoff import calculate_scs_runoff
from coordinates import get_coordinates_from_ip

# Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project="ee-floodbuddy")

latitude, longitude = get_coordinates_from_ip()
radius = 50000  # 50 km
api_key = "9a934c9a643a4edb92a123713243011"

# Define date ranges for vegetation
start_date, end_date = "2024-09-22", "2024-10-01"

today = datetime.now()
one_week_later = today + timedelta(weeks=1)

# Format the dates as strings in the format 'YYYY-MM-DD'
start_date_rainfall = today.strftime('%Y-%m-%d')
end_date_rainfall = one_week_later.strftime('%Y-%m-%d')

# Define region
region = ee.Geometry.Point([longitude, latitude]).buffer(radius)

# Fetch factors and perform calculations
print("Processing DEM data...")
dem = ee.Image("USGS/SRTMGL1_003").clip(region)
slope = ee.Terrain.slope(dem).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=region,
    scale=30,
    maxPixels=1e9
).getInfo().get("slope", 0)

print("Fetching soil data...")
soil_data = ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02").clip(region)
soil_texture = soil_data.reduceRegion(
    reducer=ee.Reducer.mode(),
    geometry=region,
    scale=250,
    maxPixels=1e9
).getInfo().get("b0", None)

print("Fetching vegetation data...")
vegetation_collection = ee.ImageCollection("MODIS/061/MOD13A1").filterDate(start_date, end_date)
if vegetation_collection.size().getInfo() == 0:
    print("No vegetation data available for the selected date range.")
    ndvi = 0  # Default value
else:
    vegetation = vegetation_collection.mean().select("NDVI").clip(region).multiply(0.0001).clamp(-1, 1)
    ndvi = vegetation.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=250,
        maxPixels=1e9
    ).getInfo().get("NDVI", 0)

# Fetch future rainfall prediction data using Weather API
print("Fetching future rainfall prediction data...")
url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=rain"
response = requests.get(url)
print(url)

if response.status_code == 200:
    data = response.json()
    hourly_precipitation = data.get("hourly", {}).get("precipitation", [])
    total_precipitation = sum(hourly_precipitation)
    mean_precipitation = total_precipitation / len(hourly_precipitation) if hourly_precipitation else 0
    print(f"Total Precipitation: {total_precipitation:.2f} mm")
    print(f"Mean Precipitation: {mean_precipitation:.2f} mm")
else:
    print("Error fetching rainfall data.")

# Calculate Curve Number
if soil_texture and ndvi:
    if soil_texture < 5:  # Sandy soils
        curve_number = 65
    elif soil_texture < 7:  # Loamy soils
        curve_number = 75
    else:  # Clayey soils
        curve_number = 85

    if slope > 10:  # Steep slopes
        curve_number += 5
    elif slope < 2:  # Flat terrain
        curve_number -= 5
else:
    curve_number = 75  # Default

curve_number = max(50, min(curve_number, 98))  # Clamp

# Calculate runoff
runoff_predicted = calculate_scs_runoff(mean_precipitation, curve_number)

# Print predicted runoff
print(f"Predicted Runoff (Future): {runoff_predicted:.2f} mm")

# Plotting the chart
factors = ["Slope (°)", "NDVI", "Soil Texture", "Precipitation (mm)", "Runoff (mm)"]
values = [slope, ndvi, soil_texture or 0, mean_precipitation, runoff_predicted]

plt.figure(figsize=(10, 6))
plt.bar(factors, values, color=["blue", "green", "brown", "cyan", "orange"])
plt.title("Factors and Predicted Runoff Based on Future Rainfall")
plt.ylabel("Values")
plt.xlabel("Factors")
plt.show()
