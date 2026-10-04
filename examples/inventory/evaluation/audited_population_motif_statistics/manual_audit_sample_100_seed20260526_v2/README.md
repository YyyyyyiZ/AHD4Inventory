# Manual motif audit sample

- Source label file: `examples/inventory/evaluation/audited_population_motif_statistics/audited_population_policy_motif_labels.csv`
- Sampling frame: all population policy records (`n=11574`)
- Sample size: 100
- Random seed: 20260526
- `sample_100_policy_motif_labels.csv` contains table motifs, extra motifs, top10/final membership, and blank manual review columns.
- `policies/` contains the full sampled policy code with metadata comments.
- `source_candidate_count_for_folder_generation` is included because some folder names may appear under nested directories; value 1 means unambiguous source lookup.
