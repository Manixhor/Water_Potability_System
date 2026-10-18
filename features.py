"""Water quality feature contract and interface sample presets.

The per-feature example is also the "Load example" value, and the bounds are
application input limits. Neither is a drinking-water safety standard.
"""
FEATURES = {
    'ph': ('pH', 'pH units', 0, 14, 6.7),
    'Hardness': ('Hardness', 'mg/L', 0, 1000, 182.4),
    'Solids': ('Dissolved solids', 'ppm', 0, 100000, 16828.9),
    'Chloramines': ('Chloramines', 'ppm', 0, 50, 7.1),
    'Sulfate': ('Sulfate', 'mg/L', 0, 2000, 355.9),
    'Conductivity': ('Conductivity', 'µS/cm', 0, 5000, 434.7),
    'Organic_carbon': ('Organic carbon', 'mg/L', 0, 100, 16.6),
    'Trihalomethanes': ('Trihalomethanes', 'µg/L', 0, 1000, 69.4),
    'Turbidity': ('Turbidity', 'NTU', 0, 100, 4.0),
}

# Preset samples for the interface: rounded dataset rows that the served model
# classifies as potable, shown as quick-start buttons below the form. Values are
# illustrative measurements, not verified laboratory samples, and the verdict is
# a model prediction rather than a safety certification. scripts/build_cloudflare.py
# refuses to build if a sample's drinkable flag disagrees with the model.
SAMPLES = (
    {
        'name': 'Balanced sample',
        'note': 'Close to the dataset medians across all nine fields.',
        'drinkable': True,
        'measurements': {
            'ph': 6.7,
            'Hardness': 182.4,
            'Solids': 16828.9,
            'Chloramines': 7.1,
            'Sulfate': 355.9,
            'Conductivity': 434.7,
            'Organic_carbon': 16.6,
            'Trihalomethanes': 69.4,
            'Turbidity': 4.0,
        },
    },
    {
        'name': 'Low-solids sample',
        'note': 'Dissolved solids far below the dataset median.',
        'drinkable': True,
        'measurements': {
            'ph': 6.2,
            'Hardness': 236.0,
            'Solids': 1198.9,
            'Chloramines': 6.1,
            'Sulfate': 374.1,
            'Conductivity': 436.2,
            'Organic_carbon': 11.1,
            'Trihalomethanes': 99.8,
            'Turbidity': 4.1,
        },
    },
    {
        'name': 'Higher-mineral sample',
        'note': 'Harder water with higher dissolved solids.',
        'drinkable': True,
        'measurements': {
            'ph': 6.8,
            'Hardness': 306.6,
            'Solids': 28508.2,
            'Chloramines': 6.8,
            'Sulfate': 293.1,
            'Conductivity': 306.1,
            'Organic_carbon': 9.0,
            'Trihalomethanes': 60.9,
            'Turbidity': 2.5,
        },
    },
)
