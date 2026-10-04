"""Export the complete fixed screening grid; never draw a final-test demand."""
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np

from .perishable import _aer_components, inventory_cap, scenarios as primary_scenarios
from .extended import scenarios as extended_scenarios

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "output/overnight_search/20260917"


def main():
    records = []
    for profile, grid in (("primary", primary_scenarios()), ("extended", extended_scenarios())):
        for scenario in grid:
            streams = {}
            for label, share in (("FIFO", scenario.f), ("LIFO", 1-scenario.f)):
                components = _aer_components(share*scenario.mean, np.sqrt(share)*scenario.sd)
                streams[label] = dict(mean=share*scenario.mean, variance=share*scenario.sd**2,
                    law="point_mass_at_zero" if share == 0 else "mixture_of_two_geometric_distributions_on_nonnegative_integers",
                    components=[dict(weight=float(weight), success_probability=None if dist is None else float(dist.args[1]))
                                for weight, dist in components])
            records.append(dict(profile=profile, params=asdict(scenario), inventory_position_cap=inventory_cap(scenario),
                numeric_structure_feedback=scenario.m in (3, 5, 7),
                baek_known_public_class=True, independent_demand_streams=streams))
    target = RUN / "instances"
    target.mkdir(parents=True, exist_ok=True)
    result = dict(purpose="All 20 prespecified/exploratory screening instances, including unfavorable outcomes; not a list of demonstrated wins.",
        count=len(records), source_sha256=hashlib.sha256(Path(__file__).with_name("perishable.py").read_bytes()).hexdigest(),
        demand_independence="FIFO and LIFO independent of one another and iid across periods.",
        cap_definition="Median of total demand over m+L periods, paper-text convention.",
        dynamics="At decision, today's arrival is already present. Order arrives after L periods. Serve FIFO oldest first, then LIFO freshest first; expire oldest residual stock, age survivors, receive next period's delivery.",
        action_projection="Clip real action to [0,cap-sum(age)-sum(pipeline)], then round half to even.",
        cost="p*lost_units + w*expired_units + h*surviving_units each period; no terminal charge or salvage.",
        literature_caveat="Actual CV and m+L cap follow paper text; published DynaPlex-legacy code uses a different dispersion and m+L+1 cap convention. This is not a numerical reproduction of its published table.",
        instances=records)
    (target / "all_20_instances.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    fields=['profile','name','m','L','mean','cv','f','h','p','w','inventory_position_cap','numeric_structure_feedback']
    with (target / "all_20_instances.csv").open('w', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({key:(row['params'][key] if key in row['params'] else row[key]) for key in fields})
    print(json.dumps(dict(count=len(records), directory=str(target), final_test_generated=False)))


if __name__ == '__main__':
    main()
