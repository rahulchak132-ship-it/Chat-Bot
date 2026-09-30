import struct
import zlib
import os

def create_png_logo(filepath, width=256, height=256):
    raw_data = bytearray()
    
    # Generate a sleek corporate badge with deep navy / cyan-emerald gradient
    # and a central CX hexagon/monogram emblem
    for y in range(height):
        raw_data.append(0)  # filter type 0 (None)
        for x in range(width):
            # Centered coordinates (-1.0 to 1.0)
            nx = (x - width / 2) / (width / 2)
            ny = (y - height / 2) / (height / 2)
            dist_sq = nx * nx + ny * ny
            
            # Rounded squircle container
            # (|x|^3.5 + |y|^3.5)^(1/3.5) < 0.88
            val = (abs(nx)**3.6 + abs(ny)**3.6)**(1/3.6)
            
            if val <= 0.86:
                # Background gradient: Deep slate navy to royal sapphire
                factor = (y / height)
                r = int(15 * (1 - factor) + 30 * factor)
                g = int(23 * (1 - factor) + 58 * factor)
                b = int(42 * (1 - factor) + 138 * factor)
                a = 255
                
                # Outer glowing rim
                if 0.80 <= val <= 0.86:
                    glow = (val - 0.80) / 0.06
                    r = int(r * (1 - glow) + 56 * glow)
                    g = int(g * (1 - glow) + 189 * glow)
                    b = int(b * (1 - glow) + 248 * glow)

                # Central Shield / Diamond Geometry
                diamond = abs(nx) * 1.35 + abs(ny) * 1.35
                if 0.38 <= diamond <= 0.44:
                    # Cyan accent ring
                    r, g, b = 14, 165, 233
                elif diamond < 0.38:
                    # Inside core
                    r, g, b = 24, 37, 69
                    # Stylized "C" arc
                    arc_dist = (nx + 0.08)**2 + ny**2
                    if 0.02 <= arc_dist <= 0.055 and not (nx > -0.04 and -0.1 < ny < 0.1):
                        r, g, b = 255, 255, 255
                    
                    # Stylized "X" cross
                    x1 = nx - 0.12
                    y1 = ny
                    if (abs(x1 - y1) < 0.035 or abs(x1 + y1) < 0.035) and abs(x1) < 0.12 and abs(y1) < 0.12:
                        r, g, b = 56, 189, 248
            else:
                r, g, b, a = 0, 0, 0, 0
                
            raw_data.extend((r, g, b, a))

    def make_chunk(chunk_type, data):
        length = struct.pack("!I", len(data))
        crc = struct.pack("!I", zlib.crc32(chunk_type + data) & 0xffffffff)
        return length + chunk_type + data + crc

    ihdr_data = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_chunk = make_chunk(b"IHDR", ihdr_data)
    idat_chunk = make_chunk(b"IDAT", zlib.compress(bytes(raw_data), 9))
    iend_chunk = make_chunk(b"IEND", b"")

    png_bytes = b"\x89PNG\r\n\x1a\n" + ihdr_chunk + idat_chunk + iend_chunk
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(png_bytes)
    print(f"Generated PNG logo at {filepath} ({len(png_bytes)} bytes)")

if __name__ == "__main__":
    create_png_logo("customer_experience_bot/assets/logo.png")
    # Also create a copy in assets/ for root if needed
    create_png_logo("assets/logo.png")
