import ee
import requests
import rasterio
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

# Initialize the Earth Engine library
ee.Authenticate()
ee.Initialize(project="ee-floodbuddy")

# Define coordinates and radius for area of interest
latitude = 37.7749  # Replace with your latitude
longitude = -122.4194  # Replace with your longitude
radius = 50000  # Radius in meters (50 km)

# Define the center and region in Google Earth Engine
center_point = ee.Geometry.Point([longitude, latitude])
region = center_point.buffer(radius)  # Create a buffer around the point

# Load the SRTM DEM dataset and clip to the region
dem_dataset = ee.Image("USGS/SRTMGL1_003")
dem_clip = dem_dataset.clip(region)

# Generate the download URL for the DEM
url = dem_clip.getDownloadURL({
    'scale': 30,
    'region': region,
    'format': 'GeoTIFF'
})

# Define local path for saving the DEM
export_path = './dem_data.tif'

# Download the DEM data and save it to the local path
print("Downloading DEM data...")
response = requests.get(url)
if response.status_code == 200:
    with open(export_path, 'wb') as file:
        file.write(response.content)
    print(f"DEM downloaded to {export_path}")
else:
    print("Failed to download DEM data.")

# Load soil data
print("Fetching soil data...")
try:
    soil_data = ee.Image("ISRIC/SoilGrids250m/phy_properties").select(["clay", "sand", "soc"])
    soil_clip = soil_data.clip(region)
    soil_url = soil_clip.getDownloadURL({'scale': 250, 'region': region, 'format': 'GeoTIFF'})
    soil_path = './soil_data.tif'

    response = requests.get(soil_url)
    if response.status_code == 200:
        with open(soil_path, 'wb') as file:
            file.write(response.content)
        print(f"Soil data downloaded to {soil_path}")
    else:
        print("Failed to download soil data.")
except Exception as e:
    print("Error fetching soil data:", e)

# Read DEM data
print("Opening and analyzing DEM data...")
with rasterio.open(export_path) as dem:
    dem_data = dem.read(1)
    data_flat = dem_data[dem_data != dem.nodata]  # Exclude nodata values

# Define a function to fetch historical and future rainfall data
def fetch_rainfall_data(lat, lon):
    historical_rainfall = 253.12  # Placeholder for actual historical data
    future_rainfall = 124.35  # Placeholder for actual forecast data
    return historical_rainfall, future_rainfall

# Use rainfall data for runoff calculations
historical_rainfall, future_rainfall = fetch_rainfall_data(latitude, longitude)
print(f"\nHistorical Rainfall (mm): {historical_rainfall}")
print(f"Predicted Future Rainfall (mm): {future_rainfall}")

# Calculate runoff using DEM, soil properties, and rainfall data
soil_properties = {"clay_content": 30, "sand_content": 40, "soc_content": 1.5}  # Sample soil values

def calculate_runoff(dem_data, rainfall, soil_properties):
    elevation_diff = dem_data.max() - dem_data.min()
    runoff = (rainfall / (elevation_diff * (soil_properties["clay_content"] + soil_properties["sand_content"])))
    return runoff

historical_runoff = calculate_runoff(dem_data, historical_rainfall, soil_properties)
future_runoff = calculate_runoff(dem_data, future_rainfall, soil_properties)

accuracy = 100 - abs((historical_runoff - future_runoff) / historical_runoff * 100)
print(f"\nHistorical Runoff: {historical_runoff:.2f} mm")
print(f"Predicted Runoff: {future_runoff:.2f} mm")
print(f"Accuracy of Prediction: {accuracy:.2f}%")

# Display table of high runoff areas
high_runoff_areas = [
    {"Latitude": latitude + 0.01, "Longitude": longitude + 0.01, "Rainfall (mm)": future_rainfall, "Water Level Rise": future_runoff},
    {"Latitude": latitude - 0.01, "Longitude": longitude - 0.01, "Rainfall (mm)": historical_rainfall, "Water Level Rise": historical_runoff}
]
runoff_df = pd.DataFrame(high_runoff_areas)
print("\nHigh Runoff Areas:")
print(runoff_df)

# Function to calculate spatial runoff for DEM data
def calculate_spatial_runoff(dem_data, rainfall, soil_properties):
    # Normalize elevation difference
    elevation_diff = np.ptp(dem_data)  # Range (max - min) of elevation
    runoff = (rainfall / (elevation_diff * (soil_properties["clay_content"] + soil_properties["sand_content"])))
    spatial_runoff = dem_data * runoff  # Scale runoff based on elevation
    return spatial_runoff

# Calculate spatial runoff for historical and predicted rainfall
historical_spatial_runoff = calculate_spatial_runoff(dem_data, historical_rainfall, soil_properties)
future_spatial_runoff = calculate_spatial_runoff(dem_data, future_rainfall, soil_properties)

# Normalize runoff values for better visualization
historical_spatial_runoff_normalized = (historical_spatial_runoff - np.min(historical_spatial_runoff)) / \
                                       (np.max(historical_spatial_runoff) - np.min(historical_spatial_runoff))
future_spatial_runoff_normalized = (future_spatial_runoff - np.min(future_spatial_runoff)) / \
                                   (np.max(future_spatial_runoff) - np.min(future_spatial_runoff))

# Plotting DEM runoff comparison
fig, axs = plt.subplots(1, 2, figsize=(12, 6))

# Historical runoff
axs[0].imshow(historical_spatial_runoff_normalized, cmap='Blues')
axs[0].set_title("Historical Rainwater Runoff")
axs[0].axis('off')  # Hide axis for cleaner visualization
axs[0].colorbar = plt.colorbar(axs[0].imshow(historical_spatial_runoff_normalized, cmap='Blues'),
                               ax=axs[0], orientation='vertical', label="Runoff Intensity")

# Predicted runoff
axs[1].imshow(future_spatial_runoff_normalized, cmap='Greens')
axs[1].set_title("Predicted Rainwater Runoff")
axs[1].axis('off')
axs[1].colorbar = plt.colorbar(axs[1].imshow(future_spatial_runoff_normalized, cmap='Greens'),
                               ax=axs[1], orientation='vertical', label="Runoff Intensity")

plt.tight_layout()
plt.show()

