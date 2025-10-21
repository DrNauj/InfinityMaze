from ursina import *
from Characters import HumanoidEnemy, Player

class CombatTest:
    def __init__(self):
        # Configuración básica
        window.title = 'Combat Test'
        window.borderless = False
        window.fullscreen = False
        window.exit_button.visible = False
        window.fps_counter.enabled = True

        # Crear escenario
        ground = Entity(
            model='plane',
            scale=(30,1,30),
            color=color.gray,
            texture='white_cube',
            texture_scale=(30,30),
            collider='box'
        )

        # Crear paredes
        wall_1 = Entity(model='cube', scale=(30,5,1), position=(0,2.5,15), color=color.gray, collider='box')
        wall_2 = Entity(model='cube', scale=(30,5,1), position=(0,2.5,-15), color=color.gray, collider='box')
        wall_3 = Entity(model='cube', scale=(1,5,30), position=(15,2.5,0), color=color.gray, collider='box')
        wall_4 = Entity(model='cube', scale=(1,5,30), position=(-15,2.5,0), color=color.gray, collider='box')

        # Crear obstáculos
        for i in range(5):
            pillar = Entity(
                model='cube',
                scale=(2,4,2),
                position=(random.uniform(-10,10), 2, random.uniform(-10,10)),
                color=color.gray,
                collider='box'
            )

        # Crear jugador
        self.player = Player(position=(0,2,0))

        # Crear enemigos
        self.enemies = []
        enemy_positions = [
            Vec3(5,0,5),
            Vec3(-5,0,5),
            Vec3(5,0,-5),
            Vec3(-5,0,-5)
        ]
        
        for pos in enemy_positions:
            enemy = HumanoidEnemy(position=pos)
            self.enemies.append(enemy)

        # Iluminación
        DirectionalLight(y=2, z=3, shadows=True)
        AmbientLight(color = Vec4(0.5, 0.5, 0.5, 0.5))

    def input(self, key):
        if key == 'escape':
            application.quit()

if __name__ == '__main__':
    app = Ursina()
    game = CombatTest()
    app.run()