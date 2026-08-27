# Steganography

DCT-based watermark embedding and extraction plus perceptual hashing for duplicate detection.

This module is intentionally isolated from the API so watermarking can be tested independently and reused by workers or background jobs.

## Watermarking

```python
from steganography import embed_watermark, extract_watermark

watermarked = embed_watermark(image, 'artist-id:timestamp:artwork-id')
watermarked.save('watermarked.png')
assert extract_watermark(watermarked) == 'artist-id:timestamp:artwork-id'
```

Watermarks are stored in paired mid-frequency DCT coefficients on the luminance channel. The payload includes a format marker, a two-byte length, and UTF-8 content.

The pHash helper prefers `imagehash` and falls back to the same 64-bit DCT strategy using OpenCV and NumPy when that optional package is unavailable.

## Duplicate detection

```python
from steganography import compute_phash, is_near_duplicate

existing = compute_phash('existing.png')
incoming = compute_phash('incoming.png')
duplicate = is_near_duplicate(existing, incoming, threshold=8)
```
