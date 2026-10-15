import os
from PIL import Image, ImageDraw

os.makedirs('installer', exist_ok=True)
sizes = [16, 32, 48, 64, 128, 256]
images = []

for s in sizes:
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer circle background: deep indigo / navy blue
    margin = int(s * 0.04)
    draw.ellipse([margin, margin, s - margin, s - margin], fill=(18, 30, 66, 255), outline=(79, 140, 255, 255), width=max(1, int(s * 0.03)))
    
    # Orbit rings (physics / atom / satellite motif)
    center = s // 2
    rx = int(s * 0.38)
    ry = int(s * 0.16)
    
    # Center nucleus / planet (cyan / light blue)
    r_core = max(2, int(s * 0.12))
    draw.ellipse([center - r_core, center - r_core, center + r_core, center + r_core], fill=(0, 220, 255, 255))
    
    # Two elliptical orbits
    # Horizontal orbit
    draw.ellipse([center - rx, center - ry, center + rx, center + ry], outline=(120, 180, 255, 200), width=max(1, int(s * 0.025)))
    # Vertical / tilted orbit approximated
    draw.ellipse([center - ry, center - rx, center + ry, center + rx], outline=(255, 170, 80, 200), width=max(1, int(s * 0.025)))
    
    # Electron / satellite bead
    bead_r = max(1, int(s * 0.04))
    bx = center + int(rx * 0.7)
    by = center - int(ry * 0.7)
    draw.ellipse([bx - bead_r, by - bead_r, bx + bead_r, by + bead_r], fill=(255, 215, 0, 255))

    images.append(img)

# Save as ICO file containing all sizes
icon_path = 'installer/app.ico'
images[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
print(f"Successfully generated multi-size icon: {icon_path} (sizes: {sizes})")
