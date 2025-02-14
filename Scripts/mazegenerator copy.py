from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.camera import Camera
import random

class Maze:
    def __init__(self, width, height, cell_size=2):
        # Usar números impares para que el algoritmo funcione bien.
        self.width = width  
        self.height = height  
        self.cell_size = cell_size  
        # Matriz: 0 = muro, 1 = camino.
        self.maze = [[0 for _ in range(width)] for _ in range(height)]
        # Definir puntos de entrada y salida:
        self.entry = (1, 1)  
        self.exit = (width - 2, height - 2)
        self.generate_maze()
        # Forzamos que la entrada y la salida sean caminos.
        self.maze[self.entry[1]][self.entry[0]] = 1
        self.maze[self.exit[1]][self.exit[0]] = 1

    def generate_maze(self):
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 1
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack[-1]
            # Vecinos a dos celdas de distancia (4 direcciones)
            neighbors = []
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = x + dx, y + dy
                if 0 < nx < self.width - 1 and 0 < ny < self.height - 1:
                    if self.maze[ny][nx] == 0:
                        neighbors.append((nx, ny))
            if neighbors:
                nx, ny = random.choice(neighbors)
                # Romper la pared intermedia
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
                    # Posición en el plano XZ, usando 'y' para la coordenada Z.
                    pos = Vec3(x * self.cell_size, self.cell_size / 2, y * self.cell_size)
                    wall = Entity(model='cube',
                                  color=color.white,
                                  position=pos,
                                  scale=(self.cell_size, self.cell_size, self.cell_size),
                                  collider='box')  # Collider para evitar que se atraviese
                    wall_entities.append(wall)
        return wall_entities

if __name__ == '__main__':
    app = Ursina()

    # Parámetros del laberinto.
    floor_number = 1  # Para el piso 1, se usa la entrada por defecto.
    maze_width = 21  # Usar números impares (ej., 21x21)
    maze_height = 21  
    cell_size = 2
    
    # Generar el laberinto.
    maze = Maze(maze_width, maze_height, cell_size)
    maze.create_entities()
    
    # Suelo del laberinto con collider.
    ground = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        texture='white_cube',
        texture_scale=(maze_width, maze_height),
        color=color.gray,
        collider='box'
    )
    ground.position = Vec3((maze_width * cell_size) / 2 - cell_size/2, 0,
                           (maze_height * cell_size) / 2 - cell_size/2)
    
    # Techo para evitar que el jugador se salga por arriba.
    ceiling = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        color=color.light_gray,
        collider='box'
    )
    ceiling.position = Vec3((maze_width * cell_size) / 2 - cell_size/2, cell_size * 2,
                            (maze_height * cell_size) / 2 - cell_size/2)
    
    # Marcadores de entrada y salida.
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
    
    # Configurar al jugador en primera persona.
    spawn_x, spawn_y = maze.entry  # Se puede ajustar según se necesite.
    player = FirstPersonController()
    player.position = Vec3(spawn_x * cell_size, cell_size, spawn_y * cell_size)
    
    # ==============================
    # Configuración del Mini Mapa
    # ==============================
    # Crear una cámara adicional para el mini mapa.
    # Configuración del Mini Mapa
    
    # Configuración del Mini Mapa
    # ==============================
    # Crear cámara para el minimapa
    mini_map_camera = Entity()
    mini_map_camera.camera = Camera()  # Crear componente Camera por separado
    mini_map_camera.camera.orthographic = True  # Configurar como ortográfica
    mini_map_camera.camera.fov = 20  # Ajustar según el tamaño del laberinto
    mini_map_camera.position = (player.position.x, 50, player.position.z)
    mini_map_camera.rotation_x = 90  # Mirar hacia abajo
    mini_map_camera.camera.render_target = True  # Habilitar renderizado en textura

    # Crear Sprite del minimapa
    mini_map = Sprite(
        texture=mini_map_camera.camera.render_texture,
        parent=camera.ui,
        position=(0.7, 0.45),
        scale=(0.3, 0.3),
        color=color.rgba(255, 255, 255, 200)
    )

    def update():
        # Actualizar posición de la cámara del minimapa
        mini_map_camera.position = (player.position.x, 50, player.position.z)
    app.run()
