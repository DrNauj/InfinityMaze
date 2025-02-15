from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import sequence, Wait, Func
import random
import os

def load_custom_texture(texture_name):
    ruta_absoluta = os.path.abspath(os.path.join('assets', 'texture', texture_name))
    if not os.path.exists(ruta_absoluta):
        print(f"ADVERTENCIA: No se encontró la textura en {ruta_absoluta}")
        return None
    print(f"Intentando cargar textura desde: {ruta_absoluta}")
    return load_texture(ruta_absoluta)  # Usa la ruta absoluta

class TextureTheme:
    def __init__(self):
        self.texture_path = os.path.join('assets', 'texture')
        print(f"Buscando texturas en: {os.path.abspath(self.texture_path)}")

        self.default_textures = {
            'wall': 'white_cube',
            'floor': 'white_cube',
            'ceiling': 'white_cube'
        }

        self.default_colors = {
            'wall': color.white,
            'floor': color.gray,
            'ceiling': color.light_gray
        }

        self.maze_themes = {
            'cave': {
                'textures': {
                    'wall': self._load_texture('cave_wall.png'),
                    'floor': self._load_texture('cave_floor.png'),
                    'ceiling': self._load_texture('cave_ceiling.png')
                },
            },
            'brick': {
                'textures': {
                    'wall': self._load_texture('brick_wall.png'),
                    'floor': self._load_texture('brick_floor.png'),
                    'ceiling': self._load_texture('brick_ceiling.png')
                },
            }
        }

    def _load_texture(self, texture_name):
        texture_path = os.path.join(self.texture_path, texture_name)
        
        if not os.path.exists(texture_path):
            print(f"❌ ADVERTENCIA: No se encontró la textura en {texture_path}")
            return self.default_textures['wall']  # Retorna la textura por defecto

        try:
            texture = Texture(texture_path)  # Fuerza la carga sin load_texture()
            print(f"✅ Textura cargada correctamente: {texture_path}")
            return texture
        except Exception as e:
            print(f"❌ ERROR al cargar la textura {texture_path}: {str(e)}")
            return self.default_textures['wall']

    def get_theme(self, theme_name='default'):
        if theme_name in self.maze_themes:
            theme = self.maze_themes[theme_name]
            result = {'textures': {}, 'colors': {}}
            for key in ['wall', 'floor', 'ceiling']:
                texture = theme['textures'][key]
                # Si la textura es la predeterminada ('white_cube'), usamos el color por defecto;
                # de lo contrario, al haberse cargado una imagen, usamos color.white para que el
                # multiplicador no altere la imagen.
                if texture == self.default_textures[key]:
                    result['textures'][key] = texture
                    result['colors'][key] = self.default_colors[key]
                else:
                    result['textures'][key] = texture
                    result['colors'][key] = color.white
            return result
        return {'textures': self.default_textures, 'colors': self.default_colors}
    
    def get_random_theme(self):
        theme_name = random.choice(list(self.maze_themes.keys()))
        return self.get_theme(theme_name)

class Maze:
    def __init__(self, width, height, cell_size=2, theme_manager=None):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.theme_manager = theme_manager or TextureTheme()
        self.current_theme = self.theme_manager.get_theme('cave')  # Puedes cambiar el tema aquí
        self.maze = [[0 for _ in range(width)] for _ in range(height)]
        self.entry = (1, 1)
        self.exit = (width - 2, height - 2)
        self.generate_maze()
        self.maze[self.entry[1]][self.entry[0]] = 1
        self.maze[self.exit[1]][self.exit[0]] = 1

    def generate_maze(self):
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 1
        stack = [(start_x, start_y)]
        while stack:
            x, y = stack[-1]
            neighbors = []
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = x + dx, y + dy
                if 0 < nx < self.width - 1 and 0 < ny < self.height - 1:
                    if self.maze[ny][nx] == 0:
                        neighbors.append((nx, ny))
            if neighbors:
                nx, ny = random.choice(neighbors)
                self.maze[(y + ny) // 2][(x + nx) // 2] = 1
                self.maze[ny][nx] = 1
                stack.append((nx, ny))
            else:
                stack.pop()

    def create_entities(self):
        wall_entities = []
        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y][x] == 0:
                    pos = Vec3(x * self.cell_size, 0, y * self.cell_size)
                    texture = self.current_theme['textures']['wall']
                    wall_color = self.current_theme['colors']['wall']
                    wall = Entity(
                        model='cube',
                        position=pos,
                        scale=Vec3(self.cell_size, self.cell_size * 2, self.cell_size),
                        collider='box'
                    )
                    if texture:
                        wall.texture = texture
                        wall.texture_scale = (2, 4)
                        wall.color = wall_color  # Será color.white para texturas cargadas
                    else:
                        wall.color = wall_color
                    wall_entities.append(wall)
        return wall_entities

class CustomFirstPersonController(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.normal_speed = 8
        self.sprint_speed = 16
        self.normal_height = 2
        self.crouch_height = 1
        self.is_crouching = False
        self.target_height = self.normal_height  # Altura deseada
        self.collider='box'

    def input(self, key):
        super().input(key)

        if key == 'left shift':
            self.speed = self.sprint_speed
        elif key == 'left shift up':
            self.speed = self.normal_speed

        if key == 'left control':  # Agacharse
            self.is_crouching = True
            self.target_height = self.crouch_height  # Cambia la altura objetivo
        elif key == 'left control up':  # Levantarse
            self.is_crouching = False
            self.target_height = self.normal_height  # Cambia la altura objetivo
    def update(self):
        super().update()
        # Suaviza el cambio de altura interpolando entre la altura actual y la deseada
        self.camera_pivot.y = lerp(self.camera_pivot.y, self.target_height, time.dt * 8)

if __name__ == '__main__':
    app = Ursina()
    # Intenta cargar la textura usando solo el nombre, sin ruta absoluta
    test_texture = load_texture('cave_wall.png')  # Prueba primero con esto

    if test_texture is None:
        print("⚠️ No se pudo cargar la textura usando solo el nombre. Probando ruta completa...")
        test_texture = load_texture('assets/textures/cave_wall.png')  # Prueba con ruta relativa

    if test_texture is None:
        print("❌ No se pudo cargar la textura de ninguna forma.")
    else:
        print("✅ Textura cargada correctamente. Mostrando en pantalla...")
        test_entity = Entity(model='cube', texture=test_texture, scale=3)

    # Configuración de la ventana
    window.borderless = False
    window.fullscreen = False
    window.fps_counter.enabled = True
    window.exit_button.visible = True

    floor_number = 1
    maze_width = 21
    maze_height = 21
    cell_size = 6
    # Inicializamos el administrador de texturas
    theme_manager = TextureTheme()
    maze = Maze(maze_width, maze_height, cell_size, theme_manager)
    walls = maze.create_entities()
    
    # Suelo: si la textura es la predeterminada se asigna un color (por ejemplo, gris),
    # de lo contrario se asigna color.white para no modificar la imagen.
    ground = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        texture=maze.current_theme['textures']['floor'],
        texture_scale=(maze_width, maze_height),
        collider='box'
    )
    ground.color = maze.current_theme['colors']['floor']
    ground.position = Vec3(
        (maze_width * cell_size) / 2 - cell_size/2,
        -cell_size/2,
        (maze_height * cell_size) / 2 - cell_size/2
    )

    # Techo
    ceiling = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        texture=maze.current_theme['textures']['ceiling'],
        texture_scale=(maze_width, maze_height),
        collider='box',
        rotation_x=180
    )
    ceiling.color = maze.current_theme['colors']['ceiling']
    ceiling.position = Vec3(
        (maze_width * cell_size) / 2 - cell_size/2,
        cell_size,
        (maze_height * cell_size) / 2 - cell_size/2
    )
    
    if floor_number > 1:
        entry_x, entry_y = maze.entry
        entry_marker = Entity(
            model='sphere',
            color=color.azure,
            scale=cell_size * 0.5,
            position=Vec3(entry_x * cell_size, cell_size / 2, entry_y * cell_size)
        )

    exit_x, exit_y = maze.exit
    exit_marker = Entity(
        model='sphere',
        color=color.red,
        scale=cell_size * 0.5,
        position=Vec3(exit_x * cell_size, cell_size / 2, exit_y * cell_size)
    )

    player = CustomFirstPersonController()
    player.position = Vec3(
        maze.entry[0] * cell_size,
        cell_size /2,
        maze.entry[1] * cell_size
    )
    Sky()
    camera.fov = 90
    
    # Crear un botón en el suelo como trampa
    trap_button = Entity(
        model='cube',
        scale=(cell_size / 2, 0.2, cell_size / 2),  # Pequeño botón en el suelo
        position=Vec3(maze.exit[0] * cell_size, -cell_size / 2 + 0.1, maze.exit[1] * cell_size),
        color=color.red,
        collider='box'
    )
    # Cantidad de trampas en el laberinto
    NUM_TRAPS = 5

    trap_buttons = []  # Lista para almacenar las trampas

    # Generar trampas en posiciones aleatorias del camino
    for _ in range(NUM_TRAPS):
        while True:
            x = random.randint(1, maze_width - 2)  # Evitar bordes
            y = random.randint(1, maze_height - 2)

            if maze.maze[y][x] == 1:  # Solo colocar en caminos
                trap_button = Entity(
                    model='cube',
                    scale=(cell_size * 0.6, 0.2, cell_size * 0.6),  # Más grande para mejor detección
                    position=Vec3(x * cell_size, -cell_size / 2 + 0.1, y * cell_size),
                    color=color.red,
                    collider='box'
                )
                trap_buttons.append(trap_button)
                break  # Salir del bucle al encontrar una posición válida

    # Función para verificar si el jugador pisa una trampa
    def check_traps():
        for trap in trap_buttons:
            collision = player.intersects(trap)

            # Depuración: Ver si la colisión está ocurriendo
            if collision.hit:
                print(f"✅ Trampa activada en {trap.position} - Colisión detectada con el jugador.")

                # Hacer que el botón baje como indicación visual
                trap.animate_position(trap.position + Vec3(0, -0.1, 0), duration=0.2, curve=curve.linear)

                # Esperar 0.5 segundos antes de teletransportar al jugador
                invoke(reset_player, delay=0.5)

                return  # Evita activar múltiples trampas a la vez

        print("❌ No se detectó ninguna colisión con las trampas.")


    def reset_player():
        print("🏃‍♂️ Regresando al inicio...")
        player.position = Vec3(maze.entry[0] * cell_size, cell_size / 2, maze.entry[1] * cell_size)


    # Minimapa
    minimap_container = Entity(parent=camera.ui, name='minimap_container')
    minimap_container.position = (0.73, 0.35)
    minimap_container.scale = (0.25, 0.25)

    cell_w = 1 / maze.width
    cell_h = 1 / maze.height

    minimap_cells = []
    for y in range(maze.height):
        for x in range(maze.width):
            ui_x = -0.5 + cell_w/2 + x * cell_w
            ui_y = 0.5 - cell_h/2 - y * cell_h
            cell_color = color.white if maze.maze[y][x] == 1 else color.black
            cell = Entity(
                parent=minimap_container,
                model='quad',
                position=(ui_x, ui_y),
                scale=(cell_w, cell_h),
                color=cell_color,
                double_sided=True
            )
            minimap_cells.append(cell)

    player_marker = Entity(
        parent=minimap_container,
        model='circle',
        color=color.azure,
        scale=(max(cell_w, cell_h) * 0.8, max(cell_w, cell_h) * 0.8),
        z=-0.01
    )

    def update():
        check_traps()
        px = int((player.position.x + cell_size/2) / cell_size)
        py = int((player.position.z + cell_size/2) / cell_size)
        px = clamp(px, 0, maze.width - 1)
        py = clamp(py, 0, maze.height - 1)        
        ui_x = -0.5 + cell_w/2 + px * cell_w
        ui_y = 0.5 - cell_h/2 - py * cell_h        
        player_marker.position = (ui_x, ui_y)
    app.run()
