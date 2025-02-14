from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

class TextureTheme:
    """Maneja las texturas del laberinto con temas predefinidos"""
    def __init__(self):
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
                'colors': {
                    'wall': color.rgb(120, 120, 120),
                    'floor': color.rgb(90, 90, 90),
                    'ceiling': color.rgb(70, 70, 70)
                }
            },
            'brick': {
                'textures': {
                    'wall': self._load_texture('brick_wall.png'),
                    'floor': self._load_texture('brick_floor.png'),
                    'ceiling': self._load_texture('brick_ceiling.png')
                },
                'colors': {
                    'wall': color.rgb(150, 130, 120),
                    'floor': color.rgb(130, 120, 110),
                    'ceiling': color.rgb(120, 110, 100)
                }
            }
        }

    def _load_texture(self, texture_name):
        try:
            return load_texture(f'assets/textures/{texture_name}')
        except:
            print(f"No se pudo cargar la textura {texture_name}, usando textura por defecto")
            return self.default_textures['wall']

    def get_theme(self, theme_name='default'):
        if theme_name in self.maze_themes:
            return self.maze_themes[theme_name]
        return {
            'textures': self.default_textures,
            'colors': self.default_colors
        }

    def get_random_theme(self):
        theme_name = random.choice(list(self.maze_themes.keys()))
        return self.get_theme(theme_name)

class Maze:
    def __init__(self, width, height, cell_size=2, theme_manager=None):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.theme_manager = theme_manager or TextureTheme()
        self.current_theme = self.theme_manager.get_random_theme()
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
                    wall = Entity(
                        model='cube',
                        texture=self.current_theme['textures']['wall'],
                        color=self.current_theme['colors']['wall'],
                        position=pos,
                        scale=Vec3(self.cell_size, self.cell_size * 2, self.cell_size),
                        collider='box'
                    )
                    wall_entities.append(wall)
        return wall_entities

if __name__ == '__main__':
    app = Ursina()
    
    floor_number = 1
    maze_width = 21
    maze_height = 21
    cell_size = 6
    
    # Inicializamos el administrador de texturas
    theme_manager = TextureTheme()
    
    # Generamos el laberinto con el administrador de texturas
    maze = Maze(maze_width, maze_height, cell_size, theme_manager)
    maze.create_entities()
    
    # Creamos el suelo con la textura del tema actual
    ground = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        texture=maze.current_theme['textures']['floor'],
        texture_scale=(maze_width, maze_height),
        color=maze.current_theme['colors']['floor'],
        collider='box'
    )
    ground.position = Vec3((maze_width * cell_size) / 2 - cell_size/2, -cell_size/2, (maze_height * cell_size) / 2 - cell_size/2)

    ceiling = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        texture=maze.current_theme['textures']['ceiling'],
        texture_scale=(maze_width, maze_height),
        color=maze.current_theme['colors']['ceiling'],
        collider='box'
    )
    ceiling.position = Vec3((maze_width * cell_size) / 2 - cell_size/2, cell_size * 2, (maze_height * cell_size) / 2 - cell_size/2)
    
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

    spawn_x, spawn_y = maze.entry
    player = FirstPersonController()
    player.position = Vec3(spawn_x * cell_size, cell_size, spawn_y * cell_size)
    
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
        px = int((player.position.x + cell_size/2) / cell_size)
        py = int((player.position.z + cell_size/2) / cell_size)

        px = clamp(px, 0, maze.width - 1)
        py = clamp(py, 0, maze.height - 1)
        
        ui_x = -0.5 + cell_w/2 + px * cell_w
        ui_y = 0.5 - cell_h/2 - py * cell_h
        
        player_marker.position = (ui_x, ui_y)

    app.run()