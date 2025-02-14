from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.camera import Camera
import random

class Maze:
    def __init__(self, width, height, cell_size=2):
        # Asegurarse de usar números impares para un buen funcionamiento.
        self.width = width  
        self.height = height  
        self.cell_size = cell_size  
        # Creamos una matriz inicial: 0 = muro, 1 = camino
        self.maze = [[0 for _ in range(width)] for _ in range(height)]
        # Definimos puntos de entrada y salida:
        self.entry = (1, 1)  # Punto de entrada (se usará si floor_number > 1)
        self.exit = (width - 2, height - 2)  # Punto de salida
        self.generate_maze()
        # Forzamos que la entrada y la salida sean caminos
        self.maze[self.entry[1]][self.entry[0]] = 1
        self.maze[self.exit[1]][self.exit[0]] = 1

    def generate_maze(self):
        # Comenzamos en la celda (1,1)
        start_x, start_y = 1, 1
        self.maze[start_y][start_x] = 1
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack[-1]
            # Vecinos a dos celdas de distancia en las cuatro direcciones
            neighbors = []
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = x + dx, y + dy
                # Verifica que el vecino esté dentro de los límites y no haya sido visitado
                if 0 < nx < self.width - 1 and 0 < ny < self.height - 1:
                    if self.maze[ny][nx] == 0:
                        neighbors.append((nx, ny))
            if neighbors:
                nx, ny = random.choice(neighbors)
                # Rompe la pared entre la celda actual y el vecino seleccionado
                self.maze[(y + ny) // 2][(x + nx) // 2] = 1
                self.maze[ny][nx] = 1
                stack.append((nx, ny))
            else:
                stack.pop()

    def create_entities(self):
        wall_entities = []
        # Se recorre la matriz y se crean entidades para cada muro
        for y in range(self.height):
            for x in range(self.width):
                if self.maze[y][x] == 0:
                    # Posicionamos cada muro en el espacio 3D; usamos x y z para el plano
                    pos = Vec3(x * self.cell_size, 0, y * self.cell_size)
                    wall = Entity(
                        model='cube', 
                        color=color.white, 
                        position=pos, 
                        scale=self.cell_size,
                        collider='box'
                    )
                    wall_entities.append(wall)
        return wall_entities

if __name__ == '__main__':
    app = Ursina()
    
    # Número de piso. Para el piso 1 no se mostrará el punto de entrada (pues no hay piso anterior).
    floor_number = 1  # Cambia este valor para probar distintos pisos.
    # Configuración del laberinto
    maze_width = 21  # Usar números impares (p.ej., 21x21)
    maze_height = 21  
    cell_size = 4
    
    # Generamos el laberinto
    maze = Maze(maze_width, maze_height, cell_size)
    maze.create_entities()
    
    # Creamos un suelo para visualizar mejor el laberinto
    ground = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        texture='white_cube',
        texture_scale=(maze_width, maze_height),
        color=color.gray,
        collider='box'
    )
    ground.position = Vec3((maze_width * cell_size) / 2 - cell_size/2, -cell_size/2, (maze_height * cell_size) / 2 - cell_size/2)

    ceiling = Entity(
        model='plane',
        scale=(maze_width * cell_size, 1, maze_height * cell_size),
        color=color.light_gray,
        collider='box'
    )
    # Posicionamos el techo; en este ejemplo se coloca a una altura de cell_size * 2.
    ceiling.position = Vec3((maze_width * cell_size) / 2 - cell_size/2, cell_size * 2, (maze_height * cell_size) / 2 - cell_size/2)
    
    # Si el piso es mayor a 1, se coloca un marcador en la entrada
    if floor_number > 1:
        entry_x, entry_y = maze.entry
        entry_marker = Entity(
            model='sphere',
            color=color.azure,
            scale=cell_size * 0.5,
            position=Vec3(entry_x * cell_size, cell_size / 2, entry_y * cell_size)
        )

    # Marcador de salida (siempre visible)
    exit_x, exit_y = maze.exit
    exit_marker = Entity(
        model='sphere',
        color=color.red,
        scale=cell_size * 0.5,
        position=Vec3(exit_x * cell_size, cell_size / 2, exit_y * cell_size)
    )

    # Configuramos al jugador en primera persona.
    # Si no es el piso 1, se puede usar la entrada como punto de spawn;
    # para el piso 1, se usará igualmente la posición de la entrada (o puedes definir otra).
    spawn_x, spawn_y = maze.entry  # Puedes modificar este punto si lo deseas.
    player = FirstPersonController()
    player.position = Vec3(spawn_x * cell_size, cell_size, spawn_y * cell_size)
    
    app.run()
