"""Shared feature contract. Bounds validate inputs, not drinking-water safety."""
FEATURES = {
    'ph': ('pH', 'pH units', 0, 14, 7.1),
    'Hardness': ('Hardness', 'mg/L', 0, 1000, 196),
    'Solids': ('Dissolved solids', 'ppm', 0, 100000, 22000),
    'Chloramines': ('Chloramines', 'ppm', 0, 50, 7.1),
    'Sulfate': ('Sulfate', 'mg/L', 0, 2000, 333),
    'Conductivity': ('Conductivity', 'µS/cm', 0, 5000, 426),
    'Organic_carbon': ('Organic carbon', 'mg/L', 0, 100, 14.3),
    'Trihalomethanes': ('Trihalomethanes', 'µg/L', 0, 1000, 66),
    'Turbidity': ('Turbidity', 'NTU', 0, 100, 4),
}
