import requests
import io
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (200, 100), color = (255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "Date Description Amount", fill=(0,0,0))
d.text((10,30), "01/01/2024 Coffee -5.00", fill=(0,0,0))

buf = io.BytesIO()
img.save(buf, format='PNG')
byte_im = buf.getvalue()

files = {"file": ("statement.png", byte_im)}
res = requests.post("http://localhost:8001/api/v1/upload", files=files)
print(res.status_code)
print(res.text)
