from __future__ import annotations

from typing import Union

from PIL import Image

ImageInput = Union[Image.Image, str]


def compute_phash(image: ImageInput) -> str:
    """Return a stable hexadecimal perceptual hash for an image."""
    try:
        import imagehash
    except ImportError:
        import cv2
        import numpy as np

        source = Image.open(image) if isinstance(image, str) else image
        grayscale = np.asarray(source.convert('L').resize((32, 32)), dtype=np.float32)
        coefficients = cv2.dct(grayscale)[:8, :8]
        threshold = np.median(coefficients[1:, :])
        bits = (coefficients >= threshold).flatten()
        return f'{sum((1 << index) for index, bit in enumerate(bits) if bit):016x}'
    return str(imagehash.phash(Image.open(image) if isinstance(image, str) else image))


def phash_distance(first_hash: str, second_hash: str) -> int:
    """Return the Hamming distance between two hexadecimal pHash values."""
    return (int(first_hash, 16) ^ int(second_hash, 16)).bit_count()


def is_near_duplicate(first_hash: str, second_hash: str, threshold: int = 8) -> bool:
    """Return true when two pHashes are within the configured Hamming distance."""
    if threshold < 0:
        raise ValueError('threshold must be non-negative')
    return phash_distance(first_hash, second_hash) <= threshold
