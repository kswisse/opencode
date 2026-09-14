"""Rothfusz heat index calculation (Steadman 1979)."""
import numpy as np

def compute_heat_index(temp_c: float, humidity: float) -> float:
    t_f = temp_c * 9 / 5 + 32
    hi_f = (
        -42.379 + 2.04901523 * t_f + 10.14333127 * humidity
        - 0.22475541 * t_f * humidity - 6.83783e-3 * t_f**2
        - 5.481717e-2 * humidity**2 + 1.22874e-3 * t_f**2 * humidity
        + 8.5282e-4 * t_f * humidity**2 - 1.99e-6 * t_f**2 * humidity**2
    )
    if humidity < 13 and 80 <= t_f <= 112:
        adjustment = -((13 - humidity) / 4) * np.sqrt((17 - abs(t_f - 95)) / 17)
        hi_f += adjustment
    if humidity > 85 and 80 <= t_f <= 87:
        adjustment = ((humidity - 85) / 10) * ((87 - t_f) / 5)
        hi_f += adjustment
    hi_c = (hi_f - 32) * 5 / 9
    return round(hi_c, 2)
