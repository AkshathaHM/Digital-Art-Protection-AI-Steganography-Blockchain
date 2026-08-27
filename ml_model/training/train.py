import argparse
from pathlib import Path

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def build_model():
    from tensorflow.keras import Model
    from tensorflow.keras.applications import VGG16
    from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D

    base_model = VGG16(weights='imagenet', include_top=False, input_shape=(*IMAGE_SIZE, 3))
    base_model.trainable = True
    for layer in base_model.layers[:-4]:
        layer.trainable = False

    features = GlobalAveragePooling2D()(base_model.output)
    features = Dense(256, activation='relu')(features)
    features = Dropout(0.4)(features)
    output = Dense(1, activation='sigmoid', name='ai_probability')(features)
    return Model(inputs=base_model.input, outputs=output)


def train(data_dir: Path, output_path: Path, epochs: int = 10) -> None:
    train_dir = data_dir / 'train'
    validation_dir = data_dir / 'validation'
    if not train_dir.is_dir() or not validation_dir.is_dir():
        raise FileNotFoundError('Expected data/train and data/validation directories')
    missing_classes = [
        directory for directory in (
            train_dir / 'Human', train_dir / 'AI',
            validation_dir / 'Human', validation_dir / 'AI',
        ) if not directory.is_dir()
    ]
    if missing_classes:
        raise FileNotFoundError(f'Missing dataset class directories: {", ".join(str(path) for path in missing_classes)}')
    empty_classes = [
        directory for directory in (
            train_dir / 'Human', train_dir / 'AI',
            validation_dir / 'Human', validation_dir / 'AI',
        ) if not any(file.suffix.lower() in SUPPORTED_EXTENSIONS for file in directory.iterdir() if file.is_file())
    ]
    if empty_classes:
        raise ValueError(f'Each class directory needs images; empty: {", ".join(str(path) for path in empty_classes)}')

    try:
        from tensorflow.keras.preprocessing.image import ImageDataGenerator
    except ImportError as error:
        raise RuntimeError('TensorFlow is required for training; use a Python environment supported by TensorFlow and install ml_model/requirements.txt') from error

    train_generator = ImageDataGenerator(
        rescale=1 / 255.0,
        rotation_range=12,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
    ).flow_from_directory(
        train_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='binary',
        classes=['Human', 'AI'],
    )
    validation_generator = ImageDataGenerator(rescale=1 / 255.0).flow_from_directory(
        validation_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='binary',
        classes=['Human', 'AI'],
        shuffle=False,
    )

    class_counts = train_generator.classes
    human_count = max(1, (class_counts == 0).sum())
    ai_count = max(1, (class_counts == 1).sum())
    total_count = human_count + ai_count
    class_weight = {
        0: total_count / (2 * human_count),
        1: total_count / (2 * ai_count),
    }

    model = build_model()
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy', 'AUC'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.fit(train_generator, validation_data=validation_generator, epochs=epochs, class_weight=class_weight)
    model.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description='Fine-tune VGG16 for AI-generated artwork detection')
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--output', type=Path, default=Path('vgg16_ai_detector.h5'))
    parser.add_argument('--epochs', type=int, default=10)
    args = parser.parse_args()
    train(args.data_dir, args.output, args.epochs)


if __name__ == '__main__':
    main()
