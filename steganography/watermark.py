from __future__ import annotations

from typing import Union

import cv2
import numpy as np
from PIL import Image

ImageInput = Union[Image.Image, np.ndarray]
_BLOCK_SIZE = 8
_COEFFICIENT_A = (3, 4)
_COEFFICIENT_B = (4, 3)
_STRENGTH = 14.0
_MAGIC = b'DAP1'
_HEADER_BITS = 32 + 16


def _to_rgb_array(image: ImageInput) -> np.ndarray:
    if isinstance(image, Image.Image):
        return np.asarray(image.convert('RGB'), dtype=np.uint8).copy()
    array = np.asarray(image)
    if array.ndim == 2:
        return cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_GRAY2RGB)
    if array.shape[2] == 4:
        return cv2.cvtColor(array.astype(np.uint8), cv2.COLOR_RGBA2RGB)
    return array.astype(np.uint8).copy()


def _bits(payload: bytes) -> list[int]:
    return [(byte >> shift) & 1 for byte in payload for shift in range(7, -1, -1)]


def _bytes(bits: list[int]) -> bytes:
    return bytes(sum(bits[index + offset] << (7 - offset) for offset in range(8)) for index in range(0, len(bits), 8))


def _capacity(array: np.ndarray) -> int:
    height, width = array.shape[:2]
    return (height // _BLOCK_SIZE) * (width // _BLOCK_SIZE)


def _watermark_bits(message: str) -> list[int]:
    payload = message.encode('utf-8')
    if len(payload) > 65535:
        raise ValueError('watermark message must be at most 65535 bytes')
    return _bits(_MAGIC) + _bits(len(payload).to_bytes(2, 'big')) + _bits(payload)


def embed_watermark(image: ImageInput, message: str) -> Image.Image:
    """Embed a UTF-8 ownership message into an image using block DCT coefficients."""
    array = _to_rgb_array(image)
    bits = _watermark_bits(message)
    if len(bits) > _capacity(array):
        raise ValueError('image is too small for this watermark')

    ycrcb = cv2.cvtColor(array, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    luminance = ycrcb[:, :, 0]
    height, width = luminance.shape
    bit_index = 0
    for top in range(0, height - _BLOCK_SIZE + 1, _BLOCK_SIZE):
        for left in range(0, width - _BLOCK_SIZE + 1, _BLOCK_SIZE):
            if bit_index >= len(bits):
                break
            block = luminance[top:top + _BLOCK_SIZE, left:left + _BLOCK_SIZE]
            coefficients = cv2.dct(block)
            first = _COEFFICIENT_A
            second = _COEFFICIENT_B
            average = (coefficients[first] + coefficients[second]) / 2.0
            if bits[bit_index]:
                coefficients[first] = average + _STRENGTH
                coefficients[second] = average - _STRENGTH
            else:
                coefficients[first] = average - _STRENGTH
                coefficients[second] = average + _STRENGTH
            luminance[top:top + _BLOCK_SIZE, left:left + _BLOCK_SIZE] = cv2.idct(coefficients)
            bit_index += 1
        if bit_index >= len(bits):
            break

    ycrcb[:, :, 0] = np.clip(luminance, 0, 255)
    result = cv2.cvtColor(ycrcb.astype(np.uint8), cv2.COLOR_YCrCb2RGB)
    return Image.fromarray(result)


def _extract_bits(array: np.ndarray, count: int) -> list[int]:
    luminance = cv2.cvtColor(array, cv2.COLOR_RGB2YCrCb)[:, :, 0].astype(np.float32)
    height, width = luminance.shape
    bits = []
    for top in range(0, height - _BLOCK_SIZE + 1, _BLOCK_SIZE):
        for left in range(0, width - _BLOCK_SIZE + 1, _BLOCK_SIZE):
            if len(bits) >= count:
                return bits
            coefficients = cv2.dct(luminance[top:top + _BLOCK_SIZE, left:left + _BLOCK_SIZE])
            bits.append(int(coefficients[_COEFFICIENT_A] > coefficients[_COEFFICIENT_B]))
    return bits


def extract_watermark(image: ImageInput) -> str:
    """Extract and decode a watermark, raising ValueError when it is absent or corrupt."""
    array = _to_rgb_array(image)
    header = _extract_bits(array, _HEADER_BITS)
    if len(header) < _HEADER_BITS or _bytes(header[:32]) != _MAGIC:
        raise ValueError('no valid watermark found')
    payload_length = int.from_bytes(_bytes(header[32:48]), 'big')
    payload_bits = _extract_bits(array, _HEADER_BITS + payload_length * 8)
    if len(payload_bits) < _HEADER_BITS + payload_length * 8:
        raise ValueError('watermark payload is incomplete')
    try:
        return _bytes(payload_bits[_HEADER_BITS:]).decode('utf-8')
    except UnicodeDecodeError as error:
        raise ValueError('watermark payload is invalid UTF-8') from error
