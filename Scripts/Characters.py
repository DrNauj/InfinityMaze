from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

class HealthBar(Entity):
    def __init__(self, target, offset=Vec2(0,0), **kwargs):
        super().__init__(
            parent=camera.ui,
            model='quad',
            scale=(.4, .025),
            color=color.red,
            position=(-0.65 + offset.x, 0.45 + offset.y),
            **kwargs
        )
        
        self.target = target  # Asignamos el target primero
        
        # Fondo negro de la barra
        self.background = Entity(
            parent=self,
            model='quad',
            scale=(1, 1),
            color=color.black,
            z=0.01
        )
        
        # Marco de la barra
        self.border = Entity(
            parent=self,
            model='quad',
            scale=(1.02, 1.2),
            color=color.light_gray,
            z=0.02
        )
        
        # Barra de vida actual
        self.health_indicator = Entity(
            parent=self,
            model='quad',
            scale=(1, 0.9),
            color=color.red,
            origin_x=-0.5,  # Origen en la izquierda
            x=-0.5         # Alineado a la izquierda
        )
        
        # Texto para mostrar vida
        self.text = Text(
            parent=self,
            text=f'{int(self.target.health)}/{int(self.target.max_health)}',
            position=(0, -0.8),
            origin=(0,0),
            color=color.white
        )
        
    def update(self):
        # Actualizar barra según porcentaje de vida
        health_ratio = self.target.health / self.target.max_health
        self.health_indicator.scale_x = health_ratio
        self.text.text = f'{int(self.target.health)}/{int(self.target.max_health)}'

class Player(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = 100
        self.max_health = 100
        self.cursor = Entity(parent=camera.ui, model='quad', color=color.white, scale=.008)
        self.health_bar = HealthBar(self)
        
        # Crear modelo del cuerpo (visible al mirar abajo)
        self.body = Entity(
            parent=self,
            model='cube',
            scale=(0.5, 0.5, 0.5),
            position=(0, -1, 0),
            color=color.blue
        )
        
    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.die()
            
    def die(self):
        print("¡Has muerto!")
        self.disable()

class HumanoidEnemy(Entity):
    def __init__(self, position=Vec3(0,0,0), **kwargs):
        super().__init__(
            position=position + Vec3(0,1.5,0),  # Ajustamos la altura inicial
            **kwargs
        )
        
        self.health = 100
        self.max_health = 100
        self.attack_range = 2
        self.attack_damage = 10
        self.attack_cooldown = 1
        self.last_attack = 0
        
        # Cuerpo principal
        self.torso = Entity(
            parent=self,
            model='cube',
            scale=(0.5, 0.8, 0.4),  # Ajustamos el tamaño del torso
            y=0,  # Ajustamos la posición vertical del torso
            color=color.red,
            collider='box'
        )
        
        # Cabeza
        self.head = Entity(
            parent=self.torso,
            model='cube',
            scale=(0.5, 0.5, 0.5),  # Ajustamos el tamaño de la cabeza
            y=0.75,  # Ajustamos la posición vertical de la cabeza
            color=color.red
        )
        
        # Brazos
        self.arm_right = Entity(
            parent=self.torso,
            model='cube',
            scale=(0.2, 1.2, 0.2),  # Ajustamos el tamaño de los brazos
            x=0.6,  # Ajustamos la posición horizontal para que estén más separados
            y=0.4,  # Ajustamos la posición vertical
            origin_y=0.4,  # Ajustamos el eje de rotación al top
            color=color.red
        )
        
        self.arm_left = Entity(
            parent=self.torso,
            model='cube',
            scale=(0.2, 1.2, 0.2),
            x=-0.6,
            y=0.4,
            origin_y=0.4,
            color=color.red
        )
        
        # Piernas
        self.leg_right = Entity(
            parent=self,
            model='cube',
            scale=(0.2, 1.6, 0.2),  # Ajustamos el tamaño de las piernas
            x=0.15,
            y=-0.5,  # Ajustamos la posición vertical
            z=0.1,  # Ajustamos la posición para que se vea más natural
            origin_y=0.4,  # Ajustamos el eje de rotación al top
            color=color.red
        )
        
        self.leg_left = Entity(
            parent=self,
            model='cube',
            scale=(0.2, 1.6, 0.2),
            x=-0.15,
            y=-0.5,
            z=0.1,
            origin_y=0.4,
            color=color.red
        )
        
        # Barra de vida ajustada
        self.health_bar = HealthBar(self, offset=Vec2(0, -0.1))

    def update(self):
        # Animación simple de balanceo al caminar
        if hasattr(self, 'target'):
            t = time.time() * 4
            self.arm_right.rotation_x = math.sin(t) * 30
            self.arm_left.rotation_x = -math.sin(t) * 30
            self.leg_right.rotation_x = -math.sin(t) * 30
            self.leg_left.rotation_x = math.sin(t) * 30

        if not hasattr(self, 'target'):
            # Buscar jugador
            player = next((e for e in scene.entities if isinstance(e, Player)), None)
            if player:
                self.target = player
            return
            
        if self.target:
            self.look_at_2d(self.target.position)
            dist = distance_xz(self.position, self.target.position)
            
            if dist <= self.attack_range:
                current_time = time.time()
                if current_time - self.last_attack >= self.attack_cooldown:
                    self.attack()
                    
    def look_at_2d(self, target_pos):
        # Rotar solo en el eje Y
        direction = Vec3(
            target_pos.x - self.position.x,
            0,
            target_pos.z - self.position.z
        ).normalized()
        self.look_at(self.position + direction)
                    
    def attack(self):
        self.last_attack = time.time()
        if hasattr(self, 'target'):
            dist = distance_xz(self.position, self.target.position)
            if dist <= self.attack_range:
                self.target.take_damage(self.attack_damage)
                # Animación de ataque ajustada
                self.arm_right.animate_rotation((90,0,0), duration=0.1)
                invoke(self.reset_attack_animation, delay=0.2)
                
    def reset_attack_animation(self):
        self.arm_right.animate_rotation((0,0,0), duration=0.1)
        
    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.die()
            
    def die(self):
        destroy(self)

def distance_xz(pos1, pos2):
    """Calcula distancia ignorando eje Y"""
    return ((pos1.x - pos2.x)**2 + (pos1.z - pos2.z)**2)**0.5