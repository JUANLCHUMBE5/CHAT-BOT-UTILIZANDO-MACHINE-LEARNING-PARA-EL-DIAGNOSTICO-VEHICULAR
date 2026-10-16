"""Escenarios sintéticos; nunca representan observaciones oficiales de tesis."""
SCENARIOS = {
    'yaris': {
        'plate': 'ABC123', 'sender': '51970000001', 'phone': 'E2E_PHONE_A',
        'vehicle': 'Toyota Yaris',
        'turns': [
            'Toyota Yaris 2019 motor 1.5 gasolina. Demora cinco segundos en arrancar en frío.',
            'No pierde potencia después de arrancar. El escáner reporta P0301.',
            'Medí compresión de 180 psi parejo en los cuatro cilindros.',
            'La bobina 1 fue intercambiada con la 2 y el P0301 no se movió.',
            'Consulta la memoria registrada. No generes otro diagnóstico.',
        ],
        'expected': ['P0301', '180', 'bobina'],
    },
    'sentra': {
        'plate': 'XYZ789', 'sender': '51970000002', 'phone': 'E2E_PHONE_B',
        'vehicle': 'Nissan Sentra',
        'turns': [
            'Nissan Sentra 2018 motor 1.8 gasolina. Vibra al frenar a 80 km/h.',
            'No vibra al acelerar. El pedal de freno también vibra.',
            'Medí alabeo del disco delantero derecho: 0.12 mm.',
            'No tengo escáner. Las pastillas fueron inspeccionadas, no están descartadas.',
            'Consulta la memoria registrada. No generes otro diagnóstico.',
        ],
        'expected': ['0.12', 'freno', 'pastillas'],
    },
}
