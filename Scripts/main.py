from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from mazegenerator import Maze, TextureTheme

class CustomFirstPersonController(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.normal_speed = 8
        self.sprint_speed = 16
        self.normal_height = 2
        self.crouch_height = 1
        self.is_crouching = False
        self.target_height = self.normal_height
        self.collider = 'box'

    def input(self, key):
        super().input(key)
        if key == 'left shift':
            self.speed = self.sprint_speed
        elif key == 'left shift up':
            self.speed = self.normal_speed
        if key == 'left control':
            self.is_crouching = True
            self.target_height = self.crouch_height
        elif key == 'left control up':
            self.is_crouching = False
            self.target_height = self.normal_height

    def update(self):
        super().update()
        self.camera_pivot.y = lerp(self.camera_pivot.y, self.target_height, time.dt * 8)

class MazeGame:
    def __init__(self):
        self.app = Ursina()
        self.setup_window()
        self.theme_manager = TextureTheme()
        self.current_floor = 1
        self.is_paused = False
        self.setup_maze()
        self.setup_player()
        self.setup_minimap()
        self.setup_sky()
        self.setup_pause_menu()
        self.app.taskMgr.add(self.update_task, "update_task")

    def setup_pause_menu(self):
        # Crear el contenedor del menú de pausa
        self.pause_menu = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.4, 0.6),
            color=color.black66,
            visible=False
        )
        
        # Título del menú
        Text("PAUSE MENU", parent=self.pause_menu, y=0.2, scale=2, origin=(0, 0))
        
        # Botones del menú
        button_width = 0.3
        button_height = 0.05
        
        # Botón para alternar pantalla completa
        self.fullscreen_button = Button(
            parent=self.pause_menu,
            text='Toggle Fullscreen',
            scale=(button_width, button_height),
            y=0.05,
            color=color.azure
        )
        self.fullscreen_button.on_click = self.toggle_fullscreen
        
        # Botón para ajustar resolución
        self.resolution_button = Button(
            parent=self.pause_menu,
            text='Resolution: 1280x720',
            scale=(button_width, button_height),
            y=-0.05,
            color=color.azure
        )
        self.resolution_button.on_click = self.cycle_resolution
        
        # Botón para reiniciar el juego
        self.restart_button = Button(
            parent=self.pause_menu,
            text='Restart Game',
            scale=(button_width, button_height),
            y=-0.15,
            color=color.orange
        )
        self.restart_button.on_click = self.restart_game
        
        # Botón para salir
        self.quit_button = Button(
            parent=self.pause_menu,
            text='Quit Game',
            scale=(button_width, button_height),
            y=-0.25,
            color=color.red
        )
        self.quit_button.on_click = self.quit_game
        
        # Lista de resoluciones disponibles
        self.resolutions = [
            (1280, 720),
            (1600, 900),
            (1920, 1080)
        ]
        self.current_resolution_index = 0
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_menu.visible = self.is_paused
        
        # Desactivar/activar el control del jugador
        self.player.enabled = not self.is_paused
        
        # Mostrar/ocultar el cursor
        mouse.locked = not self.is_paused
        
    def toggle_fullscreen(self):
        window.fullscreen = not window.fullscreen
        
    def cycle_resolution(self):
        self.current_resolution_index = (self.current_resolution_index + 1) % len(self.resolutions)
        new_resolution = self.resolutions[self.current_resolution_index]
        window.size = new_resolution
        self.resolution_button.text = f'Resolution: {new_resolution[0]}x{new_resolution[1]}'
        
    def restart_game(self):
        self.current_floor = 1
        self.setup_maze()
        self.player.position = self.maze.get_player_start_position()
        self.setup_minimap()
        self.toggle_pause()
        
    def quit_game(self):
        application.quit()
    
    def input(self, key):
        if key == 'escape':
            self.toggle_pause()

    def update_task(self, task):
        if not self.is_paused:
            self.game_update()
        return task.cont

    def setup_window(self):
        window.borderless = False
        window.fullscreen = False
        window.fps_counter.enabled = True
        window.exit_button.visible = False
        camera.fov = 90

    def setup_maze(self):
        self.maze = Maze(
            width=21,
            height=21,
            cell_size=8,
            theme_manager=self.theme_manager,
            floor_number=self.current_floor
        )
        self.maze_entities = self.maze.create_maze_entities()

    def setup_player(self):
        self.player = CustomFirstPersonController()
        self.player.position = self.maze.get_player_start_position()

    def setup_minimap(self):
        self.minimap_container = Entity(parent=camera.ui)
        self.minimap_container.position = Vec2(0.73, 0.35)
        self.minimap_container.scale = Vec2(0.25, 0.25)
        cell_w = 1.0 / self.maze.width
        cell_h = 1.0 / self.maze.height        
        self.minimap_cells = []
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                ui_x = -0.5 + cell_w/2 + x * cell_w
                ui_y = 0.5 - cell_h/2 - y * cell_h
                cell_color = color.white if self.maze.maze[y][x] == 1 else color.black
                cell = Entity(
                    parent=self.minimap_container,
                    model='quad',
                    position=(ui_x, ui_y),
                    scale=(cell_w, cell_h),
                    color=cell_color,
                    double_sided=True
                )
                self.minimap_cells.append(cell)
        self.player_marker = Entity(
            parent=self.minimap_container,
            model='circle',
            color=color.azure,
            scale=(max(cell_w, cell_h) * 0.8, max(cell_w, cell_h) * 0.8),
            z=-0.01
        )
        self.cell_w = cell_w  # Guardar el ancho de la celda
        self.cell_h = cell_h  # Guardar la altura de la celda

    def setup_sky(self):
        Sky()

    def reset_player(self):
        print("🏃‍♂️ Regresando al inicio...")
        self.player.position = self.maze.get_player_start_position()

    def check_traps(self):
        for trap in self.maze_entities['traps']:
            # Calculamos la distancia entre el jugador y la trampa
            distance = (self.player.position - trap.position).length()
            if distance < self.maze.cell_size * 0.4:  # Ajusta este valor según necesites
                print(f"✅ Trampa activada en {trap.position}")
                trap.animate_position(trap.position + Vec3(0, -0.1, 0), duration=0.2, curve=curve.linear)
                self.reset_player()
                return

    def update_minimap(self):
        # Calcular la posición del jugador en coordenadas del laberinto
        px = int((self.player.position.x + self.maze.cell_size/2) / self.maze.cell_size)
        py = int((self.player.position.z + self.maze.cell_size/2) / self.maze.cell_size)
        
        # Asegurar que las coordenadas estén dentro de los límites
        px = clamp(px, 0, self.maze.width - 1)
        py = clamp(py, 0, self.maze.height - 1)
        
        # Convertir a coordenadas UI para el minimapa
        ui_x = -0.5 + self.cell_w/2 + px * self.cell_w
        ui_y = 0.5 - self.cell_h/2 - py * self.cell_h
        
        # Actualizar la posición del marcador del jugador
        if hasattr(self, 'player_marker'):
            self.player_marker.position = Vec3(ui_x, ui_y, -0.01)

    def check_exit(self):
        px = int((self.player.position.x + self.maze.cell_size/2) / self.maze.cell_size)
        py = int((self.player.position.z + self.maze.cell_size/2) / self.maze.cell_size)
        if (px, py) == self.maze.exit:
            print("🎯 ¡Has llegado a la salida!")
            self.next_floor()

    def next_floor(self):
        # Destruir entidades del piso actual
        for entity_group in self.maze_entities.values():
            if isinstance(entity_group, list):
                for entity in entity_group:
                    destroy(entity)
            else:
                destroy(entity_group)
        
        # Limpiar el minimapa
        for cell in self.minimap_cells:
            destroy(cell)
        self.minimap_cells.clear()
        destroy(self.player_marker)
        
        # Incrementar el número de piso
        self.current_floor += 1
        
        # Generar nuevo piso
        self.setup_maze()
        self.player.position = self.maze.get_player_start_position()
        self.setup_minimap()
        
        print(f"🆙 Avanzando al piso {self.current_floor}")

    def game_update(self):
        self.check_traps()
        self.update_minimap()
        self.check_exit()

    def run(self):
        print("🎮 Iniciando el juego...")
        self.app.run()

if __name__ == '__main__':
    game = MazeGame()
    game.run()