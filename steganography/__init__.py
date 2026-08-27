"""DCT watermarking and perceptual hashing utilities."""

from .hashing import compute_phash, is_near_duplicate, phash_distance
from .watermark import embed_watermark, extract_watermark

__all__ = [
	'compute_phash',
	'embed_watermark',
	'extract_watermark',
	'is_near_duplicate',
	'phash_distance',
]
