from pathlib import Path
from functools import lru_cache
from typing import Optional

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / 'vgg16_ai_detector.h5'


@lru_cache(maxsize=4)
def _load_model(model_path: Path):
    try:
        from tensorflow.keras.models import load_model
    except ImportError as error:
        raise RuntimeError('TensorFlow is required for image prediction') from error
    if not model_path.exists():
        raise FileNotFoundError(f'Model file does not exist: {model_path}')
    return load_model(model_path, compile=False)


def warm_model(model_path: Optional[str | Path] = None) -> None:
    """Load the detector once so the first classification request is fast."""
    _load_model(Path(model_path) if model_path else DEFAULT_MODEL_PATH)


def predict_image(image_path: str | Path, model_path: Optional[str | Path] = None) -> str:
    """Classify an image as ``AI`` or ``Human`` using the saved VGG16 model."""
    try:
        from tensorflow.keras.utils import img_to_array, load_img
    except ImportError as error:
        raise RuntimeError('TensorFlow is required for image prediction') from error

    image_file = Path(image_path)
    model_file = Path(model_path) if model_path else DEFAULT_MODEL_PATH
    image = load_img(image_file, target_size=(224, 224))
    image_array = img_to_array(image) / 255.0
    prediction = _load_model(model_file)(image_array[None, ...], training=False).numpy()
    ai_probability = float(prediction.reshape(-1)[0])
    return 'AI' if ai_probability >= 0.5 else 'Human'
