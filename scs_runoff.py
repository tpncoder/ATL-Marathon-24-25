import math

def calculate_scs_runoff(mean_precipitation, curve_number):
    """
    Calculate runoff using the SCS Curve Number method.

    Args:
        mean_precipitation (float): Total precipitation (P) in mm.
        curve_number (float): Curve Number (CN).

    Returns:
        float: Runoff (Q) in mm.
    """
    if curve_number < 0 or curve_number > 100:
        raise ValueError("Curve Number (CN) must be between 0 and 100.")

    # Compute S
    S = (25400 / curve_number) - 254  # Potential maximum retention (mm)
    
    # Compute initial abstraction (Ia)
    I_a = 0.2 * S  # Initial abstraction (mm)

    # Calculate runoff (Q)
    if mean_precipitation <= I_a:
        return 0  # No runoff occurs
    else:
        Q = ((mean_precipitation - I_a) ** 2) / (mean_precipitation - I_a + S)
        return round(Q, 2)
