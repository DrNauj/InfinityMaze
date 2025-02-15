from PIL import Image
import os

ruta_texturas = 'assets/textures'

for archivo in os.listdir(ruta_texturas):
    if archivo.lower().endswith('.png'):
        img_path = os.path.join(ruta_texturas, archivo)
        try:
            img = Image.open(img_path).convert("RGBA")  # Asegura formato RGBA
            nuevo_path = os.path.join(ruta_texturas, archivo)
            img.save(nuevo_path, format='PNG')  # Guarda en formato PNG estándar
            print(f"✔ Imagen convertida correctamente: {archivo}")
        except Exception as e:
            print(f"❌ Error al convertir {archivo}: {e}")

print("🛠️ Proceso completado. Prueba nuevamente en Ursina.")
