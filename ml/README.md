# Machine Learning

Normalized ML structure.

## Layout
- inference/: runtime-safe inference package
- training/: model training scripts
- models/: model artifacts and metadata
- datasets/: ML dataset references

## Runtime safety
If model loading fails or artifacts are absent, inference falls back to TTC threshold classification.
