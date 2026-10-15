"""Draws the Tiny IDE app icon (pure Python, no extra packages)."""
import base64, math, struct, zlib


def _box(px, py, cx, cy, hx, hy, r):
    """signed distance to a rounded box (negative = inside)"""
    qx, qy = abs(px - cx) - (hx - r), abs(py - cy) - (hy - r)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r


def _seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def make_png(size=128):
    ss = 2
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            r = g = b = a = 0.0
            for sy in range(ss):
                for sx in range(ss):
                    px, py = (x + (sx + .5) / ss) / size, (y + (sy + .5) / ss) / size
                    if _box(px, py, .5, .5, .46, .46, .2) > 0:
                        continue
                    t = (px + py) / 2
                    cr, cg, cb = 79 + 89 * t, 70 + 15 * t, 229 + 18 * t
                    if min(_seg(px, py, .27, .32, .50, .50), _seg(px, py, .50, .50, .27, .68)) <= .045:
                        cr, cg, cb = 255, 255, 255
                    elif _box(px, py, .665, .6775, .105, .0425, .0425) <= 0:
                        cr, cg, cb = 125, 249, 255
                    r += cr; g += cg; b += cb; a += 255
            n = ss * ss
            if a:
                k = a / 255
                row += bytes((int(r / k), int(g / k), int(b / k), int(a / n)))
            else:
                row += bytes((0, 0, 0, 0))
        rows.append(bytes(row))

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def png_base64(size=64):
    return base64.b64encode(make_png(size)).decode()