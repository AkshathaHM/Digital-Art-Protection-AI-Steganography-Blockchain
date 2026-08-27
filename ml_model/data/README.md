# Detector dataset

Add image files to the four class directories:

```text
data/
  train/
    Human/
    AI/
  validation/
    Human/
    AI/
```

Use only images whose labels are known. Keep validation images separate from training images and aim for a balanced number of `Human` and `AI` examples in each split. Do not commit artwork or trained model files to the repository.

Recommended starting point:

- 80% of each class in `train/`
- 20% of each class in `validation/`
- At least several hundred varied images per class for a useful fine-tune
