import ee

# Initialize and authenticate Earth Engine
ee.Initialize(project="ee-floodbuddy")

def get_rainfall_data(latitude, longitude, radius, start_date, end_date):
    """
    Fetches total rainfall data over a period for a specific region.
    """
    point = ee.Geometry.Point([longitude, latitude])
    region = point.buffer(radius)
    
    # Use CHIRPS dataset for historical data
    dataset = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") \
               .filterBounds(region) \
               .filterDate(start_date, end_date)
    
    # Sum the daily rainfall over the selected period
    rainfall_image = dataset.sum()
    rainfall = rainfall_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=500
    ).getInfo()

    return rainfall['precipitation']
