import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


def build_fuzzy_system(grade):
    busuk = ctrl.Antecedent(np.arange(0, 101, 1), 'busuk')
    cacat = ctrl.Antecedent(np.arange(0, 101, 1), 'cacat')
    cuping = ctrl.Antecedent(np.arange(0, 101, 1), 'cuping')

    keputusan = ctrl.Consequent(np.arange(0, 101, 1), 'keputusan')

    # Membership function
    for var in [busuk, cacat, cuping]:
        var['rendah'] = fuzz.trapmf(var.universe, [0, 0, 5, 10])
        var['sedang'] = fuzz.trapmf(var.universe, [8, 15, 25, 35])
        var['tinggi'] = fuzz.trapmf(var.universe, [30, 50, 100, 100])

    keputusan['olahan'] = fuzz.trapmf(keputusan.universe, [0, 0, 20, 40])
    keputusan['ditunda'] = fuzz.trapmf(keputusan.universe, [35, 45, 55, 65])
    keputusan['lokal'] = fuzz.trapmf(keputusan.universe, [60, 70, 80, 90])
    keputusan['ekspor'] = fuzz.trapmf(keputusan.universe, [85, 90, 100, 100])

    rules = []

    # -------- GRADE A --------
    if grade == 'A':
        rules.extend([
            ctrl.Rule(busuk['rendah'] & cacat['rendah'] & cuping['rendah'], keputusan['ekspor']),
            ctrl.Rule(busuk['rendah'] & cacat['sedang'] & cuping['rendah'], keputusan['lokal']),
            ctrl.Rule(busuk['sedang'] & cacat['sedang'], keputusan['lokal']),
            ctrl.Rule(busuk['tinggi'] | cacat['tinggi'] | cuping['tinggi'], keputusan['olahan']),
        ])

    # -------- GRADE B --------
    elif grade == 'B':
        rules.extend([
            ctrl.Rule(busuk['rendah'] & cacat['rendah'] & cuping['rendah'], keputusan['lokal']),
            ctrl.Rule(busuk['sedang'] & cacat['sedang'], keputusan['lokal']),
            ctrl.Rule(busuk['sedang'] | cacat['tinggi'] | cuping['tinggi'], keputusan['olahan']),
            ctrl.Rule(busuk['tinggi'], keputusan['olahan']),
        ])

    # -------- GRADE C --------
    elif grade == 'C':
        rules.extend([
            ctrl.Rule(busuk['rendah'] & cacat['rendah'] & cuping['rendah'], keputusan['ditunda']),
            ctrl.Rule(busuk['sedang'] & cacat['rendah'], keputusan['ditunda']),
            ctrl.Rule(busuk['sedang'] | cacat['sedang'] | cuping['tinggi'], keputusan['olahan']),
            ctrl.Rule(busuk['tinggi'] | cacat['tinggi'], keputusan['olahan']),
        ])

    system_ctrl = ctrl.ControlSystem(rules)
    return ctrl.ControlSystemSimulation(system_ctrl)
