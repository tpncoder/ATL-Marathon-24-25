import ee
from rainfall import get_rainfall_data
from scs_runoff import calculate_scs_runoff

# Initialize Earth Engine
ee.Authenticate()
ee.Initialize(project="ee-floodbuddy")

latitude = 37.7749
longitude = -122.4194
radius = 50000

# Define region
region = ee.Geometry.Point([longitude, latitude]).buffer(radius)

# Processing DEM data
print("Processing DEM data...")
dem = ee.Image("USGS/SRTMGL1_003").clip(region)
slope = ee.Terrain.slope(dem).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=region,
    scale=30,
    maxPixels=1e9
).getInfo().get("slope", 0)

print(f"Mean Slope: {slope} degrees")

# Fetching soil data
print("Fetching soil data...")
soil_data = ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02").clip(region)
soil_texture = soil_data.reduceRegion(
    reducer=ee.Reducer.mode(),
    geometry=region,
    scale=250,
    maxPixels=1e9
).getInfo().get("b0", None)

print(f"Soil Texture: {soil_texture}")

# Fetching vegetation data
print("Fetching vegetation data...")
vegetation = ee.ImageCollection("MODIS/061/MOD13A1").filterDate("2022-01-01", "2022-12-31").mean().select("NDVI").clip(region)
ndvi = vegetation.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=region,
    scale=250,
    maxPixels=1e9
).getInfo().get("NDVI", 0)

print(f"Mean NDVI: {ndvi}")

# Fetching historical rainfall data
print("Fetching historical rainfall data...")
rainfall_data = get_rainfall_data(latitude, longitude, radius, "2022-01-01", "2022-12-31")
mean_precipitation = rainfall_data.get("precipitation", 0)
print(f"Mean Precipitation: {mean_precipitation} mm")

# Estimate Curve Number (CN)
# Adjust the curve number dynamically using slope, soil, and NDVI
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
    curve_number = 75  # Default value

# Calculate SCS runoff
runoff = calculate_scs_runoff(mean_precipitation, curve_number)
print(f"Runoff using SCS Curve Number method: {runoff} mm")

# Fetch historical runoff data
print("Fetching historical runoff data...")
runoff_dataset = "NASA/GLDAS/V021/NOAH/G025/T3H"  # Verify this path in Earth Engine catalog
try:
    runoff_data = ee.ImageCollection(runoff_dataset).filterDate("2022-01-01", "2022-12-31").select("Qs_acc").mean()
    historical_runoff = runoff_data.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9
    ).getInfo().get("Qs_acc", None)

    if historical_runoff is not None:
        historical_runoff_mm = historical_runoff * 1000  # Convert from meters to mm
        print(f"Historical Runoff (mm): {historical_runoff_mm}")
    else:
        print("No historical runoff data found.")
except ee.ee_exception.EEException as e:
    print(f"Error fetching historical runoff data: {e}")
    historical_runoff_mm = None

# Compare results if historical data is available
if historical_runoff_mm is not None:
    difference = runoff - historical_runoff_mm
    print(f"Difference between SCS Runoff and Historical Runoff: {difference} mm")
else:
    print("Comparison skipped due to missing historical runoff data.")
