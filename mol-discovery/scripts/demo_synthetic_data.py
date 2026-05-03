#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

def generate_catalysts(n=200):
    families = ['ZSM5-Ga', 'ZSM5-Al', 'TiO2', 'ZrO2', 'Zeolite']
    data = []
    
    for family in families:
        n_family = 40
        si_al = np.random.uniform(10, 100, n_family)
        
        if 'Ga' in family:
            activity = 3.2 + 0.01 * si_al - 0.002 * si_al**2  # optimum at Si/Al~25
            selectivity = 0.92 - 0.001 * np.abs(si_al - 25)
        elif 'Al' in family:
            activity = 2.8 + 0.008 * si_al
            selectivity = 0.85
        else:
            activity = np.random.uniform(1.5, 2.5, n_family)
            selectivity = np.random.uniform(0.7, 0.9, n_family)
        
        for i in range(n_family):
            data.append({
                'family': family,
                'smiles': f"{family}_SiAl{int(si_al[i])}",
                'si_al_ratio': si_al[i],
                'activity': max(0, activity[i] + np.random.normal(0, 0.2)),
                'selectivity': max(0, min(1, selectivity[i] + np.random.normal(0, 0.05))),
                'stability': np.random.uniform(24, 72)
            })
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    catalysts = generate_catalysts()
    experiments = catalysts.sample(50).copy()
    experiments['experiment_date'] = pd.date_range('2024-01-01', periods=50)
    
    Path("data").mkdir(exist_ok=True)
    catalysts.to_csv("data/catalysts.csv", index=False)
    experiments.to_csv("data/experiments.csv", index=False)
    
    print("✅ Generated synthetic ethanol-to-jet dataset:")
    print(f"  Catalysts: {len(catalysts)} (trend: Ga-ZSM5 optimal @ Si/Al=25)")
    print(f"  Experiments: {len(experiments)}")
    print(catalysts.head())

