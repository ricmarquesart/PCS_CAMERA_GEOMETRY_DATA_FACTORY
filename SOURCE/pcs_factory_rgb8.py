from __future__ import annotations

"""Dependency-free RGB8 PNG transforms used by the Data Factory.

R10 intentionally keeps this module free of Blender/Pillow/OpenCV dependencies so
its byte-level behavior is deterministic under Blender's bundled Python.
"""

import hashlib
import struct
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _round_nearest_signed(n: int, d: int) -> int:
    if d <= 0:
        raise ValueError("denominator must be positive")
    if n >= 0:
        return (n + d // 2) // d
    return -((-n + d // 2) // d)


def fixed_contrast_channel_u8(x: int, *, pivot: int = 128, numerator: int = 5, denominator: int = 4) -> int:
    """Exact affine contrast in integer arithmetic.

    y = pivot + numerator/denominator * (x - pivot)
      = (numerator*x + pivot*(denominator-numerator))/denominator
    rounded to nearest with a deterministic signed rule and clamped to u8.
    """
    x = int(x)
    n = numerator * x + pivot * (denominator - numerator)
    y = _round_nearest_signed(n, denominator)
    return 0 if y < 0 else 255 if y > 255 else y


def _parse_png(data: bytes):
    if not data.startswith(PNG_SIG):
        raise RuntimeError("R10_PNG_SIGNATURE")
    pos = len(PNG_SIG)
    chunks = []
    while pos < len(data):
        if pos + 12 > len(data):
            raise RuntimeError("R10_PNG_TRUNCATED_CHUNK")
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        end = pos + 12 + ln
        if end > len(data):
            raise RuntimeError("R10_PNG_TRUNCATED_PAYLOAD")
        payload = data[pos + 8:pos + 8 + ln]
        crc_expected = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])[0]
        crc_actual = zlib.crc32(typ)
        crc_actual = zlib.crc32(payload, crc_actual) & 0xFFFFFFFF
        if crc_actual != crc_expected:
            raise RuntimeError("R10_PNG_CRC:" + typ.decode("ascii", "replace"))
        chunks.append((typ, payload))
        pos = end
        if typ == b"IEND":
            break
    if not chunks or chunks[-1][0] != b"IEND":
        raise RuntimeError("R10_PNG_IEND_MISSING")
    return chunks


def _chunk(typ: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(typ)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + typ + payload + struct.pack(">I", crc)


def _decode_rgb8(chunks):
    ihdr = next((p for t, p in chunks if t == b"IHDR"), None)
    if ihdr is None or len(ihdr) != 13:
        raise RuntimeError("R10_PNG_IHDR")
    w, h, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", ihdr)
    if bit_depth != 8 or color_type != 2 or comp != 0 or filt != 0 or interlace != 0:
        raise RuntimeError(
            f"R10_PNG_UNSUPPORTED:bit={bit_depth}:color={color_type}:comp={comp}:filter={filt}:interlace={interlace}"
        )
    compressed = b"".join(p for t, p in chunks if t == b"IDAT")
    raw = zlib.decompress(compressed)
    bpp = 3
    stride = w * bpp
    expected = h * (1 + stride)
    if len(raw) != expected:
        raise RuntimeError(f"R10_PNG_RAW_SIZE:{len(raw)}:{expected}")
    rows = []
    prev = bytearray(stride)
    off = 0
    for _ in range(h):
        ft = raw[off]
        off += 1
        scan = bytearray(raw[off:off + stride])
        off += stride
        rec = bytearray(stride)
        for i, x in enumerate(scan):
            a = rec[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 0:
                v = x
            elif ft == 1:
                v = (x + a) & 255
            elif ft == 2:
                v = (x + b) & 255
            elif ft == 3:
                v = (x + ((a + b) // 2)) & 255
            elif ft == 4:
                v = (x + _paeth(a, b, c)) & 255
            else:
                raise RuntimeError("R10_PNG_FILTER:" + str(ft))
            rec[i] = v
        rows.append(rec)
        prev = rec
    return w, h, rows


def apply_fixed_rgb8_contrast_png(
    src_path,
    dst_path,
    *,
    pivot: int = 128,
    numerator: int = 5,
    denominator: int = 4,
):
    """Apply the frozen R10 per-channel transform while preserving ancillary chunks.

    The output is encoded with PNG filter 0 for determinism. All non-IDAT chunks
    from the source are preserved in original order; IDAT is replaced by one
    deterministic stream. No pixel positions or dimensions are changed.
    """
    src = Path(src_path)
    dst = Path(dst_path)
    data = src.read_bytes()
    chunks = _parse_png(data)
    w, h, rows = _decode_rgb8(chunks)
    out_rows = []
    for row in rows:
        out = bytearray(len(row))
        for i, x in enumerate(row):
            out[i] = fixed_contrast_channel_u8(
                x, pivot=pivot, numerator=numerator, denominator=denominator
            )
        out_rows.append(bytes(out))
    raw_out = b"".join(b"\x00" + row for row in out_rows)
    new_idat = zlib.compress(raw_out, level=9)
    rebuilt = bytearray(PNG_SIG)
    idat_written = False
    for typ, payload in chunks:
        if typ == b"IDAT":
            if not idat_written:
                rebuilt.extend(_chunk(b"IDAT", new_idat))
                idat_written = True
            continue
        rebuilt.extend(_chunk(typ, payload))
    if not idat_written:
        raise RuntimeError("R10_PNG_IDAT_MISSING")
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".r10tmp")
    tmp.write_bytes(bytes(rebuilt))
    tmp.replace(dst)
    return {
        "schema": "DF-G100-R10-RGB8-CONTRAST-V1",
        "width": w,
        "height": h,
        "pivot_u8": int(pivot),
        "factor_numerator": int(numerator),
        "factor_denominator": int(denominator),
        "raw_sha256": sha256_bytes(data),
        "final_sha256": sha256_bytes(bytes(rebuilt)),
        "spatial_warp": False,
        "resize": False,
        "resample": False,
        "adaptive": False,
    }


def fixed_gain_channel_u8(x: int, *, numerator: int = 2, denominator: int = 1) -> int:
    """Exact per-channel gain, deterministic integer arithmetic, clamped to u8."""
    x = int(x)
    y = _round_nearest_signed(numerator * x, denominator)
    return 0 if y < 0 else 255 if y > 255 else y


def apply_fixed_rgb8_gain_png(src_path, dst_path, *, numerator: int = 2, denominator: int = 1):
    """Apply the frozen R33 spatially invariant per-channel RGB8 gain.

    Pixel coordinates, dimensions and ancillary PNG chunks are preserved. The
    output IDAT stream is deterministically re-encoded with filter 0 / zlib 9.
    """
    src = Path(src_path); dst = Path(dst_path)
    data = src.read_bytes(); chunks = _parse_png(data)
    w, h, rows = _decode_rgb8(chunks)
    out_rows = []
    for row in rows:
        out = bytearray(len(row))
        for i, x in enumerate(row):
            out[i] = fixed_gain_channel_u8(x, numerator=numerator, denominator=denominator)
        out_rows.append(bytes(out))
    raw_out = b"".join(b"\x00" + row for row in out_rows)
    new_idat = zlib.compress(raw_out, level=9)
    rebuilt = bytearray(PNG_SIG); idat_written = False
    for typ, payload in chunks:
        if typ == b"IDAT":
            if not idat_written:
                rebuilt.extend(_chunk(b"IDAT", new_idat)); idat_written = True
            continue
        rebuilt.extend(_chunk(typ, payload))
    if not idat_written:
        raise RuntimeError("R33_PNG_IDAT_MISSING")
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".r33tmp")
    tmp.write_bytes(bytes(rebuilt)); tmp.replace(dst)
    return {
        "schema": "DF-G100-R33-RGB8-FIXED-GAIN-V1",
        "width": w,
        "height": h,
        "gain_numerator": int(numerator),
        "gain_denominator": int(denominator),
        "offset_u8": 0,
        "raw_sha256": sha256_bytes(data),
        "final_sha256": sha256_bytes(bytes(rebuilt)),
        "spatial_warp": False,
        "resize": False,
        "resample": False,
        "adaptive": False,
        "threshold_adaptive": False,
        "sample_statistics_used": False,
    }
