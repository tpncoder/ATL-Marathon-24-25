import ee

def get_rainfall_data(latitude, longitude, radius, start_date, end_date):
    """
    Fetch historical rainfall data for a specific region.

    Args:
        latitude (float): Latitude of the center point.
        longitude (float): Longitude of the center point.
        radius (int): Radius of the area in meters.
        start_date (str): Start date in the format "YYYY-MM-DD".
        end_date (str): End date in the format "YYYY-MM-DD".

    Returns:
        dict: Rainfall data statistics.
    """
    region = ee.Geometry.Point([longitude, latitude]).buffer(radius)
    rainfall_dataset = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(start_date, end_date)
    rainfall_image = rainfall_dataset.sum()
    stats = rainfall_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=5000,
        maxPixels=1e9
    ).getInfo()
    return stats
