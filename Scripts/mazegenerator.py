from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
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
    
    # --- Código para construir el minimapa por capas ---
    # Suponiendo que 'maze' es tu instancia de Maze, con:
    #   maze.width, maze.height, y maze.maze (la matriz de celdas)
    # También suponemos que 'cell_size' es el tamaño en el mundo 3D (para ubicar al jugador)
    # Creamos un contenedor para el minimapa en la UI
    minimap_container = Entity(parent=camera.ui, name='minimap_container')
    # Ubicación y escala del contenedor en la UI (ajusta según tus preferencias)
    minimap_container.position = (0.73, 0.35)  
    minimap_container.scale = (0.25, 0.25)  # Este contenedor trabajará en un sistema de coordenadas locales de [-0.5, 0.5]

    # Calcula el tamaño de cada celda en coordenadas locales del contenedor
    cell_w = 1 / maze.width    # ancho de celda en el contenedor (el contenedor abarca 1 unidad en cada dimensión)
    cell_h = 1 / maze.height   # alto de celda

    # Creamos la cuadrícula (una capa para los caminos/muros)
    minimap_cells = []  # guardamos las entidades (opcional)
    for y in range(maze.height):
        for x in range(maze.width):
            # Convertimos la posición (x, y) de la matriz al sistema local del contenedor.
            # Queremos que la celda (0,0) (en la matriz) se muestre en la esquina superior izquierda.
            # Por ello invertimos el eje y: la fila 0 se dibuja en y=+0.5 y la última fila en y=-0.5.
            ui_x = -0.5 + cell_w/2 + x * cell_w
            ui_y =  0.5 - cell_h/2 - y * cell_h  # invertimos y

            # Si la celda es camino (1) la pintamos de blanco; si es muro (0) la pintamos de negro.
            # (Puedes modificar los colores si prefieres caminos transparentes, pero aquí usamos blanco para diferenciarlos.)
            cell_color = color.white if maze.maze[y][x] == 1 else color.black

            cell = Entity(
                parent = minimap_container,
                model = 'quad',
                position = (ui_x, ui_y),
                scale = (cell_w, cell_h),
                color = cell_color,
                double_sided = True
            )
            minimap_cells.append(cell)

    # Creamos el marcador del jugador como otro Entity que se posicionará sobre el contenedor.
    player_marker = Entity(
        parent = minimap_container,
        model = 'circle',
        color = color.azure,
        scale = (max(cell_w, cell_h) * 0.8, max(cell_w, cell_h) * 0.8),
        z = -0.01  # Asegura que se dibuje sobre las celdas
    )

    # Actualizamos la posición del marcador en cada frame, de acuerdo con la posición del jugador en el laberinto.
    def update():
        # Se suma la mitad del 'cell_size' para centrar el jugador en la celda,
        # ya que cada celda se considera 2x2 en el mundo.
        px = int((player.position.x + cell_size/2) / cell_size)
        py = int((player.position.z + cell_size/2) / cell_size)

        # Asegurarse de que la posición se mantenga dentro de los límites del laberinto
        px = clamp(px, 0, maze.width - 1)
        py = clamp(py, 0, maze.height - 1)
        
        # Convertir la celda a coordenadas del contenedor del minimapa:
        ui_x = -0.5 + cell_w/2 + px * cell_w
        ui_y =  0.5 - cell_h/2 - py * cell_h
        
        player_marker.position = (ui_x, ui_y)

    app.run()
