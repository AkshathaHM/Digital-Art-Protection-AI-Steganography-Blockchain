# ML model

VGG16 training and inference module for classifying uploaded artwork as human-created or AI-generated.

## Dataset layout

Place labeled images in this structure:

```text
data/
	train/
		Human/
		AI/
	validation/
		Human/
		AI/
```

## Train

From `ml_model/`:

```powershell
python -m pip install -r requirements.txt
python -m training.train --data-dir data --output vgg16_ai_detector.h5 --epochs 10
```

The classifier uses ImageNet VGG16 weights, fine-tunes the last four convolutional layers, and adds global pooling plus dense classification layers. The default output path is `ml_model/vgg16_ai_detector.h5`, which matches the backend `MODEL_PATH` default.

## Inference

```python
from inference import predict_image

label = predict_image('artwork.png', 'vgg16_ai_detector.h5')
# label is exactly "AI" or "Human"
```

Model artifacts are excluded from version control by the repository `.gitignore`.
