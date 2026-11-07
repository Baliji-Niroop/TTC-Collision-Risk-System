# Synthetic TTC dataset

`synthetic_ttc_validation.csv` contains 610 generated rows across six named scenarios. It is the only checked-in copy of this dataset.

| Scenario | Rows |
|---|---:|
| `safe_cruise` | 100 |
| `slow_closing` | 100 |
| `sudden_braking` | 110 |
| `fast_collision` | 90 |
| `noisy_sensor` | 100 |
| `wet_road_threshold_shift` | 110 |

`ground_truth_risk_class` is produced by TTC threshold rules in `src/synthetic_validation_dataset.py`; it is not a measured collision outcome. The CSV also contains training features and scenario metadata. Those extra columns do not change the frozen seven-field runtime telemetry contract.

Generate the file again from the repository root:

```bash
python src/synthetic_validation_dataset.py
```

Train and evaluate the optional models using whole scenarios for the held-out split:

```bash
python ml/training/train_model.py
python validation/evaluate_synthetic.py
```
