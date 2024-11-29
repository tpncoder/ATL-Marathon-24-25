import ee

def get_rainfall_data(latitude, longitude, radius, start_date, end_date):
    """
    Fetch precipitation data for a specific date range and region.

    Args:
        latitude (float): Latitude of the region's center.
        longitude (float): Longitude of the region's center.
        radius (float): Radius (in meters) around the point.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        dict: Statistics of precipitation (total and mean) in mm.
    """
    # Define the region of interest
    region = ee.Geometry.Point([longitude, latitude]).buffer(radius)

    # Use GPM IMERG dataset (global precipitation data)
    precipitation_dataset = ee.ImageCollection("NASA/GPM_L3/IMERG_V07").filterDate(start_date, end_date)

    # Compute total precipitation over the period
    total_precipitation = precipitation_dataset.select("precipitation").sum().clip(region)

    # Calculate total and mean precipitation in the region
    stats = total_precipitation.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            ee.Reducer.sum(), sharedInputs=True
        ),
        geometry=region,
        scale=1000,
        maxPixels=1e9
    ).getInfo()

    # Return total and mean precipitation
    return {
        "total_precipitation": stats.get("precipitation_sum", None),
        "mean_precipitation": stats.get("precipitation_mean", None)
    }
