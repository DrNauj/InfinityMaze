from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from mazegenerator import Maze, TextureTheme

class CustomFirstPersonController(FirstPersonController):
    def __init__(self, maze, **kwargs):
        super().__init__(**kwargs)
        self.maze = maze
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
        # Restauramos la funcionalidad de agacharse
        self.camera_pivot.y = lerp(self.camera_pivot.y, self.target_height, time.dt * 8)

class MazeGame(Entity):
    def __init__(self):
        super().__init__()
        self.app = Ursina()
        self.setup_window()
        self.theme_manager = TextureTheme()
        self.current_floor = 1
        self.is_paused = False

        # Diccionario para almacenar los Maze precargados
        self.preloaded_floors = {}
        self.preload_floors()  # Pre-carga según el piso actual

        self.setup_maze()     # Usa el Maze precargado del piso actual
        self.setup_player()
        self.setup_minimap()
        self.setup_sky()
        self.setup_pause_menu()
        self.setup_lighting()  # Añadir después de setup_sky()

        # Registrar teclas: Escape para pausa, Page Up para siguiente piso, Page Down para piso anterior.
        self.app.accept('escape', self.toggle_pause)
        self.app.accept('page up', self.next_floor)
        self.app.accept('page down', self.prev_floor)

        self.app.taskMgr.add(self.update_task, "update_task")

    def preload_floors(self):
        # Determinar rango a precargar:
        # Si estamos en piso 1, precargamos 1 a 3; si no, precargamos desde max(1, current_floor-2) hasta current_floor+2.
        if self.current_floor == 1:
            floor_min = 1
            floor_max = 3
        else:
            floor_min = max(1, self.current_floor - 2)
            floor_max = self.current_floor + 2

        # Precargar los pisos en ese rango si no están en memoria
        for floor in range(floor_min, floor_max + 1):
            if floor not in self.preloaded_floors:
                self.preloaded_floors[floor] = Maze(
                    width=21,
                    height=21,
                    cell_size=8,
                    theme_manager=self.theme_manager,
                    floor_number=floor
                )
        # Eliminar pisos fuera del rango para liberar memoria
        floors_to_remove = [f for f in self.preloaded_floors if f < floor_min or f > floor_max]
        for f in floors_to_remove:
            del self.preloaded_floors[f]

    def go_to_floor(self, floor):
        # Destruir entidades del piso actual
        for group in self.maze_entities.values():
            if isinstance(group, list):
                for entity in group:
                    if isinstance(entity, dict):  # Para las trampas
                        destroy(entity['button'])
                        if 'hole' in entity:
                            destroy(entity['hole'])
                        if 'floor_section' in entity:
                            # La sección del piso ahora es directamente una Entity
                            destroy(entity['floor_section'])
                            # Destruir los bordes si existen
                            for border in entity.get('borders', []):
                                destroy(border)
                    else:
                        destroy(entity)
            else:
                destroy(group)
        
        # Limpiar el minimapa
        for cell in self.minimap_cells:
            destroy(cell)
        self.minimap_cells.clear()
        destroy(self.player_marker)
        destroy(self.minimap_bg)  # antes de crear el nuevo minimapa
        
        # Configurar nuevo piso
        self.maze = self.preloaded_floors[floor]
        self.maze_entities = self.maze.create_maze_entities()
        self.player.position = self.maze.get_player_start_position()
        self.setup_minimap()

    def next_floor(self):
        self.current_floor += 1
        self.preload_floors()
        self.go_to_floor(self.current_floor)
        print(f"🆙 Avanzando al piso {self.current_floor}")

    def prev_floor(self):
        if self.current_floor > 1:
            self.current_floor -= 1
            self.preload_floors()
            self.go_to_floor(self.current_floor)
            print(f"⬇️ Retrocediendo al piso {self.current_floor}")
        else:
            print("⚠️ Ya estás en el piso 1.")

    def restart_game(self):
        self.current_floor = 1
        self.preload_floors()
        self.go_to_floor(1)
        self.toggle_pause()
        print("🔄 Juego reiniciado: piso 1.")

    def setup_pause_menu(self):
        self.pause_menu = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.4, 0.6),
            color=color.black66,
            visible=False
        )
        Text("PAUSE MENU", parent=self.pause_menu, y=0.2, scale=2, origin=(0, 0))
        button_width = 0.3
        button_height = 0.05

        self.fullscreen_button = Button(
            parent=self.pause_menu,
            text='Toggle Fullscreen',
            scale=(button_width, button_height),
            y=0.05,
            color=color.azure
        )
        self.fullscreen_button.on_click = self.toggle_fullscreen

        self.resolution_button = Button(
            parent=self.pause_menu,
            text='Resolution: 1280x720',
            scale=(button_width, button_height),
            y=-0.05,
            color=color.azure
        )
        self.resolution_button.on_click = self.cycle_resolution

        self.restart_button = Button(
            parent=self.pause_menu,
            text='Restart Game',
            scale=(button_width, button_height),
            y=-0.15,
            color=color.orange
        )
        self.restart_button.on_click = self.restart_game

        self.quit_button = Button(
            parent=self.pause_menu,
            text='Quit Game',
            scale=(button_width, button_height),
            y=-0.25,
            color=color.red
        )
        self.quit_button.on_click = self.quit_game

        self.resolutions = [(1280,720), (1600,900), (1920,1080)]
        self.current_resolution_index = 0

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_menu.visible = self.is_paused
        self.player.enabled = not self.is_paused
        mouse.visible = self.is_paused
        mouse.locked = not self.is_paused

    def toggle_fullscreen(self):
        window.fullscreen = not window.fullscreen

    def cycle_resolution(self):
        self.current_resolution_index = (self.current_resolution_index + 1) % len(self.resolutions)
        new_res = self.resolutions[self.current_resolution_index]
        window.size = new_res
        self.resolution_button.text = f'Resolution: {new_res[0]}x{new_res[1]}'

    def quit_game(self):
        application.quit()

    def update_task(self, task):
        if not self.is_paused:
            self.game_update()
        return task.cont

    def setup_window(self):
        window.borderless = False
        window.fullscreen = False
        window.fps_counter.enabled = True
        camera.fov = 90
        window.vsync = False
        window.fps_counter.enabled = True
        camera.fov = 90
        
        # Activar el modo de iluminación avanzada
        from ursina.shaders import lit_with_shadows_shader
        scene.shader = lit_with_shadows_shader

    def setup_maze(self):
        # Usa el Maze precargado para el piso actual
        self.maze = self.preloaded_floors[self.current_floor]
        self.maze_entities = self.maze.create_maze_entities()

    def setup_player(self):
        self.player = CustomFirstPersonController(maze=self.maze)
        self.player.position = self.maze.get_player_start_position()

    def setup_minimap(self):
        # Crear un fondo semitransparente para el minimapa
        self.minimap_bg = Entity(
            parent=camera.ui,
            model='quad',
            position=Vec2(0.73, 0.35),
            scale=Vec2(0.25, 0.25),
            color=color.black50,  # Color negro con 50% de transparencia
            z=0.1
        )

        self.minimap_container = Entity(parent=camera.ui)
        self.minimap_container.position = Vec2(0.73, 0.35)
        self.minimap_container.scale = Vec2(0.25, 0.25)
        cell_w = 1.0 / self.maze.width
        cell_h = 1.0 / self.maze.height
        self.minimap_cells = []
        
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                # Invertir la coordenada X para las celdas
                ui_x = 0.5 - cell_w/2 - x * cell_w
                ui_y = 0.5 - cell_h/2 - y * cell_h
                cell_color = color.rgba(1, 1, 1, 0.4) if self.maze.maze[y][x] == 1 else color.rgba(0, 0, 0, 0.3)
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
            color=color.rgb(0, 157, 255),  # Azul sólido
            scale=(max(cell_w, cell_h) * 0.8, max(cell_w, cell_h) * 0.8),
            z=-0.01
        )
        self.cell_w = cell_w
        self.cell_h = cell_h

    def setup_sky(self):
        Sky()

    def setup_lighting(self):
        # Configurar la niebla para oscurecer el ambiente
        scene.fog_color = color.black
        scene.fog_density = 0.18  # Aumentado para más oscuridad
        
        # Crear luz puntual que seguirá al jugador
        self.player_light = PointLight(
            parent=self.player,
            color=color.white,
            position=(0, 2, 0),
            radius=18,           # Reducido para menos visibilidad
            shadows=True
        )
        
        # Reducir aún más la luz ambiental
        scene.ambient_color = color.rgba(0.09, 0.09, 0.09, 1)

    def reset_player(self):
        print("🏃‍♂️ Regresando al inicio...")
        # Añadir una pequeña pausa antes de reiniciar
        invoke(self._delayed_reset, delay=0.3)
    
    def _delayed_reset(self):
        self.player.position = self.maze.get_player_start_position()

    def check_traps(self):
        for trap in self.maze_entities['traps']:
            if not trap or trap['activated']:
                continue
                
            distance = (self.player.position - trap['button'].position).length()
            if distance < self.maze.cell_size * 0.4:
                print(f"✅ Trampa activada en {trap['button'].position}")
                
                # Activar la trampa
                trap['activated'] = True
                
                # Animar y destruir el botón
                trap['button'].animate_position(
                    trap['button'].position + Vec3(0, -0.5, 0),
                    duration=0.2,
                    curve=curve.linear
                )
                trap['button'].animate_color(color.clear, duration=0.2)
                
                # Animar y destruir solo la sección central del piso
                if trap['floor_section']:
                    # Animar la sección central
                    trap['floor_section'].animate_position(
                        trap['floor_section'].position + Vec3(0, -2, 0),
                        duration=0.3,
                        curve=curve.linear
                    )
                    trap['floor_section'].animate_color(color.clear, duration=0.3)
                    invoke(destroy, trap['floor_section'], delay=0.4)
                
                # Hacer visible el hoyo
                trap['hole'].position = trap['button'].position + Vec3(0, -0.5, 0)
                trap['hole'].visible = True
                trap['hole'].color = color.black66
                
                # Programar la destrucción del botón
                invoke(destroy, trap['button'], delay=0.3)
                
                return
    def check_player_boundaries(self):
        if not self.maze.check_maze_boundaries(self.player.position):
            print("⚠️ Jugador fuera de los límites o caído en trampa")
            self.reset_player()

    def update_minimap(self):
        px = int((self.player.position.x + self.maze.cell_size/2) / self.maze.cell_size)
        py = int((self.player.position.z + self.maze.cell_size/2) / self.maze.cell_size)
        px = clamp(px, 0, self.maze.width - 1)
        py = clamp(py, 0, self.maze.height - 1)
        # Invertir la coordenada X para corregir el efecto espejo
        ui_x = 0.5 - self.cell_w/2 - px * self.cell_w
        ui_y = 0.5 - self.cell_h/2 - py * self.cell_h
        if hasattr(self, 'player_marker'):
            self.player_marker.position = Vec3(ui_x, ui_y, -0.01)

    def check_exit(self):
        if self.maze.check_player_exit(self.player.position):
            print("🎯 ¡Has llegado a la salida!")
            self.next_floor()  # Esto ya debería funcionar correctamente
            return True
        return False

    def game_update(self):
        self.check_traps()
        self.check_player_boundaries()
        self.update_minimap()
        self.check_exit()

    def run(self):
        print("🎮 Iniciando el juego...")
        self.app.run()

if __name__ == '__main__':
    game = MazeGame()
    game.run()
