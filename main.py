import ee
import matplotlib.pyplot as plt
from rainfall import get_rainfall_data
from scs_runoff import calculate_scs_runoff

# Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project="ee-floodbuddy")

# Define parameters
latitude = 37.7749
longitude = -122.4194
radius = 50000  # 50 km
start_date, end_date = "2022-06-01", "2022-06-30"  # Example: June 2022

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
vegetation = (
    ee.ImageCollection("MODIS/061/MOD13A1")
    .filterDate(start_date, end_date)
    .mean()
    .select("NDVI")
    .clip(region)
    .multiply(0.0001)
    .clamp(-1, 1)
)

ndvi = vegetation.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=region,
    scale=250,
    maxPixels=1e9
).getInfo().get("NDVI", 0)

print("Fetching historical rainfall data...")
rainfall_data = get_rainfall_data(latitude, longitude, radius, start_date, end_date)
total_precipitation = rainfall_data.get("total_precipitation", 0)
mean_precipitation = rainfall_data.get("mean_precipitation", 0)

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

# Fetch historical runoff data
print("Fetching historical runoff data...")
runoff_dataset = "NASA/GLDAS/V021/NOAH/G025/T3H"  # Check EE catalog for accuracy
try:
    runoff_data = ee.ImageCollection(runoff_dataset).filterDate(start_date, end_date).select("Qs_acc").mean()
    historical_runoff = runoff_data.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9
    ).getInfo().get("Qs_acc", None)

    historical_runoff_mm = historical_runoff * 1000 if historical_runoff else None
except ee.ee_exception.EEException as e:
    print(f"Error fetching historical runoff data: {e}")
    historical_runoff_mm = None

# Print predicted runoff
print(f"Predicted Runoff: {runoff_predicted:.2f} mm")
print(f"Historical Runoff: {historical_runoff_mm:.2f}" if historical_runoff_mm else "No historical runoff data available")

# Plotting the chart
factors = ["Slope (°)", "NDVI", "Soil Texture", "Precipitation (mm)", "Runoff (mm)"]
values = [slope, ndvi, soil_texture or 0, mean_precipitation, runoff_predicted]

plt.figure(figsize=(10, 6))
plt.bar(factors, values, color=["blue", "green", "brown", "cyan", "orange"])
plt.title("Factors and Predicted Runoff")
plt.ylabel("Values")
plt.xlabel("Factors")
plt.show()
