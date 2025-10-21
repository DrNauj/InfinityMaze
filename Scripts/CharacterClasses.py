import random
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

class EquipmentSlot(Enum):
    RIGHT_HAND = 'Mano derecha'
    LEFT_HAND = 'Mano izquierda'
    CHEST = 'Pecho'
    GLOVES = 'Guantes'
    BOOTS = 'Botas'

class EquipmentType(Enum):
    WEAPON = 'Arma'
    ARMOR = 'Armadura'
    SHIELD = "Escudo"

class EquipmentRarity(Enum):
    COMMON = ('Común', 1.0)
    UNCOMMON = ('Poco común', 1.5)
    RARE = ('Raro', 2.0)
    EPIC = ('Épico', 2.5)
    LEGENDARY = ('Legendario', 3.0)

    def __init__(self, label, drop_multiplier):
        self.label = label
        self.drop_multiplier = drop_multiplier

@dataclass
class EquipmentStats:
    attack: int = 0
    defense: int = 0

    def __add__(self, other):
        return EquipmentStats(
            attack=self.attack + other.attack,
            defense=self.defense + other.defense
        )

class Equipment:
    def __init__(
        self, 
        name: str,
        equipment_type: EquipmentType,
        rarity: EquipmentRarity,
        valid_slots: List[EquipmentSlot],
        stats: EquipmentStats,
        max_durability: int,
        base_drop_chance: float = 0.1,
        skills: Optional[Dict[str, int]] = None
    ):
        self.name = name
        self.equipment_type = equipment_type
        self.rarity = rarity
        self.valid_slots = valid_slots
        self.stats = stats
        self.max_durability = max_durability
        self.current_durability = max_durability
        self.base_drop_chance = base_drop_chance
        self.skills = skills if skills is not None else {}
        
    @property
    def drop_chance(self) -> float:
        return self.base_drop_chance * self.rarity.drop_multiplier
    
    def apply_wear(self, wear_amount: int = 1) -> bool:
        self.current_durability = max(0, self.current_durability - wear_amount)
        return self.current_durability > 0
    
    def repair(self, repair_amount: Optional[int] = None) -> None:
        if repair_amount is None:
            self.current_durability = self.max_durability
        else:
            self.current_durability = min(
                self.max_durability, 
                self.current_durability + repair_amount
            )
    
    def is_usable(self) -> bool:
        return self.current_durability > 0
    
    def __str__(self) -> str:
        durability_percent = (self.current_durability / self.max_durability) * 100
        skills_str = ", ".join(f"{skill} (Nv{level})" for skill, level in self.skills.items()) if self.skills else "Ninguna"
        return (f"{self.name} ({self.rarity.label}) - "
                f"Durabilidad: {self.current_durability}/{self.max_durability} "
                f"({durability_percent:.1f}%) | "
                f"ATK: {self.stats.attack}, DEF: {self.stats.defense} | "
                f"Habilidades: {skills_str}")

@dataclass
class SkillData:
    levels: List[float]
    unlock_level: int
    upgrade_level: Optional[int]
    priority: int  # Nuevo campo para prioridad
    phase: str  # Fase en la que se activa la skill (pre_combat, combat, post_combat)

# Diccionario global de habilidades actualizado
SKILL_TREE: Dict[str, SkillData] = {
    "haste": SkillData(
        levels=[0, 0.50, 0.50],
        unlock_level=4,
        upgrade_level=None,
        priority=1,  # Alta prioridad ya que afecta el orden de turnos
        phase="pre_combat"
    ),
    "skulk": SkillData(
        levels=[0, 0.25, 0.40],
        unlock_level=5,
        upgrade_level=None,
        priority=2,  # Se verifica después de haste pero antes del daño
        phase="combat"
    ),
    "critical_strike": SkillData(
        levels=[0, 0.30, 0.30],
        unlock_level=1,
        upgrade_level=None,
        priority=3,  # Se aplica durante el cálculo de daño
        phase="combat"
    ),
    "lifelink": SkillData(
        levels=[0, 0.10, 0.20],
        unlock_level=3,
        upgrade_level=10,
        priority=4,  # Se aplica después del daño
        phase="post_combat"
    ),
    "poison": SkillData(
        levels=[0, 0.20, 0.30],
        unlock_level=6,
        upgrade_level=None,
        priority=5,  # Se aplica después del daño normal
        phase="post_combat"
)
}

def get_sorted_skills_by_phase(phase: str) -> List[str]:
    """
    Retorna una lista de skills ordenadas por prioridad para una fase específica
    """
    return sorted(
        [skill_name for skill_name, data in SKILL_TREE.items() if data.phase == phase],
        key=lambda x: SKILL_TREE[x].priority
    )

class Character:
    def __init__(self, name: str, health: int, attack: int, defense: int) -> None:
        self.name = name
        self.health = health
        self.max_health = health
        self.attack = attack
        self.defense = defense
        self.skills: Dict[str, int] = {skill: 0 for skill in SKILL_TREE}
        self.equipment = EquipmentManager()
        self.has_priority = False

    def get_effective_skill_level(self, skill_name: str) -> int:
        """
        Calcula el nivel efectivo de una habilidad considerando todas las fuentes:
        - Nivel base del personaje
        - Niveles de cada pieza de equipo
        
        Reglas:
        1. Se usa el nivel más alto como base
        2. Por cada fuente adicional de la habilidad, se suma +0.5 niveles
        3. El resultado se redondea hacia abajo
        4. El nivel máximo está limitado por el máximo en SKILL_TREE
        """
        # Nivel base del personaje
        character_level = self.skills.get(skill_name, 0)
        
        # Recopilar todos los niveles de equipo
        equipment_levels = []
        for slot in EquipmentSlot:
            item = self.equipment.equipment[slot]
            if item and item.is_usable() and item.skills.get(skill_name, 0) > 0:
                equipment_levels.append(item.skills[skill_name])
        
        # Si no hay ninguna fuente de la habilidad, retornar 0
        if character_level == 0 and not equipment_levels:
            return 0
        
        # Calcular el nivel base (el más alto de todas las fuentes)
        base_level = max([character_level] + equipment_levels)
        
        # Contar fuentes adicionales (excluyendo la fuente del nivel más alto)
        additional_sources = len([level for level in equipment_levels if level > 0])
        if character_level > 0:
            additional_sources += 1
        additional_sources -= 1  # Restar la fuente del nivel base
        
        # Calcular el bonus por fuentes adicionales
        bonus = additional_sources * 0.5
        
        # Calcular nivel final
        final_level = int(base_level + bonus)
        
        # Limitar al máximo disponible en SKILL_TREE
        max_level = len(SKILL_TREE[skill_name].levels) - 1
        return min(final_level, max_level)

    def apply_skills_in_order(self, phase: str, **kwargs) -> Dict[str, Any]:
        """
        Aplica las skills en orden de prioridad para una fase específica
        y retorna los resultados
        
        Args:
            phase: Fase actual ('pre_combat', 'combat', 'post_combat')
            **kwargs: Argumentos adicionales necesarios para las skills
            
        Returns:
            Dict con los resultados de las skills aplicadas
        """
        results = {}
        for skill_name in get_sorted_skills_by_phase(phase):
            skill_level = self.get_effective_skill_level(skill_name)
            if skill_level > 0:
                prob = self.calculate_skill_probability(skill_name)
                if random.random() < prob:
                    # Aplicar efecto según la skill
                    if skill_name == "haste" and phase == "pre_combat":
                        results["has_priority"] = True
                    elif skill_name == "skulk" and phase == "combat":
                        results["damage_avoided"] = True
                    elif skill_name == "critical_strike" and phase == "combat":
                        results["damage_multiplier"] = 2.0
                    elif skill_name == "lifelink" and phase == "post_combat":
                        damage = kwargs.get("damage", 0)
                        results["heal_amount"] = int(damage * prob)
                    elif skill_name == "poison" and phase == "post_combat":
                        results["poison_damage"] = int(self.attack * 0.2)
                    # Registrar la activación de la skill
                    print(f"{self.name} activa {skill_name}!")
        
        return results

    def calculate_skill_probability(self, skill_name: str) -> float:
        """
        Calcula la probabilidad final de una habilidad basada en su nivel efectivo
        """
        effective_level = self.get_effective_skill_level(skill_name)
        if effective_level == 0 or skill_name not in SKILL_TREE:
            return 0.0
            
        # Usar el nivel efectivo para obtener la probabilidad de la habilidad
        return SKILL_TREE[skill_name].levels[min(effective_level, len(SKILL_TREE[skill_name].levels) - 1)]
 
    def check_haste(self) -> bool:
        """
        Verifica prioridad de turno al inicio del combate
        """
        pre_combat_results = self.apply_skills_in_order("pre_combat")
        return pre_combat_results.get("has_priority", False)
    
    def summarize_active_effects(self) -> str:
        """
        Muestra un resumen de todas las habilidades activas y sus efectos
        """
        effects = []
        for skill_name in SKILL_TREE:
            prob = self.calculate_skill_probability(skill_name)
            if prob > 0:
                effect_desc = {
                    "critical_strike": f"Golpe Crítico: {prob*100:.1f}% prob. (x2 daño)",
                    "lifelink": f"Robo de Vida: {prob*100:.1f}% del daño",
                    "skulk": f"Evasión: {prob*100:.1f}% prob.",
                    "haste": f"Prioridad: {prob*100:.1f}% prob."
                }
                effects.append(effect_desc[skill_name])
        
        return "\n".join(effects) if effects else "Sin efectos activos"

    def take_damage(self, incoming_damage: int) -> int:
        """
        Procesa el daño recibido considerando las skills defensivas
        """
        if incoming_damage <= 0:
            return 0

        # Verificar skills defensivas
        combat_results = self.apply_skills_in_order("combat")
        if combat_results.get("damage_avoided", False):
            return 0

        # Aplicar reducción por defensa
        total_defense = self.defense + self.equipment.get_total_stats().defense
        actual_damage = max(0, incoming_damage - total_defense)
        self.health = max(0, self.health - actual_damage)
        
        # Aplicar efectos post-combate
        post_combat_results = self.apply_skills_in_order("post_combat", damage=actual_damage)
        heal_amount = post_combat_results.get("heal_amount", 0)
        if heal_amount > 0:
            self.heal(heal_amount)
        
        return actual_damage

    def is_alive(self) -> bool:
        return self.health > 0

    def heal(self, amount: int) -> None:
        if amount <= 0:
            return
        self.health = min(self.max_health, self.health + amount)

    def calculate_damage(self) -> int:
        """
        Calcula el daño considerando las skills de combate
        """
        base_damage = self.attack + self.equipment.get_total_stats().attack
        
        # Aplicar skills de fase de combate
        combat_results = self.apply_skills_in_order("combat")
        
        # Aplicar multiplicadores de daño
        damage_multiplier = combat_results.get("damage_multiplier", 1.0)
        final_damage = int(base_damage * damage_multiplier)
        
        return final_damage
    
    def attack_target(self, target: 'Character') -> int:
        """
        Realiza un ataque considerando todas las habilidades activas.
        Orden de efectos:
        1. Calcular daño
        2. Target intenta evadir (skulk)
        3. Aplicar daño
        4. Efectos post-daño (lifelink)
        """
        if not self.is_alive() or not target.is_alive():
            return 0

        # 1. Calcular daño
        damage = self.calculate_damage()
        
        # 2 & 3. Target procesa el daño (incluye intento de evasión)
        damage_dealt = target.take_damage(damage)

        # 4. Aplicar efectos post-daño
        if damage_dealt > 0:
            # Lifelink
            lifelink_prob = self.calculate_skill_probability("lifelink")
            if lifelink_prob > 0:
                heal_amount = int(damage_dealt * lifelink_prob)
                if heal_amount > 0:
                    self.heal(heal_amount)
                    print(f"{self.name} recupera {heal_amount} HP gracias a Lifelink!")

        return damage_dealt
    
    def __str__(self) -> str:
        # Mejorar la visualización para mostrar las fuentes de habilidades
        active_skills = self._get_active_skills_info()
        skills_str = '\n- '.join(active_skills) if active_skills else 'Ninguna'
        return (f"{self.name}: {self.health}/{self.max_health} HP, "
                f"{self.attack} ATK, {self.defense} DEF\n"
                f"Habilidades:\n- {skills_str}")
            
    def _get_active_skills_info(self) -> List[str]:
        active_skills = []
        for skill_name in SKILL_TREE:
            sources = self._get_skill_sources(skill_name)
            if sources:
                effective_level = self.get_effective_skill_level(skill_name)
                prob = self.calculate_skill_probability(skill_name)
                sources_str = ', '.join(sources)
                active_skills.append(
                    f"{skill_name} - Nivel Efectivo: {effective_level} ({prob*100:.1f}%) "
                    f"[Fuentes: {sources_str}]"
                )
        return active_skills
    
    def _get_skill_sources(self, skill_name: str) -> List[str]:
        sources = []
        if self.skills.get(skill_name, 0) > 0:
            sources.append(f"Base(Nv{self.skills[skill_name]})")
        
        for slot in EquipmentSlot:
            item = self.equipment.equipment[slot]
            if item and item.is_usable() and item.skills.get(skill_name, 0) > 0:
                sources.append(f"{slot.value}(Nv{item.skills[skill_name]})")
        return sources

class CharacterPlayer(Character):
    def __init__(self, name: str, health: int, attack: int, defense: int, 
                 level: int = 1, experience: int = 0) -> None:
        super().__init__(name, health, attack, defense)
        self.level = level
        self.experience = experience
        self.skills["critical_strike"] = 1  # Habilidad innata
        self._check_skill_unlocks()

    def gain_experience(self, amount: int) -> None:
        if amount <= 0:
            return
            
        self.experience += amount
        while self.experience >= self.xp_to_next_level():
            self.level_up()

    def xp_to_next_level(self) -> int:
        return self.level * 100

    def level_up(self) -> None:
        self.level += 1
        self.experience = max(0, self.experience - self.xp_to_next_level())
        
        # Mejoras por nivel
        self.max_health += 10
        self.health = self.max_health
        self.attack += 2
        self.defense += 1
        
        print(f"¡{self.name} ha subido al nivel {self.level}!")
        self._check_skill_unlocks()

    def _check_skill_unlocks(self) -> None:
        for skill, data in SKILL_TREE.items():
            if self.level >= data.unlock_level and self.skills[skill] == 0:
                self.skills[skill] = 1
                print(f"¡{self.name} ha desbloqueado {skill}!")
            elif (data.upgrade_level and 
                  self.level >= data.upgrade_level and 
                  self.skills[skill] == 1):
                self.skills[skill] = 2
                print(f"¡{self.name} ha mejorado {skill}!")

# Diccionario Global de Equipamiento
EQUIPMENT_DATABASE: Dict[str, Equipment] = {
    # Armas Comunes
    "garrote": Equipment(
        "Garrote de Madera",
        EquipmentType.WEAPON,
        EquipmentRarity.COMMON,
        [EquipmentSlot.RIGHT_HAND, EquipmentSlot.LEFT_HAND],
        EquipmentStats(attack=5),
        max_durability=20,
        base_drop_chance=0.4
    ),
    "daga_oxidada": Equipment(
        "Daga Oxidada",
        EquipmentType.WEAPON,
        EquipmentRarity.COMMON,
        [EquipmentSlot.RIGHT_HAND, EquipmentSlot.LEFT_HAND],
        EquipmentStats(attack=4),
        max_durability=15,
        base_drop_chance=0.4,
        skills={"critical_strike": 1}
    ),
    
    # Armas Poco Comunes
    "espada_corta": Equipment(
        "Espada Corta",
        EquipmentType.WEAPON,
        EquipmentRarity.UNCOMMON,
        [EquipmentSlot.RIGHT_HAND],
        EquipmentStats(attack=8),
        max_durability=30,
        base_drop_chance=0.3,
        skills={"critical_strike": 1}
    ),
    "hacha_batalla": Equipment(
        "Hacha de Batalla",
        EquipmentType.WEAPON,
        EquipmentRarity.UNCOMMON,
        [EquipmentSlot.RIGHT_HAND],
        EquipmentStats(attack=10),
        max_durability=25,
        base_drop_chance=0.3
    ),
    
    # Armas Raras
    "espada_vampirica": Equipment(
        "Espada Vampírica",
        EquipmentType.WEAPON,
        EquipmentRarity.RARE,
        [EquipmentSlot.RIGHT_HAND],
        EquipmentStats(attack=12),
        max_durability=40,
        base_drop_chance=0.2,
        skills={"lifelink": 1}
    ),
    "katana_veloz": Equipment(
        "Katana del Viento",
        EquipmentType.WEAPON,
        EquipmentRarity.RARE,
        [EquipmentSlot.RIGHT_HAND],
        EquipmentStats(attack=11),
        max_durability=35,
        base_drop_chance=0.2,
        skills={"haste": 1}
    ),
    
    # Armaduras Comunes
    "armadura_cuero": Equipment(
        "Armadura de Cuero",
        EquipmentType.ARMOR,
        EquipmentRarity.COMMON,
        [EquipmentSlot.CHEST],
        EquipmentStats(defense=3),
        max_durability=25,
        base_drop_chance=0.4
    ),
    "botas_cuero": Equipment(
        "Botas de Cuero",
        EquipmentType.ARMOR,
        EquipmentRarity.COMMON,
        [EquipmentSlot.BOOTS],
        EquipmentStats(defense=1),
        max_durability=20,
        base_drop_chance=0.4
    ),
    
    # Armaduras Poco Comunes
    "peto_hierro": Equipment(
        "Peto de Hierro",
        EquipmentType.ARMOR,
        EquipmentRarity.UNCOMMON,
        [EquipmentSlot.CHEST],
        EquipmentStats(defense=6),
        max_durability=35,
        base_drop_chance=0.3
    ),
    "guantes_hierro": Equipment(
        "Guantes de Hierro",
        EquipmentType.ARMOR,
        EquipmentRarity.UNCOMMON,
        [EquipmentSlot.GLOVES],
        EquipmentStats(attack=2, defense=2),
        max_durability=30,
        base_drop_chance=0.3
    ),
    
    # Armaduras Raras
    "armadura_sombras": Equipment(
        "Armadura de las Sombras",
        EquipmentType.ARMOR,
        EquipmentRarity.RARE,
        [EquipmentSlot.CHEST],
        EquipmentStats(defense=8),
        max_durability=45,
        base_drop_chance=0.2,
        skills={"skulk": 1}
    ),
    "botas_velocidad": Equipment(
        "Botas de Velocidad",
        EquipmentType.ARMOR,
        EquipmentRarity.RARE,
        [EquipmentSlot.BOOTS],
        EquipmentStats(defense=4),
        max_durability=40,
        base_drop_chance=0.2,
        skills={"haste": 1}
    ),
    
    # Escudos
    "escudo_madera": Equipment(
        "Escudo de Madera",
        EquipmentType.SHIELD,
        EquipmentRarity.COMMON,
        [EquipmentSlot.LEFT_HAND],
        EquipmentStats(defense=3),
        max_durability=20,
        base_drop_chance=0.4
    ),
    "escudo_hierro": Equipment(
        "Escudo de Hierro",
        EquipmentType.SHIELD,
        EquipmentRarity.UNCOMMON,
        [EquipmentSlot.LEFT_HAND],
        EquipmentStats(defense=5),
        max_durability=30,
        base_drop_chance=0.3
    )
}

# Configuración de equipamiento para enemigos
ENEMY_EQUIPMENT_CONFIGS = {
    "Goblin": {
        "equipment_pools": {
            EquipmentSlot.RIGHT_HAND: ["garrote", "daga_oxidada"],
            EquipmentSlot.CHEST: ["armadura_cuero"],
            EquipmentSlot.BOOTS: ["botas_cuero"]
        },
        "equipment_chances": {  # Probabilidad de tener equipo en cada slot
            EquipmentSlot.RIGHT_HAND: 0.8,
            EquipmentSlot.CHEST: 0.5,
            EquipmentSlot.BOOTS: 0.3
        }
    },
    "Orco": {
        "equipment_pools": {
            EquipmentSlot.RIGHT_HAND: ["hacha_batalla", "espada_corta"],
            EquipmentSlot.LEFT_HAND: ["escudo_madera", "escudo_hierro"],
            EquipmentSlot.CHEST: ["armadura_cuero", "peto_hierro"],
            EquipmentSlot.GLOVES: ["guantes_hierro"]
        },
        "equipment_chances": {
            EquipmentSlot.RIGHT_HAND: 0.9,
            EquipmentSlot.LEFT_HAND: 0.6,
            EquipmentSlot.CHEST: 0.7,
            EquipmentSlot.GLOVES: 0.4
        }
    },
    "Esqueleto": {
        "equipment_pools": {
            EquipmentSlot.RIGHT_HAND: ["espada_corta", "daga_oxidada"],
            EquipmentSlot.LEFT_HAND: ["escudo_madera"],
            EquipmentSlot.CHEST: ["armadura_cuero"]
        },
        "equipment_chances": {
            EquipmentSlot.RIGHT_HAND: 0.7,
            EquipmentSlot.LEFT_HAND: 0.4,
            EquipmentSlot.CHEST: 0.5
        }
    },
    "Vampiro": {
        "equipment_pools": {
            EquipmentSlot.RIGHT_HAND: ["espada_vampirica", "katana_veloz"],
            EquipmentSlot.CHEST: ["armadura_sombras"],
            EquipmentSlot.BOOTS: ["botas_velocidad"]
        },
        "equipment_chances": {
            EquipmentSlot.RIGHT_HAND: 0.8,
            EquipmentSlot.CHEST: 0.6,
            EquipmentSlot.BOOTS: 0.5
        }
    }
}

def generate_enemy_equipment(enemy_type: str) -> Dict[EquipmentSlot, Optional[Equipment]]:
    """
    Genera equipo aleatorio para un enemigo basado en su tipo.
    """
    if enemy_type not in ENEMY_EQUIPMENT_CONFIGS:
        return {}
    
    config = ENEMY_EQUIPMENT_CONFIGS[enemy_type]
    equipment: Dict[EquipmentSlot, Optional[Equipment]] = {}
    
    for slot in EquipmentSlot:
        if (slot in config["equipment_pools"] and 
            random.random() < config["equipment_chances"].get(slot, 0)):
            # Seleccionar un item aleatorio del pool para este slot
            item_id = random.choice(config["equipment_pools"][slot])
            # Crear una copia del equipo para este enemigo
            base_item = EQUIPMENT_DATABASE[item_id]
            equipment[slot] = Equipment(
                base_item.name,
                base_item.equipment_type,
                base_item.rarity,
                base_item.valid_slots,
                base_item.stats,
                base_item.max_durability,
                base_item.base_drop_chance,
                base_item.skills.copy() if base_item.skills else None
            )
        else:
            equipment[slot] = None
            
    return equipment

class EquipmentManager:
    def __init__(self):
        self.equipment: Dict[EquipmentSlot, Optional[Equipment]] = {
            slot: None for slot in EquipmentSlot
        }
    
    def can_equip(self, item: Equipment, slot: EquipmentSlot) -> bool:
        return slot in item.valid_slots and item.is_usable()
    
    def equip(self, item: Equipment, slot: EquipmentSlot) -> Optional[Equipment]:
        if not self.can_equip(item, slot):
            return None
            
        old_item = self.equipment[slot]
        self.equipment[slot] = item
        return old_item
    
    def unequip(self, slot: EquipmentSlot) -> Optional[Equipment]:
        item = self.equipment[slot]
        self.equipment[slot] = None
        return item
    
    def get_total_stats(self) -> EquipmentStats:
        total_stats = EquipmentStats()
        for item in self.equipment.values():
            if item and item.is_usable():
                total_stats += item.stats
        return total_stats
    
    def get_active_skills(self) -> Dict[str, int]:
        """Retorna todas las habilidades activas del equipo"""
        active_skills: Dict[str, int] = {}
        for item in self.equipment.values():
            if item and item.is_usable() and item.skills:
                for skill, level in item.skills.items():
                    # Mantener el nivel más alto de cada habilidad
                    active_skills[skill] = max(active_skills.get(skill, 0), level)
        return active_skills
    
    def apply_combat_wear(self) -> Set[EquipmentSlot]:
        """
        Aplica desgaste a todo el equipo usado en combate.
        Retorna un conjunto de slots donde el equipo se rompió.
        """
        broken_slots = set()
        for slot, item in self.equipment.items():
            if item and item.is_usable():
                # Aplicar desgaste
                if not item.apply_wear():
                    broken_slots.add(slot)
        return broken_slots

class CharacterEnemy(Character):
    def __init__(self, name: str, health: int, attack: int, defense: int,
                 difficulty: int, innate_skills: Optional[Dict[str, int]] = None) -> None:
        super().__init__(name, health, attack, defense)
        self.difficulty = difficulty
        if innate_skills:
            for skill, level in innate_skills.items():
                self.skills[skill] = level
        
        # Generar y equipar objetos según el tipo de enemigo
        enemy_equipment = generate_enemy_equipment(name)
        for slot, item in enemy_equipment.items():
            if item:
                self.equipment.equip(item, slot)

    @classmethod
    def create_from_type(cls, enemy_type: Dict, current_floor: int, current_level: int) -> 'CharacterEnemy':
        base_health = 100
        base_attack = 20
        base_defense = 10
        
        health = int(base_health * enemy_type.get('health', 1.0))
        attack = int(base_attack * enemy_type.get('attack', 1.0))
        defense = int(base_defense * enemy_type.get('defense', 1.0))
        difficulty = (current_floor + current_level) // 2
        
        return cls(
            enemy_type.get('name', 'Desconocido'),
            health, attack, defense,
            difficulty,
            enemy_type.get("skills", {})
        )
def handle_enemy_drops(enemy: CharacterEnemy) -> List[Equipment]:
    """
    Maneja el sistema de drops cuando un enemigo es derrotado.
    Retorna una lista de equipamiento que el enemigo ha soltado.
    """
    drops = []
    for slot in EquipmentSlot:
        item = enemy.equipment.equipment[slot]
        if item and random.random() < item.drop_chance:
            drops.append(item)
    return drops

# Tipos de enemigos predefinidos
ENEMY_TYPES = [
    {
        "name": "Goblin",
        "min_floor": 1, "max_floor": 4,
        "min_level": 1, "max_level": 3,
        "health": 0.5, "attack": 0.6, "defense": 0.4
    },
    {
        "name": "Orco",
        "min_floor": 2, "max_floor": 5,
        "min_level": 2, "max_level": 4,
        "health": 0.8, "attack": 0.7, "defense": 0.5,
        "skills": {"haste": 1}
    },
    {
        "name": "Esqueleto",
        "min_floor": 1, "max_floor": 3,
        "min_level": 1, "max_level": 2,
        "health": 0.4, "attack": 0.5, "defense": 0.3,
        "skills": {"skulk": 1}
    },
    {
        "name": "Vampiro",
        "min_floor": 3, "max_floor": 6,
        "min_level": 3, "max_level": 6,
        "health": 0.9, "attack": 0.8, "defense": 0.6,
        "skills": {"lifelink": 1, "haste": 1}
    }
]

def generate_random_enemies(current_floor: int, current_level: int, num_enemies: int = 3) -> List[CharacterEnemy]:
    """Genera hasta 3 enemigos aleatorios basados en el piso y nivel actual"""
    valid_enemies = [
        enemy for enemy in ENEMY_TYPES 
        if (enemy["min_floor"] <= current_floor <= enemy["max_floor"] and 
            enemy["min_level"] <= current_level <= enemy["max_level"])
    ]
    
    if not valid_enemies:
        valid_enemies = ENEMY_TYPES
        
    num_enemies = min(num_enemies, len(valid_enemies))
    selected_enemies = random.sample(valid_enemies, num_enemies)
    
    return [CharacterEnemy.create_from_type(enemy_type, current_floor, current_level) 
            for enemy_type in selected_enemies]

def combate(player: CharacterPlayer, current_floor: int, current_level: int) -> None:
    """Sistema de combate con múltiples enemigos y prioridad de turnos"""
    enemies = generate_random_enemies(current_floor, current_level)
    
    print("\n¡Comienza el combate!")
    print(f"{player.name} se enfrenta a:")
    for i, enemy in enumerate(enemies, 1):
        print(f"{i}. {enemy}")
    
    all_combatants = [player] + enemies
    round_number = 1
    
    while player.is_alive() and any(enemy.is_alive() for enemy in enemies):
        print(f"\n=== Ronda {round_number} ===")
        
        # Determinar orden de turnos
        for combatant in all_combatants:
            if combatant.is_alive():
                combatant.has_priority = combatant.check_haste()
        
        # Ordenar combatientes por prioridad
        priority_combatants = [c for c in all_combatants if c.is_alive() and c.has_priority]
        normal_combatants = [c for c in all_combatants if c.is_alive() and not c.has_priority]
        
        random.shuffle(priority_combatants)
        random.shuffle(normal_combatants)
        turn_order = priority_combatants + normal_combatants
        
        # Ejecutar turnos
        for attacker in turn_order:
            # Verificar si el jugador ha sido derrotado
            if not player.is_alive():
                break  # Salir del bucle de turnos si el jugador muere
                
            if not attacker.is_alive():
                continue
                
            if isinstance(attacker, CharacterPlayer):
                alive_enemies = [e for e in enemies if e.is_alive()]
                if not alive_enemies:
                    break
                    
                target = random.choice(alive_enemies)
                print(f"\nTurno de {attacker.name}")
                damage = attacker.attack_target(target)
                print(f"Daño causado a {target.name}: {damage}")
                print(target)
            else:
                print(f"\nTurno de {attacker.name}")
                damage = attacker.attack_target(player)
                print(f"Daño causado a {player.name}: {damage}")
                print(player)
                
                # Verificar si el jugador murió después del ataque
                if not player.is_alive():
                    break  # Salir del bucle de turnos si el jugador muere
        
        # Si el jugador está muerto, salir del bucle principal
        if not player.is_alive():
            break
            
        # Resetear prioridades
        for combatant in all_combatants:
            combatant.has_priority = False
            
        round_number += 1
    
    # Resultado del combate
    print("\n=== Fin del Combate ===")
    if player.is_alive():
        print(f"¡Victoria para {player.name}!")
        experience_gained = sum(enemy.difficulty * 50 for enemy in enemies)
        player.gain_experience(experience_gained)
        print(f"{player.name} gana {experience_gained} puntos de experiencia!")
        
        # Procesar drops de los enemigos
        for enemy in enemies:
            drops = handle_enemy_drops(enemy)
            if drops:
                print(f"\nDrops de {enemy.name}:")
                for item in drops:
                    print(f"- {item}")
                # Aquí podrías implementar un sistema para que el jugador
                # decida qué objetos recoger y equipar
        
        # Aplicar desgaste al equipo del jugador
        broken_slots = player.equipment.apply_combat_wear()
        if broken_slots:
            print("\n¡Equipo dañado!")
            for slot in broken_slots:
                print(f"El equipo en {slot.value} se ha roto.")
    else:
        print(f"¡{player.name} ha sido derrotado!")

# Ejemplo de uso
if __name__ == "__main__":
    # Crear jugador
    player = CharacterPlayer("Héroe", 100, 30, 15)
    print("Estado inicial del jugador:")
    print(player)
    
    # Simular combates en diferentes pisos
    for floor in range(1, 4):
        print(f"\n=== Entrando al piso {floor} ===")
        combate(player, current_floor=floor, current_level=player.level)
        
        if not player.is_alive():
            print("\n¡Juego terminado!")
            break