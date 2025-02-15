from PIL import Image
import os

# Ruta donde se encuentran las texturas
ruta_texturas = 'assets/textures'  # Ajusta esta ruta según tu proyecto

# Verifica si la carpeta existe
if not os.path.exists(ruta_texturas):
    print(f"Error: La carpeta '{ruta_texturas}' no existe.")
else:
    for archivo in os.listdir(ruta_texturas):
        if archivo.lower().endswith('.png'):  # Asegura que solo modifique archivos PNG
            img_path = os.path.join(ruta_texturas, archivo)
            try:
                img = Image.open(img_path)
                img.save(img_path, icc_profile=None)  # Guarda la imagen sin el perfil ICC
                print(f"Perfil ICC eliminado: {archivo}")
            except Exception as e:
                print(f"Error al procesar {archivo}: {e}")

print("Proceso completado.")
