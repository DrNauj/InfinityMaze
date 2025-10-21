from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

class ItemType(Enum):
    WEAPON = "Arma"
    ARMOR = "Armadura"
    JEWELRY = "Joyería"

class ItemRarity(Enum):
    COMMON = ("Común", 1.0)
    UNCOMMON = ("Poco común", 1.5)
    RARE = ("Raro", 2.0)
    EPIC = ("Épico", 2.5)
    LEGENDARY = ("Legendario", 3.0)

    def __init__(self, label: str, multiplier: float):
        self.label = label
        self.multiplier = multiplier

class StatusEffect(Enum):
    POISON = "Veneno"  # DOT: 5% HP por turno
    BLEEDING = "Sangrado"  # DOT: 3% HP por turno + acumulable
    STUN = "Aturdimiento"  # 20% chance de perder turno
    BURN = "Quemadura"  # DOT: 4% HP por turno + reduce defensa
    FREEZE = "Congelación"  # Reduce velocidad y precisión
    SHOCK = "Electrocución"  # Reduce precisión y chance de crítico

@dataclass
class Enchantment:
    attack_bonus: float = 0  # Porcentaje adicional
    defense_bonus: float = 0  # Porcentaje adicional
    penetration_bonus: float = 0  # Puntos adicionales
    immunity_bonus: float = 0  # Puntos adicionales
    effects: List[StatusEffect] = None
    
    def __post_init__(self):
        if self.effects is None:
            self.effects = []
        # Asegurar que los bonus no excedan el 10%
        self.attack_bonus = min(10, max(0, self.attack_bonus))
        self.defense_bonus = min(10, max(0, self.defense_bonus))
        self.penetration_bonus = min(10, max(0, self.penetration_bonus))
        self.immunity_bonus = min(10, max(0, self.immunity_bonus))

@dataclass
class Item:
    name: str
    item_type: ItemType
    level: int
    rarity: ItemRarity
    attack: int = 0
    defense: int = 0
    critical: float = 0  # Porcentaje de crítico
    accuracy: float = 0  # Porcentaje de precisión
    penetration: float = 0  # Porcentaje de penetración de defensa
    immunity: float = 0  # Porcentaje de inmunidad al daño
    enchantment: Optional[Enchantment] = None
    upgrade_level: int = 0
    max_upgrade_level: int = 10

    def __post_init__(self):
        if self.item_type == ItemType.ARMOR:
            self.attack = 0
        if not self.enchantment:
            self.enchantment = Enchantment()

    @property
    def total_attack(self) -> float:
        base = self.attack * (1 + self.enchantment.attack_bonus / 100)
        return base * (1 + 0.1 * self.upgrade_level)

    @property
    def total_defense(self) -> float:
        base = self.defense * (1 + self.enchantment.defense_bonus / 100)
        return base * (1 + 0.1 * self.upgrade_level)

    @property
    def total_penetration(self) -> float:
        return self.penetration + self.enchantment.penetration_bonus

    @property
    def total_immunity(self) -> float:
        return self.immunity + self.enchantment.immunity_bonus

class Smith:
    @staticmethod
    def create_weapon(name: str, level: int, rarity: ItemRarity) -> Item:
        base_stats = Smith._calculate_base_stats(level, rarity)
        return Item(
            name=name,
            item_type=ItemType.WEAPON,
            level=level,
            rarity=rarity,
            attack=base_stats['attack'],
            critical=base_stats['critical'],
            accuracy=base_stats['accuracy'],
            penetration=base_stats['penetration']
        )

    @staticmethod
    def create_armor(name: str, level: int, rarity: ItemRarity) -> Item:
        base_stats = Smith._calculate_base_stats(level, rarity)
        return Item(
            name=name,
            item_type=ItemType.ARMOR,
            level=level,
            rarity=rarity,
            defense=base_stats['defense'],
            immunity=base_stats['immunity']
        )

    @staticmethod
    def create_jewelry(name: str, level: int, rarity: ItemRarity) -> Item:
        base_stats = Smith._calculate_base_stats(level, rarity)
        return Item(
            name=name,
            item_type=ItemType.JEWELRY,
            level=level,
            rarity=rarity,
            critical=base_stats['critical'],
            accuracy=base_stats['accuracy'],
            penetration=base_stats['penetration'] * 0.5,
            immunity=base_stats['immunity'] * 0.5
        )

    @staticmethod
    def _calculate_base_stats(level: int, rarity: ItemRarity) -> Dict:
        rarity_multiplier = rarity.multiplier
        return {
            'attack': int(level * 5 * rarity_multiplier),
            'defense': int(level * 3 * rarity_multiplier),
            'critical': min(5 + (level * 0.5 * rarity_multiplier), 50),
            'accuracy': 75 + min(level * 0.3 * rarity_multiplier, 20),
            'penetration': min(level * 0.2 * rarity_multiplier, 30),
            'immunity': min(level * 0.2 * rarity_multiplier, 30)
        }

    @staticmethod
    def upgrade_item(item: Item, success_chance: float = 0.7) -> bool:
        if item.upgrade_level >= item.max_upgrade_level:
            return False

        # La probabilidad disminuye con cada nivel
        actual_chance = success_chance * (1 - item.upgrade_level / 20)
        
        if random.random() < actual_chance:
            item.upgrade_level += 1
            return True
        return False

    @staticmethod
    def apply_enchantment(item: Item, enchantment: Enchantment) -> bool:
        if item.enchantment and len(item.enchantment.effects) > 0:
            return False
        item.enchantment = enchantment
        return True

    @staticmethod
    def generate_random_enchantment(item_level: int, rarity: ItemRarity) -> Enchantment:
        power = item_level * rarity.multiplier * 0.1
        
        return Enchantment(
            attack_bonus=random.uniform(0, min(10, power * 2)),
            defense_bonus=random.uniform(0, min(10, power * 2)),
            penetration_bonus=random.uniform(0, min(5, power)),
            immunity_bonus=random.uniform(0, min(5, power)),
            effects=[random.choice(list(StatusEffect))] if random.random() < 0.3 else []
        )

# Ejemplo de uso
if __name__ == "__main__":
    # Crear una espada
    sword = Smith.create_weapon("Espada de Fuego", level=10, rarity=ItemRarity.EPIC)
    
    # Aplicar encantamiento
    enchant = Smith.generate_random_enchantment(sword.level, sword.rarity)
    Smith.apply_enchantment(sword, enchant)
    
    # Mejorar el arma
    success = Smith.upgrade_item(sword)
    print(f"Mejora exitosa: {success}")
    print(f"Nivel de mejora actual: {sword.upgrade_level}")
    print(f"Daño total: {sword.total_attack}")
    print(f"Penetración total: {sword.total_penetration}")
