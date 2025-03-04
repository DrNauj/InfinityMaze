from ursina import *
import random
import os
from ursina.shaders import lit_with_shadows_shader  # Añadir esta importación al inicio

class TextureTheme:
    def __init__(self):
        self.texture_path = os.path.join('assets', 'textures')
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
            return self.default_textures['wall']

        try:
            texture = Texture(texture_path)
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
    def __init__(self, width, height, cell_size=2, theme_manager=None, floor_number=1):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.floor_number = floor_number
        self.theme_manager = theme_manager or TextureTheme()
        self.current_theme = self.theme_manager.get_theme('brick')
        self.maze = [[0 for _ in range(width)] for _ in range(height)]
        self.wall_entities = []
        self.trap_buttons = []
        self.markers = []
        self.floor_sections = []
        self.ground = None  # Inicializar como None
        self.ceiling = None
        self.generate_maze()
        self.set_random_entry_exit()
        self.maze[self.entry[1]][self.entry[0]] = 1
        self.maze[self.exit[1]][self.exit[0]] = 1

    def set_random_entry_exit(self):
        self.entry = (random.randint(1, self.width - 2), random.randint(1, self.height - 2))
        self.exit = (random.randint(1, self.width - 2), random.randint(1, self.height - 2))
        while self.exit == self.entry:
            self.exit = (random.randint(1, self.width - 2), random.randint(1, self.height - 2))

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

    def create_maze_entities(self):
        entities = {
            'walls': [],
            'floor': None,
            'ceiling': None,
            'markers': [],
            'traps': []
        }
        
        # Primero crear el piso
        self.create_floor()  # Esto crea self.ground
        
        # Luego crear las paredes
        self.create_walls()
        entities['walls'] = self.wall_entities
        
        # Crear el techo
        self.create_ceiling()
        
        # Crear los marcadores
        self.create_markers()
        entities['markers'] = self.markers
        
        # Finalmente crear las trampas
        self.create_traps()
        entities['traps'] = self.trap_buttons
        
        # Asignar las entidades creadas
        entities['floor'] = self.ground
        entities['ceiling'] = self.ceiling
        
        return entities

    def create_walls(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y][x] == 0:
                    pos = Vec3(x * self.cell_size, 0, y * self.cell_size)
                    texture = self.current_theme['textures']['wall']
                    wall_color = self.current_theme['colors']['wall']
                    wall = Entity(
                        parent=self.ground,
                        model='cube',
                        scale=Vec3(self.cell_size, self.cell_size, self.cell_size),
                        position=Vec3(x * self.cell_size, 0, y * self.cell_size),
                        texture=texture,
                        color=wall_color,
                        collider='box',
                        shader=lit_with_shadows_shader  # Añadir shader
                    )
                    if texture:
                        wall.texture = texture
                        wall.texture_scale = (4, 4)
                        wall.color = wall_color
                    else:
                        wall.color = wall_color
                    self.wall_entities.append(wall)

    def create_floor(self):
        self.ground = Entity()
        self.floor_sections = []

        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y][x] == 1:
                    pos_x = x * self.cell_size
                    pos_z = y * self.cell_size
                    
                    section = Entity(
                        parent=self.ground,
                        model='cube',
                        scale=(self.cell_size, 0.2, self.cell_size),
                        position=Vec3(pos_x, -self.cell_size/2, pos_z),
                        texture=self.current_theme['textures']['floor'],
                        texture_scale=(4, 4),
                        color=self.current_theme['colors']['floor'],
                        collider='box',
                        shader=lit_with_shadows_shader
                    )

                    self.floor_sections.append({
                        'entity': section,
                        'borders': [],
                        'position': (x, y)
                    })

    def create_ceiling(self):
        self.ceiling = Entity(
            model='plane',
            scale=(self.width * self.cell_size, 1, self.height * self.cell_size),
            texture=self.current_theme['textures']['ceiling'],
            texture_scale=(self.width*4, self.height*4),
            collider='box',
            rotation_x=180
        )
        self.ceiling.color = self.current_theme['colors']['ceiling']
        self.ceiling.position = Vec3(
            (self.width * self.cell_size) / 2 - self.cell_size/2,
            self.cell_size/2,
            (self.height * self.cell_size) / 2 - self.cell_size/2
        )

    def create_markers(self):
        self.markers = []
        if self.floor_number > 1:
            entry_marker = Entity(
                model='sphere',
                color=color.azure,
                scale=self.cell_size * 0.5,
                position=Vec3(self.entry[0] * self.cell_size, self.cell_size / 2, self.entry[1] * self.cell_size)
            )
            self.markers.append(entry_marker)

        exit_marker = Entity(
            model='sphere',
            color=color.red,
            scale=self.cell_size * 0.5,
            position=Vec3(self.exit[0] * self.cell_size, -2, self.exit[1] * self.cell_size)
        )
        self.markers.append(exit_marker)

    def create_traps(self, num_traps=9):
        self.trap_buttons = []
        section_size = self.cell_size / 4  # Para las secciones divididas

        for _ in range(num_traps):
            while True:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)
                if (self.maze[y][x] == 1 and 
                    distance_2d((x, y), self.entry) > 2 and 
                    distance_2d((x, y), self.exit) > 2):

                    # Encontrar y destruir la sección original del piso
                    for section in self.floor_sections:
                        if section['position'] == (x, y):
                            destroy(section['entity'])
                            self.floor_sections.remove(section)
                            break

                    pos_x = x * self.cell_size
                    pos_z = y * self.cell_size
                    
                    sections = []
                    # Crear las secciones del borde para la trampa
                    for row in range(4):
                        for col in range(4):
                            is_center = (1 <= row <= 2) and (1 <= col <= 2)
                            if not is_center:
                                border = Entity(
                                    parent=self.ground,
                                    model='cube',
                                    scale=(section_size, 0.2, section_size),
                                    position=Vec3(
                                        pos_x - self.cell_size/2 + section_size/2 + col * section_size,
                                        -self.cell_size/2,
                                        pos_z - self.cell_size/2 + section_size/2 + row * section_size
                                    ),
                                    texture=self.current_theme['textures']['floor'],
                                    texture_scale=(1, 1),
                                    color=self.current_theme['colors']['floor'],
                                    collider='box'
                                )
                                sections.append(border)

                    # Crear la sección central (2x2)
                    center = Entity(
                        parent=self.ground,
                        model='cube',
                        scale=(section_size * 2, 0.2, section_size * 2),
                        position=Vec3(pos_x, -self.cell_size/2, pos_z),
                        texture=self.current_theme['textures']['floor'],
                        texture_scale=(2, 2),
                        color=self.current_theme['colors']['floor'],
                        collider='box'
                    )

                    # Agregar la nueva sección dividida
                    self.floor_sections.append({
                        'entity': center,
                        'borders': sections,
                        'position': (x, y)
                    })

                    # Crear el botón y el hoyo de la trampa
                    trap_button = Entity(
                        model='cube',
                        scale=(self.cell_size * 0.4, 0.2, self.cell_size * 0.4),
                        position=Vec3(pos_x, -self.cell_size/2 + 0.1, pos_z),
                        color=color.red,
                        collider='box'
                    )

                    hole = Entity(
                        model='cube',
                        scale=(self.cell_size * 0.5, 0.1, self.cell_size * 0.5),
                        position=Vec3(pos_x, -self.cell_size/2 - 0.1, pos_z),
                        color=color.black66,
                        visible=False
                    )

                    self.trap_buttons.append({
                        'button': trap_button,
                        'hole': hole,
                        'floor_section': center,
                        'activated': False,
                        'position': (x, y)
                    })
                    break

    def check_maze_boundaries(self, position):
        x, z = position.x / self.cell_size, position.z / self.cell_size
        margin = 1
        # Ajustar el límite vertical para una detección más rápida
        if (x < -margin or x > self.width + margin or 
            z < -margin or z > self.height + margin or 
            position.y < -10):  # Límite vertical más cercano
            return False
        return True

    def get_player_start_position(self):
        return Vec3(
            self.entry[0] * self.cell_size,
            0,
            self.entry[1] * self.cell_size
        )

    def check_player_exit(self, player_position):
        exit_pos = Vec3(self.exit[0] * self.cell_size, 0, self.exit[1] * self.cell_size)
        if distance(player_position, exit_pos) < self.cell_size:
            return True
        return False

# Función auxiliar para calcular distancia 2D
def distance_2d(pos1, pos2):
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5