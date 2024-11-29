def calculate_scs_runoff(precipitation, curve_number):
    """
    Calculate runoff using the SCS Curve Number method.

    Args:
        precipitation (float): Precipitation in mm.
        curve_number (float): Curve number (50-98 range).

    Returns:
        float: Runoff in mm.
    """
    # Potential maximum retention
    s = 25400 / curve_number - 254

    # Initial abstraction (adjusted)
    ia = 0.02 * s

    # Debugging: print intermediate values
    print(f"Precipitation (P): {precipitation:.2f} mm")
    print(f"Curve Number (CN): {curve_number:.2f}")
    print(f"Potential Maximum Retention (S): {s:.2f} mm")
    print(f"Initial Abstraction (Ia): {ia:.2f} mm")

    # Calculate runoff
    if precipitation > ia:
        runoff = ((precipitation - ia) ** 2) / (precipitation + 0.8 * s)
    else:
        runoff = 0

    # Debugging: print runoff
    print(f"Runoff (Q): {runoff:.2f} mm")
    return runoff
