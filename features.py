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

# Preset samples for the interface: rounded dataset rows, shown as quick-start
# buttons below the form. Illustrative measurements, not verified samples.
SAMPLES = (
    {
        'name': 'Near-median sample',
        'note': 'Typical dataset values across all nine fields.',
        'drinkable': False,
        'measurements': {
            'ph': 7.1,
            'Hardness': 196,
            'Solids': 22000,
            'Chloramines': 7.1,
            'Sulfate': 333,
            'Conductivity': 426,
            'Organic_carbon': 14.3,
            'Trihalomethanes': 66,
            'Turbidity': 4,
        },
    },
    {
        'name': 'Low-solids sample',
        'note': 'Dissolved solids far below the dataset median.',
        'drinkable': True,
        'measurements': {
            'ph': 6.19,
            'Hardness': 236.03,
            'Solids': 1198.94,
            'Chloramines': 6.14,
            'Sulfate': 374.1,
            'Conductivity': 436.24,
            'Organic_carbon': 11.09,
            'Trihalomethanes': 99.78,
            'Turbidity': 4.09,
        },
    },
    {
        'name': 'High-chloramines sample',
        'note': 'Elevated chloramines with higher dissolved solids.',
        'drinkable': False,
        'measurements': {
            'ph': 6.14,
            'Hardness': 175.27,
            'Solids': 29072.17,
            'Chloramines': 12.06,
            'Sulfate': 287.7,
            'Conductivity': 469.98,
            'Organic_carbon': 13.14,
            'Trihalomethanes': 83.28,
            'Turbidity': 3.48,
        },
    },
)
