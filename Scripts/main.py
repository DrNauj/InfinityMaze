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
        self.camera_pivot.y = lerp(self.camera_pivot.y, self.target_height, time.dt * 8)

class MazeGame:
    def __init__(self, app):
        self.app = app
        self.theme_manager = TextureTheme()
        self.current_floor = 1
        self.is_paused = False
        
        # Configuración de pantalla
        self.screen_modes = ['Ventana', 'Completa', 'Sin Bordes']
        self.current_screen_mode = 0
        self.resolutions = ['1280x720', '1366x768', '1600x900', '1920x1080']
        self.current_resolution_index = 0
        
        # Variables para controlar listas desplegables
        self.dropdown_visible = None  # 'screen' o 'resolution'
        
        # Precarga
        self.preloaded_floors = {}

        # Setup inicial
        self.setup_window()
        self.preload_floors()
        self.setup_maze()
        self.setup_player()
        self.setup_minimap()
        self.setup_sky_and_lighting()
        self.setup_pause_menu()

        # Controles
        self.app.accept('escape', self.toggle_pause)
        self.app.accept('page_up', self.next_floor)
        self.app.accept('page_down', self.prev_floor)

        # Game loop
        self.app.taskMgr.add(self.update_task, "update_task")

    def safe_destroy(self, obj):
        try:
            if obj is None:
                return
            destroy(obj)
        except Exception:
            pass

    def show_message(self, text, duration=2):
        if getattr(self, 'message_text', None) is not None:
            self.safe_destroy(self.message_text)
        self.message_text = Text(
            text=text,
            parent=camera.ui,
            position=(0, 0.4),
            origin=(0, 0),
            color=color.white,
            scale=2
        )
        invoke(self.safe_destroy, self.message_text, delay=duration)

    def setup_window(self):
        window.borderless = False
        window.fullscreen = False
        window.fps_counter.enabled = True
        camera.fov = 90
        window.vsync = False
        scene.shader = None

    def setup_sky_and_lighting(self):
        Sky()
        scene.fog_color = color.black
        scene.fog_density = 0.18
        scene.ambient_color = color.rgba(0.09, 0.09, 0.09, 1)
        
        if getattr(self, 'player', None) is not None:
            self.player_light = PointLight(parent=self.player, color=color.white, position=(0,2,0), radius=18, shadows=True)

    def preload_floors(self):
        floor_min = max(1, self.current_floor - 2)
        floor_max = self.current_floor + 2
        
        for f in range(floor_min, floor_max + 1):
            if f not in self.preloaded_floors:
                self.preloaded_floors[f] = Maze(width=21, height=21, cell_size=8,
                                                theme_manager=self.theme_manager, floor_number=f)
        
        for f in list(self.preloaded_floors.keys()):
            if f < floor_min or f > floor_max:
                del self.preloaded_floors[f]

    def setup_maze(self):
        self.maze = self.preloaded_floors.get(self.current_floor)
        if self.maze is None:
            self.maze = Maze(width=21, height=21, cell_size=8, theme_manager=self.theme_manager, floor_number=self.current_floor)
            self.preloaded_floors[self.current_floor] = self.maze
        self.maze_entities = self.maze.create_maze_entities()

    def setup_player(self):
        self.player = CustomFirstPersonController(maze=self.maze)
        self.player.position = self.maze.get_player_start_position()

    def setup_minimap(self):
        self.safe_destroy(getattr(self, 'minimap_container', None))
        self.safe_destroy(getattr(self, 'minimap_bg', None))
        self.safe_destroy(getattr(self, 'player_marker', None))
        self.safe_destroy(getattr(self, 'floor_text', None))

        self.minimap_bg = Entity(parent=camera.ui, model='quad', position=Vec2(0.73, 0.35),
                                 scale=Vec2(0.25, 0.25), color=color.black50, z=0.1)
        self.minimap_container = Entity(parent=camera.ui)
        self.minimap_container.position = Vec2(0.73, 0.35)
        self.minimap_container.scale = Vec2(0.25, 0.25)

        cell_w = 1.0 / self.maze.width
        cell_h = 1.0 / self.maze.height
        self.minimap_cells = []
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                ui_x = 0.5 - cell_w/2 - x * cell_w
                ui_y = 0.5 - cell_h/2 - y * cell_h
                cell_color = color.rgba(1, 1, 1, 0.4) if self.maze.maze[y][x] == 1 else color.rgba(0, 0, 0, 0.3)
                cell = Entity(parent=self.minimap_container, model='quad', position=(ui_x, ui_y),
                              scale=(cell_w, cell_h), color=cell_color, double_sided=True)
                self.minimap_cells.append(cell)

        self.player_marker = Entity(parent=self.minimap_container, model='circle',
                                   color=color.rgb(0, 157, 255),
                                   scale=(max(cell_w, cell_h) * 0.8, max(cell_w, cell_h) * 0.8),
                                   z=-0.01)
        self.cell_w = cell_w
        self.cell_h = cell_h

        self.floor_text = Text(text=f'Piso {self.current_floor}', parent=camera.ui, position=(0.73, 0.2),
                               origin=(0, 0), color=color.white, scale=1.5)

    def update_minimap(self):
        if not hasattr(self, 'player'):
            return
        
        px = int((self.player.position.x + self.maze.cell_size/2) / self.maze.cell_size)
        py = int((self.player.position.z + self.maze.cell_size/2) / self.maze.cell_size)
        px = clamp(px, 0, self.maze.width - 1)
        py = clamp(py, 0, self.maze.height - 1)
        
        ui_x = 0.5 - self.cell_w/2 - px * self.cell_w
        ui_y = 0.5 - self.cell_h/2 - py * self.cell_h
        
        if getattr(self, 'player_marker', None) is not None:
            self.player_marker.position = Vec3(ui_x, ui_y, -0.01)

    # NUEVO SISTEMA DE MENÚ CORREGIDO
    def setup_pause_menu(self):
        """Crea el menú de pausa con sistema mejorado de listas desplegables"""
        # Limpiar menú anterior
        self.safe_destroy(getattr(self, 'pause_menu', None))
        self.safe_destroy(getattr(self, 'dropdown_container', None))
        
        # Crear menú principal
        self.pause_menu = Entity(parent=camera.ui, model='quad', 
                               scale=(0.7, 0.85), color=color.rgba(0.1, 0.1, 0.2, 0.95),
                               visible=False)

        # Contenedor para listas desplegables (con alto z-index)
        self.dropdown_container = Entity(parent=camera.ui, z=-1)
        
        # Botón de cerrar (X) en esquina superior derecha
        self.close_btn = Button(parent=self.pause_menu, text='X',
                              scale=(0.08, 0.08), position=(0.45, 0.45),
                              color=color.rgba(0.1, 0.1, 0.2, 0.95))
        self.close_btn.on_click = self.toggle_pause

        # Título
        Text("MENÚ", parent=self.pause_menu, position=(-0.1, 0.3), scale=2.5, color=color.white)

        # Botón Reiniciar partida
        self.restart_btn = Button(parent=self.pause_menu, text='Reiniciar partida',
                                scale=(0.5, 0.08), position=(0, 0.15),
                                color=color.orange)
        self.restart_btn.on_click = self.restart_game

        # Configuración de pantalla
        screen_label = Text("Pantalla:", parent=self.pause_menu, 
                          position=(-0.2, 0.02), scale=1.2, color=color.white)
        screen_label.origin = (-0.5, 0)
        
        current_screen = self.screen_modes[self.current_screen_mode]
        self.screen_btn = Button(parent=self.pause_menu, text=current_screen,
                               scale=(0.3, 0.06), position=(0.15, 0.02),
                               color=color.blue)
        self.screen_btn.on_click = lambda: self.toggle_dropdown('screen')

        # Configuración de resolución
        res_label = Text("Resolución:", parent=self.pause_menu, 
                       position=(-0.2, -0.08), scale=1.2, color=color.white)
        res_label.origin = (-0.5, 0)
        
        current_res = self.resolutions[self.current_resolution_index]
        self.res_btn = Button(parent=self.pause_menu, text=current_res,
                            scale=(0.3, 0.06), position=(0.15, -0.08),
                            color=color.blue)
        self.res_btn.on_click = lambda: self.toggle_dropdown('resolution')

        # Botón Salir del juego
        self.quit_btn = Button(parent=self.pause_menu, text='Salir del juego',
                             scale=(0.35, 0.08), position=(0, -0.20),
                             color=color.red)
        self.quit_btn.on_click = self.quit_game

        # Botones Restaurar y Aplicar
        self.restore_btn = Button(parent=self.pause_menu, text='Restaurar',
                                scale=(0.2, 0.07), position=(-0.38, -0.45),
                                color=color.gray)
        self.restore_btn.on_click = self.restore_settings

        self.apply_btn = Button(parent=self.pause_menu, text='Aplicar',
                              scale=(0.2, 0.07), position=(0.38, -0.45),
                              color=color.green)
        self.apply_btn.on_click = self.apply_settings

    def toggle_dropdown(self, dropdown_type):
        """Maneja la visualización de listas desplegables"""
        # Si ya está visible, ocultarlo
        if self.dropdown_visible == dropdown_type:
            self.hide_dropdowns()
            return
        
        # Ocultar cualquier dropdown previo
        self.hide_dropdowns()
        
        # Mostrar el nuevo dropdown
        self.dropdown_visible = dropdown_type
        
        if dropdown_type == 'screen':
            self.create_screen_dropdown()
        elif dropdown_type == 'resolution':
            self.create_resolution_dropdown()

    def create_screen_dropdown(self):
        """Crea la lista desplegable de modos de pantalla"""
        # Fondo del dropdown
        self.screen_dropdown_bg = Entity(parent=self.dropdown_container, model='quad',
                                       scale=(0.24, 0.21), position=(0.35, -0.01),
                                       color=color.rgba(0.2, 0.2, 0.3, 0.95))
        
        # Botones de opciones
        for i, mode in enumerate(self.screen_modes):
            btn = Button(parent=self.dropdown_container, text=mode,
                       scale=(0.2, 0.05), position=(0.35, 0.05 - i*0.06),
                       color=color.rgb(0.2, 0.2, 0.3))
            btn.on_click = lambda m=mode, idx=i: self.select_screen_mode(m, idx)

    def create_resolution_dropdown(self):
        """Crea la lista desplegable de resoluciones"""
        # Fondo del dropdown
        self.res_dropdown_bg = Entity(parent=self.dropdown_container, model='quad',
                                    scale=(0.24, 0.27), position=(0.35, -0.14),
                                    color=color.rgba(0.2, 0.2, 0.3, 0.95))
        
        # Botones de opciones
        for i, res in enumerate(self.resolutions):
            btn = Button(parent=self.dropdown_container, text=res,
                       scale=(0.2, 0.05), position=(0.35, -0.05 - i*0.06),
                       color=color.rgb(0.2, 0.2, 0.3))
            btn.on_click = lambda r=res, idx=i: self.select_resolution(r, idx)

    def hide_dropdowns(self):
        """Oculta todas las listas desplegables"""
        self.dropdown_visible = None
        # Destruir todos los hijos del contenedor de dropdowns
        for child in self.dropdown_container.children:
            self.safe_destroy(child)

    def select_screen_mode(self, mode, index):
        """Seleccionar modo de pantalla"""
        self.current_screen_mode = index
        self.screen_btn.text = mode
        self.hide_dropdowns()
        self.show_message(f"Modo de pantalla: {mode}")

    def select_resolution(self, resolution, index):
        """Seleccionar resolución"""
        self.current_resolution_index = index
        self.res_btn.text = resolution
        self.hide_dropdowns()
        self.show_message(f"Resolución: {resolution}")

    def apply_settings(self):
        """Aplicar todos los cambios de configuración"""
        # Aplicar modo de pantalla
        mode = self.screen_modes[self.current_screen_mode]
        if mode == 'Completa':
            window.fullscreen = True
            window.borderless = False
        elif mode == 'Sin Bordes':
            window.fullscreen = False
            window.borderless = True
        else:  # Ventana
            window.fullscreen = False
            window.borderless = False

        # Aplicar resolución
        resolution = self.resolutions[self.current_resolution_index]
        width, height = map(int, resolution.split('x'))
        window.size = (width, height)

        self.show_message("Configuración aplicada correctamente")

    def restore_settings(self):
        """Restaurar configuración por defecto"""
        self.current_screen_mode = 0  # Ventana
        self.current_resolution_index = 0  # 1280x720
        
        if hasattr(self, 'screen_btn'):
            self.screen_btn.text = self.screen_modes[self.current_screen_mode]
        
        if hasattr(self, 'res_btn'):
            self.res_btn.text = self.resolutions[self.current_resolution_index]
        
        self.hide_dropdowns()
        self.show_message("Configuración restaurada")

    def toggle_pause(self):
        """Mostrar/ocultar menú de pausa"""
        self.is_paused = not self.is_paused
        
        # Controlar jugador y ratón
        if hasattr(self, 'player'):
            self.player.enabled = not self.is_paused
        mouse.visible = self.is_paused
        mouse.locked = not self.is_paused
        
        # Mostrar/ocultar menú
        if hasattr(self, 'pause_menu'):
            self.pause_menu.visible = self.is_paused
            self.hide_dropdowns()  # Ocultar dropdowns al abrir/cerrar menú
            
            # Animación
            if self.is_paused:
                self.pause_menu.scale = (0.01, 0.01)
                self.pause_menu.animate_scale((0.7, 0.85), duration=0.3)

    def quit_game(self):
        """Salir del juego"""
        self.show_message("¡Hasta luego!")
        invoke(application.quit, delay=1)

    def restart_game(self):
        """Reiniciar juego"""
        self.current_floor = 1
        self.preload_floors()
        self.go_to_floor(1)
        if self.is_paused:
            self.toggle_pause()
        self.show_message("Juego reiniciado")

    # Resto de funciones del juego (sin cambios)
    def check_traps(self):
        for trap in self.maze_entities.get('traps', []):
            if not trap or trap.get('activated'):
                continue
            if getattr(trap.get('button'), 'position', None) is None:
                continue
            
            distance = (self.player.position - trap['button'].position).length()
            if distance < self.maze.cell_size * 0.4:
                print(f"✅ Trampa activada en {trap['button'].position}")
                trap['activated'] = True
                
                trap['button'].animate_position(trap['button'].position + Vec3(0,-0.5,0), duration=0.2, curve=curve.linear)
                trap['button'].animate_color(color.clear, duration=0.2)
                
                if trap.get('floor_section'):
                    trap['floor_section'].animate_position(trap['floor_section'].position + Vec3(0,-2,0), duration=0.3, curve=curve.linear)
                    trap['floor_section'].animate_color(color.clear, duration=0.3)
                    invoke(self.safe_destroy, trap.get('floor_section'), delay=0.4)
                
                if trap.get('hole'):
                    trap['hole'].position = trap['button'].position + Vec3(0,-0.5,0)
                    trap['hole'].visible = True
                    trap['hole'].color = color.black66
                
                invoke(self.safe_destroy, trap.get('button'), delay=0.3)
                return

    def check_player_boundaries(self):
        if not self.maze.check_maze_boundaries(self.player.position):
            print("⚠️ Jugador fuera de los límites o caído en trampa")
            self.reset_player()

    def check_exit(self):
        if self.maze.check_player_exit(self.player.position):
            print("🎯 ¡Has llegado a la salida!")
            self.next_floor()
            return True
        return False

    def game_update(self):
        self.check_traps()
        self.check_player_boundaries()
        self.update_minimap()
        self.check_exit()

    def update_task(self, task):
        if not self.is_paused:
            self.game_update()
        return task.cont

    def reset_player(self):
        print("Regresando al inicio...")
        invoke(self._delayed_reset, delay=0.3)

    def _delayed_reset(self):
        if getattr(self, 'player', None) is not None:
            self.player.position = self.maze.get_player_start_position()

    def go_to_floor(self, floor):
        for group in getattr(self, 'maze_entities', {}).values():
            if isinstance(group, list):
                for entity in group:
                    if isinstance(entity, dict):
                        self.safe_destroy(entity.get('button'))
                        self.safe_destroy(entity.get('hole'))
                        self.safe_destroy(entity.get('floor_section'))
                        for b in entity.get('borders', []):
                            self.safe_destroy(b)
                    else:
                        self.safe_destroy(entity)
            else:
                self.safe_destroy(group)

        for cell in getattr(self, 'minimap_cells', []):
            self.safe_destroy(cell)
        if hasattr(self, 'minimap_cells'):
            self.minimap_cells.clear()
        self.safe_destroy(getattr(self, 'player_marker', None))
        self.safe_destroy(getattr(self, 'minimap_bg', None))
        self.safe_destroy(getattr(self, 'minimap_container', None))
        self.safe_destroy(getattr(self, 'floor_text', None))

        self.current_floor = floor
        self.maze = self.preloaded_floors.get(floor)
        if self.maze is None:
            self.maze = Maze(width=21, height=21, cell_size=8, theme_manager=self.theme_manager, floor_number=floor)
            self.preloaded_floors[floor] = self.maze
            
        self.maze_entities = self.maze.create_maze_entities()
        
        if getattr(self, 'player', None) is not None:
            self.player.position = self.maze.get_player_start_position()
        self.setup_minimap()

    def next_floor(self):
        self.current_floor += 1
        self.preload_floors()
        self.go_to_floor(self.current_floor)
        self.show_message(f"Avanzando al piso {self.current_floor}")
        if getattr(self, 'floor_text', None) is not None:
            self.floor_text.text = f'Piso {self.current_floor}'

    def prev_floor(self):
        if self.current_floor > 1:
            self.current_floor -= 1
            self.preload_floors()
            self.go_to_floor(self.current_floor)
            self.show_message(f"Retrocediendo al piso {self.current_floor}")
            if getattr(self, 'floor_text', None) is not None:
                self.floor_text.text = f'Piso {self.current_floor}'
        else:
            self.show_message("Ya estás en el piso 1")

# ENTRYPOINT
if __name__ == '__main__':
    app = Ursina()
    game = MazeGame(app)
    app.run()