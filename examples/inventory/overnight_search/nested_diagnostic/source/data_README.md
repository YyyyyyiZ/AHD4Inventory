# Benchmark data

The assortment experiments run on the **Guo et al. (2026) hard-instance benchmark**. The data
(~61 MB) is not committed to this repository.

## Setup

Download the `hard_data/` directory from the **GitHub release** of the benchmark:

    github.com/wch444/Assortment-Benchmark

and place it at `assortment/data/hard_data/` (or point the `ASSORT_DATA` environment variable
at it). The loaders expect the files

    mmnl_card_RS2_data.json        mmnl_unconstrained_RS2_data.json
    mmnl_card_RS4_data.json        mmnl_unconstrained_RS4_data.json
    nl_card_01_data.json           nl_unconstrained_01_data.json
    nl_card_34_data.json           nl_unconstrained_34_data.json

⚠ Use the GitHub release only. The earlier anonymized copy (anonymous.4open.science) ships 27
MMNL instances whose stated `max_rev` is unattainable by any assortment (verified with the exact
block-enumeration solver in `exact2d.py`); those values are corrected upstream, and this repo
does not support the anonymized copy.

## Constrained pools

The constrained-MMNL family is generated from the MMNL data by `build_constrained.py` (their
constraint generator at the paper's published spec) and saved to `data/constrained/`. Build it
once after fetching the data:

    python build_constrained.py
