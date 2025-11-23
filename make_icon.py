from PIL import Image

# Wejście/wyjście
SRC = "ikona.png"
DST = "ikona.ico"

# Rozmiary, które wbudujemy do ICO (Windows je lubi)
sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]

img = Image.open(SRC).convert("RGBA")
icons = [img.resize(s, Image.LANCZOS) for s in sizes]
icons[0].save(DST, format="ICO", sizes=sizes)
print(f"Zrobione: {DST}")
