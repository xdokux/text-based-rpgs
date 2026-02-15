#!/usr/bin/env python3


import json
import os
import random
import shutil
import tempfile
import uuid
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional

# -------------------------
# Terminal colors (For Later)
# -------------------------
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

def c(text, color):
    return f"{color}{text}{Color.RESET}"

# -------------------------
# Config
# -------------------------
SAVE_DIR = "saves"
NUM_SLOTS = 3
WORLD_ENCOUNTERS = 12  # number of encounters per generated run

# Hunter unlock level
HUNTER_UNLOCK_LEVEL = 7

# Grenade config
FRAG_DAMAGE = 60
FRAG_SHIELD_PENETRATION = 0.6  # fraction of grenade damage that bypasses shields
FRAG_SELF_DAMAGE_ON_FAIL = 10   # small chance grenade toss harms thrower if fail (flavor)

# -------------------------
# Lore-ish weapon & enemy DB
# (extended with enemy-class-specific weapons)
# -------------------------
WEAPONS_DB = {
    # UNSC weapons (player starters)
    "MA5B Assault Rifle": {"type": "ballistic", "damage": 8, "mag": 32, "range": 15, "crit": 0.02},
    "BR55 Battle Rifle": {"type": "ballistic", "damage": 28, "mag": 8, "range": 40, "crit": 0.03},
    "M6D Magnum": {"type": "ballistic", "damage": 40, "mag": 8, "range": 35, "crit": 0.06},
    "SRS99C Sniper": {"type": "ballistic", "damage": 110, "mag": 4, "range": 200, "crit": 0.12},

    # Covenant weapons (used by Elites, Jackals, Grunts depending on class)
    "Needler": {"type": "exotic", "damage": 12, "mag": 32, "range": 12, "crit": 0.03},
    "Plasma Pistol": {"type": "energy", "damage": 10, "mag": 100, "range": 20, "crit": 0.01},
    "Plasma Rifle": {"type": "energy", "damage": 18, "mag": 60, "range": 25, "crit": 0.02},
    "Energy Sword": {"type": "melee", "damage": 85, "mag": 0, "range": 1, "crit": 0.10},

    # Sentinel / Forerunner
    "Sentinel Beam": {"type": "energy", "damage": 18, "mag": 1000, "range": 40, "crit": 0.02},

    # Heavy / vehicle-mounted (Hunter's fuel rod tuned)
    # Base damage for Fuel Rod lowered to 40; crit logic will allow up to 90 on crit
    "Fuel Rod Cannon": {"type": "explosive", "damage": 40, "mag": 1, "range": 60, "crit": 0.10},

    # Flood melee
    "Claw": {"type": "melee", "damage": 10, "mag": 0, "range": 1, "crit": 0.02},

    # Frag grenade as a 'weapon' possible to drop (kept)
    "Frag Grenade": {"type": "explosive", "damage": FRAG_DAMAGE, "mag": 1, "range": 8, "crit": 0.0},
}

# Map some enemy classes to allowed weapons
ENEMY_WEAPON_POOLS = {
    "Elite": ["Needler", "Plasma Rifle", "Plasma Pistol", "Energy Sword"],
    "Jackal": ["Plasma Rifle", "Needler", "Plasma Pistol"],
    "Grunt": ["Plasma Pistol", "Needler"],
    "Sentinel": ["Sentinel Beam"],
    "Hunter": ["Fuel Rod Cannon"],
    "Flood": ["Claw"],
    # Engineers: no weapons
}

ENEMIES_DB = {
    "Grunt": {"hp": 20, "shield": 0, "damage": 4, "accuracy": 0.7},
    "Jackal": {"hp": 30, "shield": 10, "damage": 6, "accuracy": 0.65},
    "Elite (Minor)": {"hp": 60, "shield": 50, "damage": 12, "accuracy": 0.75},
    "Elite (Major)": {"hp": 120, "shield": 80, "damage": 20, "accuracy": 0.8},
    "Hunter": {"hp": 300, "shield": 0, "damage": 45, "accuracy": 0.6},
    "Sentinel": {"hp": 80, "shield": 80, "damage": 18, "accuracy": 0.6},
    "Flood Infected": {"hp": 45, "shield": 0, "damage": 8, "accuracy": 0.6},
    "Engineer": {"hp": 25, "shield": 0, "damage": 0, "accuracy": 0.1},
}

FRIENDLY_TYPES = [
    "Marine",
    "ODST",
    "Spartan",
    "Civilian"
]


# -------------------------
# Utilities
# -------------------------
def ensure_save_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def slot_filename(slot: int) -> str:
    assert 1 <= slot <= NUM_SLOTS
    return os.path.join(SAVE_DIR, f"save_slot_{slot}.json")


def atomic_save(path: str, data: Dict[str, Any]):
    # Write to a temp file and move to ensure atomic save
    dirpath = os.path.dirname(path)
    with tempfile.NamedTemporaryFile("w", dir=dirpath, delete=False) as tf:
        json.dump(data, tf, indent=2)
        tempname = tf.name
    shutil.move(tempname, path)


def load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


# -------------------------
# Data classes
# -------------------------
@dataclass
class Weapon:
    name: str
    damage: int
    mag: int
    ammo: int
    wtype: str
    range: int
    crit_bonus: float = 0.0  # optional

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        crit = d.get("crit_bonus", d.get("crit", 0.0))
        return Weapon(name=d["name"], damage=d["damage"], mag=d["mag"],
                      ammo=d["ammo"], wtype=d["wtype"], range=d["range"], crit_bonus=crit)


@dataclass
class Player:
    name: str
    hp: int
    max_hp: int
    shield: int
    max_shield: int
    xp: int
    level: int
    inventory: Dict[str, int] = field(default_factory=dict)  # grenades, medkits, artifacts
    weapons: List[Weapon] = field(default_factory=list)      # exactly 2 items max
    current_weapon: int = 0  # index in weapons (0 or 1)
    pos: int = 0  # index in world encounters
    seed: str = ""  # world seed - unique per game

    def to_dict(self):
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "shield": self.shield,
            "max_shield": self.max_shield,
            "xp": self.xp,
            "level": self.level,
            "inventory": self.inventory,
            "weapons": [w.to_dict() for w in self.weapons],
            "current_weapon": self.current_weapon,
            "pos": self.pos,
            "seed": self.seed,
        }

    @staticmethod
    def from_dict(d):
        # weapons field may exist as list of dicts
        p = Player(
            name=d["name"],
            hp=d["hp"],
            max_hp=d["max_hp"],
            shield=d["shield"],
            max_shield=d["max_shield"],
            xp=d["xp"],
            level=d["level"],
            inventory=d.get("inventory", {}),
            weapons=[Weapon.from_dict(wd) for wd in d.get("weapons", [])],
            current_weapon=d.get("current_weapon", 0),
            pos=d.get("pos", 0),
            seed=d.get("seed", "")
        )
        # Ensure weapons list is length 2 (pad with MA5B if necessary)
        if len(p.weapons) < 2:
            for _ in range(2 - len(p.weapons)):
                wd = WEAPONS_DB["MA5B Assault Rifle"]
                p.weapons.append(Weapon(name="MA5B Assault Rifle", damage=wd["damage"], mag=wd["mag"], ammo=wd["mag"], wtype=wd["type"], range=wd["range"], crit_bonus=wd.get("crit", 0.0)))
        elif len(p.weapons) > 2:
            p.weapons = p.weapons[:2]
        if p.current_weapon not in (0, 1):
            p.current_weapon = 0
        return p


@dataclass
class Enemy:
    name: str
    hp: int
    shield: int
    damage: int  # legacy field (kept), but enemy attacks should use enemy.weapon if present
    accuracy: float
    ai_type: str = "standard"
    has_grenades: bool = False
    weapon: Optional[Weapon] = None  # assigned based on class

    def is_alive(self):
        return self.hp > 0


@dataclass
class NPC:
    name: str
    role: str
    friendliness: int  # -100 to 100

# -------------------------
# Helper: create Weapon instance from WEAPONS_DB
# -------------------------
def make_weapon_by_name(name: str) -> Weapon:
    wd = WEAPONS_DB[name]
    return Weapon(name=name, damage=wd["damage"], mag=wd["mag"], ammo=wd["mag"], wtype=wd["type"], range=wd["range"], crit_bonus=wd.get("crit", 0.0))

# -------------------------
# Helper: choose enemy weapon based on enemy class/name
# -------------------------
def choose_weapon_for_enemy(enemy_name: str) -> Optional[Weapon]:
    # Map enemy base names to pools
    if "Elite" in enemy_name:
        pool = ENEMY_WEAPON_POOLS.get("Elite", [])
    elif "Jackal" in enemy_name:
        pool = ENEMY_WEAPON_POOLS.get("Jackal", [])
    elif "Grunt" in enemy_name:
        pool = ENEMY_WEAPON_POOLS.get("Grunt", [])
    elif "Sentinel" in enemy_name:
        pool = ENEMY_WEAPON_POOLS.get("Sentinel", [])
    elif "Hunter" in enemy_name:
        pool = ENEMY_WEAPON_POOLS.get("Hunter", [])
    elif "Flood" in enemy_name:
        pool = ENEMY_WEAPON_POOLS.get("Flood", [])
    elif "Engineer" in enemy_name:
        pool = []  # engineers don't use weapons
    else:
        pool = []

    if not pool:
        return None

    wname = random.choice(pool)
    return make_weapon_by_name(wname)

# -------------------------
# World generator
# -------------------------
class World:
    def __init__(self, seed: Optional[str] = None):
        self.seed = seed or str(uuid.uuid4())
        self.encounters = []
        self.npcs = {}  # position -> NPC
        self.generate()

    def generate(self):
        random.seed(self.seed)
        self.encounters = []
        self.npcs = {}
        for i in range(WORLD_ENCOUNTERS):
            r = random.random()
            if r < 0.5:
                # combat encounter
                enemy_name = random.choice(list(ENEMIES_DB.keys()))
                ed = ENEMIES_DB[enemy_name]
                ai_choice = random.random()
                if ai_choice < 0.12:
                    ai = "coward"
                elif ai_choice < 0.7:
                    ai = "standard"
                elif ai_choice < 0.9:
                    ai = "tactical"
                else:
                    ai = "berserk"
                has_g = random.random() < (0.18 if "Elite" in enemy_name or enemy_name == "Jackal" else 0.06)
                # create enemy with a weapon suitable to its class
                enemy_weapon = choose_weapon_for_enemy(enemy_name)
                enemy = Enemy(name=enemy_name, hp=ed["hp"], shield=ed["shield"],
                              damage=ed["damage"], accuracy=ed["accuracy"], ai_type=ai, has_grenades=has_g, weapon=enemy_weapon)
                self.encounters.append(("combat", enemy))
            elif r < 0.75:
                npc_name = random.choice(FRIENDLY_TYPES)
                npc = NPC(name=npc_name, role=random.choice(["scout", "engineer", "soldier", "medic"]),
                          friendliness=random.randint(-20, 100))
                self.encounters.append(("npc", npc))
                if random.random() < 0.6:
                    self.npcs[i] = npc
            else:
                item = random.choice(["ammo_pack", "shield_battery", "artifact", "vehicle_key", "frag_grenade"])
                self.encounters.append(("loot", item))

    def to_dict(self):
        return {"seed": self.seed, "npcs": {str(k): asdict(v) for k, v in self.npcs.items()}}

    @staticmethod
    def from_dict(d):
        w = World(seed=d["seed"])
        w.npcs = {int(k): NPC(**v) for k, v in d.get("npcs", {}).items()}
        w.generate()
        return w

# -------------------------
# Save manager
# -------------------------
class SaveManager:
    def __init__(self):
        ensure_save_dir()

    def slot_exists(self, slot: int) -> bool:
        return os.path.exists(slot_filename(slot))

    def new_game(self, slot: int, player_name: str) -> Dict[str, Any]:
        seed = str(uuid.uuid4())
        world = World(seed=seed)

        # helper to create Weapon instances for starter loadout
        def make_w(name):
            wd = WEAPONS_DB[name]
            return Weapon(name=name, damage=wd["damage"], mag=wd["mag"],
                          ammo=wd["mag"], wtype=wd["type"], range=wd["range"], crit_bonus=wd.get("crit", 0.0))

        # Starter loadout: exactly 2 weapons
        weapons = [make_w("MA5B Assault Rifle"), make_w("M6D Magnum")]
        player = Player(name=player_name, hp=100, max_hp=100, shield=50, max_shield=50,
                        xp=0, level=1, inventory={"medkit": 1, "frag_grenade": 1}, weapons=weapons, current_weapon=0, pos=0, seed=seed)

        save_data = {
            "player": player.to_dict(),
            "world": world.to_dict(),
            "meta": {"slot_created": slot, "seed": seed}
        }
        self.save_slot(slot, save_data)
        return save_data

    def save_slot(self, slot: int, data: Dict[str, Any]):
        path = slot_filename(slot)
        atomic_save(path, data)

    def load_slot(self, slot: int) -> Optional[Dict[str, Any]]:
        path = slot_filename(slot)
        return load_json(path)

    def delete_slot(self, slot: int):
        path = slot_filename(slot)
        if os.path.exists(path):
            os.remove(path)

# -------------------------
# Combat system (mostly unchanged; weapon use updated)
# -------------------------
def perform_attack(attacker_name: str, weapon: Optional[Weapon], attacker_accuracy: float, defender: Enemy) -> (str, int):
    """
    Returns (description, damage_dealt)
    - Uses weapon damage (weapon param) if provided; otherwise fallback 6
    - Crit chance base 0.05 + weapon.crit_bonus
    - Crit multiplier 1.5x (special-case Hunter handled in enemy_turn)
    """
    # miss check
    roll = random.random()
    hit_threshold = attacker_accuracy
    if roll > hit_threshold:
        return (f"{attacker_name} fires but misses!", 0)

    # Determine base damage
    base_damage = weapon.damage if weapon else 6

    # Critical roll
    base_crit = 0.05
    crit_chance = base_crit + (weapon.crit_bonus if weapon else 0.0)
    crit = False
    if random.random() < crit_chance:
        crit = True
        base_damage = int(base_damage * 1.5)

    crit_text = " Critical hit!" if crit else ""
    return (f"{attacker_name} hits {defender.name} for {base_damage} damage.{crit_text}", base_damage)


def throw_grenade(attacker_name: str, target_name: str, inventory: Dict[str, int]) -> (str, int, Dict[str, int]):
    if inventory.get("frag_grenade", 0) <= 0:
        return (f"{attacker_name} tries to throw a grenade but has none!", 0, inventory)
    inventory["frag_grenade"] = max(0, inventory.get("frag_grenade", 0) - 1)
    hit_roll = random.random()
    if hit_roll < 0.9:
        dmg = FRAG_DAMAGE
        return (f"{attacker_name} throws a frag grenade at {target_name}! It explodes for {dmg} damage.", dmg, inventory)
    else:
        dud_dmg = int(FRAG_DAMAGE * 0.25)
        return (f"{attacker_name} fumbles the throw; weak explosion deals {dud_dmg} damage.", dud_dmg, inventory)

# -------------------------
# Simple CLI helpers
# -------------------------
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def pause(msg="Press Enter to continue..."):
    input(msg)


# -------------------------
# Game class: orchestrates flow
# -------------------------
class Game:
    def __init__(self):
        self.savemgr = SaveManager()
        self.player: Optional[Player] = None
        self.world: Optional[World] = None
        self.save_slot: Optional[int] = None

    def main_menu(self):
        while True:
            clear_screen()
            print("=== HALO-TEXT-RPG (Prototype) ===")
            print("1) New Game")
            print("2) Load Game")
            print("3) Delete Save")
            print("4) Exit")
            choice = input("> ").strip()
            if choice == "1":
                self.menu_new_game()
            elif choice == "2":
                self.menu_load_game()
            elif choice == "3":
                self.menu_delete_save()
            elif choice == "4":
                print("Bye.")
                return
            else:
                print("Invalid choice.")
                pause()

    def menu_new_game(self):
        clear_screen()
        print("Choose save slot for new game (1-3). Creating a new game will overwrite that slot.")
        for i in range(1, NUM_SLOTS + 1):
            exists = self.savemgr.slot_exists(i)
            print(f"{i}) Slot {i} - {'USED' if exists else 'EMPTY'}")
        try:
            slot = int(input("Slot: ").strip() or "1")
        except ValueError:
            print("Invalid slot.")
            pause(); return
        if slot < 1 or slot > NUM_SLOTS:
            print("Invalid slot.")
            pause(); return
        name = input("Enter your player name (default: 'Chief'): ").strip() or "Chief"
        save = self.savemgr.new_game(slot, name)
        print(f"New game created in slot {slot}.")
        pause()
        self.load_from_save(slot, save)

    def menu_load_game(self):
        clear_screen()
        print("Choose a slot to load (1-3)")
        for i in range(1, NUM_SLOTS + 1):
            exists = self.savemgr.slot_exists(i)
            print(f"{i}) Slot {i} - {'USED' if exists else 'EMPTY'}")
        try:
            slot = int(input("Slot: ").strip() or "1")
        except ValueError:
            print("Invalid slot.")
            pause(); return
        loaded = self.savemgr.load_slot(slot)
        if not loaded:
            print("No save in that slot.")
            pause(); return
        self.load_from_save(slot, loaded)
        print(f"Loaded slot {slot}.")
        pause()

    def menu_delete_save(self):
        clear_screen()
        print("Choose a slot to delete (1-3)")
        for i in range(1, NUM_SLOTS + 1):
            exists = self.savemgr.slot_exists(i)
            print(f"{i}) Slot {i} - {'USED' if exists else 'EMPTY'}")
        try:
            slot = int(input("Slot to delete: ").strip() or "1")
        except ValueError:
            print("Invalid slot.")
            pause(); return
        if not self.savemgr.slot_exists(slot):
            print("Slot empty.")
            pause(); return
        confirm = input(f"Type DELETE to erase slot {slot}: ")
        if confirm == "DELETE":
            self.savemgr.delete_slot(slot)
            print("Deleted.")
        else:
            print("Cancelled.")
        pause()

    def load_from_save(self, slot: int, save_data: Dict[str, Any]):
        # strictly only use the single file provided
        self.save_slot = slot
        player_data = save_data["player"]
        world_data = save_data["world"]
        self.player = Player.from_dict(player_data)
        self.world = World.from_dict(world_data)

        # Make sure to reseed RNG so world remains deterministic across sessions
        random.seed(self.player.seed)

        # Start game loop
        self.game_loop()

    def save_game(self):
        if not self.save_slot or not self.player or not self.world:
            print("No game to save.")
            return
        data = {"player": self.player.to_dict(), "world": self.world.to_dict(), "meta": {"slot": self.save_slot}}
        self.savemgr.save_slot(self.save_slot, data)
        print("Game saved.")

    # ---- Gameplay loop & mechanics
    def game_loop(self):
        while True:
            clear_screen()
            print(f"=== Adventure (Slot {self.save_slot}) ===")
            print(f"Player: {self.player.name}  Level: {self.player.level}  XP: {self.player.xp}")
            print(f"HP: {self.player.hp}/{self.player.max_hp}   Shields: {self.player.shield}/{self.player.max_shield}")
            cw = self.player.weapons[self.player.current_weapon]
            # Ammo removed from UI; only show weapon name and crit bonus
            print(f"Weapon: [{self.player.current_weapon}] {cw.name}  (Crit +{cw.crit_bonus*100:.1f}%)")
            print(f"Frag grenades: {self.player.inventory.get('frag_grenade', 0)}")
            print(f"Progress: encounter {self.player.pos + 1} / {len(self.world.encounters)}")
            print("")
            print("Actions: [M]ove forward  [S]tatus  [I]nventory  [W]eapons  Sa[V]e  [Q]uit (to menu)")
            action = input("> ").strip().lower()
            if action == "m":
                self.advance()
                if self.player.pos >= len(self.world.encounters):
                    print("You reached the end of the mission. Congrats!")
                    # reward: small XP and end
                    self.player.xp += 50
                    pause()
                    self.save_game()
                    return
            elif action == "s":
                pause("Showing status. Press Enter...")
            elif action == "i":
                self.show_inventory()
            elif action == "w":
                self.switch_weapon()
            elif action == "v":
                self.save_game()
                pause()
            elif action == "q":
                print("Returning to main menu.")
                pause()
                return
            else:
                print("Unknown action.")
                pause()

    def show_inventory(self):
        clear_screen()
        print("== Inventory ==")
        for k, v in self.player.inventory.items():
            print(f"{k}: {v}")
        print("Weapons:")
        for idx, w in enumerate(self.player.weapons):
            cur = "<-- equipped" if idx == self.player.current_weapon else ""
            print(f"[{idx}] {w.name} Crit+{w.crit_bonus*100:.1f}% {cur}")
        pause()

    def switch_weapon(self):
        clear_screen()
        print("Choose weapon index to equip (0 or 1):")
        for idx, w in enumerate(self.player.weapons):
            print(f"{idx}) {w.name} Crit+{w.crit_bonus*100:.1f}%")
        try:
            idx = int(input("Index: ").strip())
            if 0 <= idx < len(self.player.weapons):
                self.player.current_weapon = idx
                print(f"Equipped {self.player.weapons[idx].name}")
            else:
                print("Invalid index.")
        except Exception:
            print("Invalid input.")
        pause()

    def advance(self):
        idx = self.player.pos
        encounter = self.world.encounters[idx]
        typ = encounter[0]
        if typ == "combat":
            enemy: Enemy = encounter[1]
            # If Hunter appears but player hasn't unlocked them yet, replace with non-Hunter
            if "Hunter" in enemy.name and self.player.level < HUNTER_UNLOCK_LEVEL:
                # pick a different enemy (non-Hunter)
                alternative = random.choice([n for n in ENEMIES_DB.keys() if "Hunter" not in n and n != "Engineer"])
                ed = ENEMIES_DB[alternative]
                enemy = Enemy(name=alternative, hp=ed["hp"], shield=ed["shield"], damage=ed["damage"], accuracy=ed["accuracy"], ai_type=enemy.ai_type, has_grenades=enemy.has_grenades, weapon=choose_weapon_for_enemy(alternative))
            # copy enemy so save file keeps deterministic world but we battle fresh instance
            ecopy = Enemy(name=enemy.name, hp=enemy.hp, shield=enemy.shield, damage=enemy.damage, accuracy=enemy.accuracy, ai_type=enemy.ai_type, has_grenades=enemy.has_grenades, weapon=enemy.weapon)
            self.run_combat(ecopy)
            # if player alive, gain small xp and continue
            if self.player.hp > 0:
                self.player.xp += 10
                # drop small loot sometimes
                if random.random() < 0.35:
                    self.give_loot("ammo_pack")
        elif typ == "npc":
            npc: NPC = encounter[1]
            self.interact_npc(npc)
        elif typ == "loot":
            item = encounter[1]
            print(f"You stumbled on: {item}!")
            self.give_loot(item)
            pause()
        self.player.pos += 1
        # auto-save after each encounter
        self.save_game()

    def give_loot(self, item: str):
        if item == "ammo_pack":
            # legacy: ammo_pack adds ammo to current weapon if desired — but ammo isn't used.
            w = self.player.weapons[self.player.current_weapon]
            add = int(w.mag * 0.6)
            w.ammo += add
            print(f"You found ammo for {w.name} (+{add}). (Ammo not used)")
        elif item == "shield_battery":
            self.player.shield = min(self.player.max_shield, self.player.shield + 50)
            print("Shield battery used: +50 shields")
        elif item == "artifact":
            self.player.inventory["artifact"] = self.player.inventory.get("artifact", 0) + 1
            print("You recovered a Forerunner artifact.")
        elif item == "vehicle_key":
            self.player.inventory["vehicle_key"] = self.player.inventory.get("vehicle_key", 0) + 1
            print("You found a vehicle key (use later).")
        elif item == "frag_grenade":
            self.player.inventory["frag_grenade"] = self.player.inventory.get("frag_grenade", 0) + 1
            print("You found a frag grenade!")
        else:
            self.player.inventory[item] = self.player.inventory.get(item, 0) + 1
            print(f"You found {item}.")
        pause()

    def interact_npc(self, npc: NPC):
        clear_screen()
        print(f"You encounter a {npc.name} ({npc.role}).")
        if npc.friendliness > 30:
            print("They seem friendly and will trade / help.")
            # small trade: give medkit if you have artifact
            if self.player.inventory.get("artifact", 0) > 0:
                print("You can trade an artifact for a medkit.")
                choice = input("Trade artifact for medkit? (y/n) ")
                if choice.lower() == "y":
                    self.player.inventory["artifact"] -= 1
                    self.player.inventory["medkit"] = self.player.inventory.get("medkit", 0) + 1
                    print("Traded.")
            else:
                print("They offer you a medkit.")
                if random.random() < 0.45:
                    self.player.inventory["medkit"] = self.player.inventory.get("medkit", 0) + 1
                    print("Received medkit.")
        else:
            print("They are cautious. You move on.")
        pause()

    def run_combat(self, enemy: Enemy):
        # Show enemy weapon if present
        e_weapon_line = f"  Weapon: {enemy.weapon.name}" if enemy.weapon else ""
        print(f"Combat start! Enemy: {enemy.name} (HP {enemy.hp}, SH {enemy.shield}){e_weapon_line}")
        if enemy.has_grenades:
            print(f"{enemy.name} appears to be carrying grenades.")
        print(f"Enemy behavior: {enemy.ai_type}")
        pause("Press Enter to begin combat...")
        # simple turn-based: player then enemy until one dies
        while enemy.is_alive() and self.player.hp > 0:
            clear_screen()
            # Display enemy stats + weapon
            print(f"Enemy: {enemy.name}   HP:{enemy.hp}  SH:{enemy.shield}  AI:{enemy.ai_type}")
            if enemy.weapon:
                print(f"  Weapon: {enemy.weapon.name}  (DMG {enemy.weapon.damage})")
            # Display player stats
            print(f"You: HP:{self.player.hp}/{self.player.max_hp}  SH:{self.player.shield}/{self.player.max_shield}")
            cw = self.player.weapons[self.player.current_weapon]
            # No ammo display
            print(f"Equipped: {cw.name}  (Crit +{cw.crit_bonus*100:.1f}%)")
            print(f"Frag grenades: {self.player.inventory.get('frag_grenade', 0)}")
            print("Actions: [A]ttack  [G]renade  [M]edkit  [F]lee  [S]tatus")
            act = input("> ").strip().lower()
            if act == "a":
                # attack with current weapon (no ammo checks)
                w = self.player.weapons[self.player.current_weapon]
                player_accuracy = 0.75
                desc, dmg = perform_attack(self.player.name, w, player_accuracy, enemy)
                print(desc)
                # apply damage: shields first
                applied = 0
                if enemy.shield > 0:
                    if dmg <= enemy.shield:
                        enemy.shield -= dmg
                        applied = dmg
                        dmg = 0
                    else:
                        applied = enemy.shield
                        dmg -= enemy.shield
                        enemy.shield = 0
                if dmg > 0:
                    enemy.hp = max(0, enemy.hp - dmg)
                pause()
            elif act == "g":
                # throw grenade if player has any
                desc, raw_dmg, self.player.inventory = throw_grenade(self.player.name, enemy.name, self.player.inventory)
                print(desc)
                # grenade : apply shield penetration
                shield_dmg = int(raw_dmg * (1 - FRAG_SHIELD_PENETRATION))
                hp_dmg = raw_dmg - shield_dmg
                # apply shield component first (the shield_dmg portion)
                if enemy.shield > 0:
                    if shield_dmg <= enemy.shield:
                        enemy.shield -= shield_dmg
                        shield_dmg = 0
                    else:
                        shield_dmg -= enemy.shield
                        enemy.shield = 0
                # any leftover small shield_dmg is converted to hp damage
                total_hp_damage = hp_dmg + shield_dmg
                if total_hp_damage > 0:
                    enemy.hp = max(0, enemy.hp - total_hp_damage)
                pause()
            elif act == "m":
                if self.player.inventory.get("medkit", 0) > 0:
                    self.player.inventory["medkit"] -= 1
                    heal = 40
                    self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                    print("Used medkit. Restored HP.")
                else:
                    print("No medkits!")
                pause()
            elif act == "f":
                chance = 0.5
                if random.random() < chance:
                    print("You fled successfully.")
                    pause()
                    return
                else:
                    print("Failed to flee!")
                    pause()
            elif act == "s":
                pause("Status view.")
            else:
                print("Unknown action.")
                pause()
                continue

            # enemy turn (if still alive)
            if enemy.is_alive():
                self.enemy_take_turn(enemy)
                pause()

        if self.player.hp <= 0:
            # PERMADEATH flow: delete this save slot, prompt to start again
            print("You died. Mission failed.")
            if self.save_slot:
                # remove save file
                try:
                    self.savemgr.delete_slot(self.save_slot)
                    print("Your save slot has been wiped (permadeath).")
                except Exception:
                    pass
            # ask player whether to start a new game immediately
            choice = input("Start a new game in this slot now? (y/n) ").strip().lower()
            if choice == "y":
                # prompt for name and create new game in same slot
                name = input("Enter new player name (default: 'Chief'): ").strip() or "Chief"
                save = self.savemgr.new_game(self.save_slot, name)
                print("New game created. Loading...")
                pause()
                self.load_from_save(self.save_slot, save)
                return
            else:
                print("Returning to main menu.")
                pause()
                return

        if not enemy.is_alive():
            print(f"You defeated the {enemy.name}!")
            # reward: a small chance for weapon or medkit or grenade
            r = random.random()
            # Weapon drop logic: enemy may drop its own weapon (if any)
            dropped_weapon = None
            if enemy.weapon and r < 0.3:
                # 30% of the time the enemy's weapon is recoverable
                dropped_weapon = enemy.weapon
            if r < 0.2:
                # medkit
                self.player.inventory["medkit"] = self.player.inventory.get("medkit", 0) + 1
                print("Found medkit on enemy.")
            elif r < 0.28:
                # small chance for a random weapon (legacy behavior kept but rare)
                drop = random.choice(list(WEAPONS_DB.keys()))
                wd = WEAPONS_DB[drop]
                neww = Weapon(name=drop, damage=wd["damage"], mag=wd["mag"], ammo=wd["mag"], wtype=wd["type"], range=wd["range"], crit_bonus=wd.get("crit", 0.0))
                dropped_weapon = neww
            elif r < 0.36:
                self.player.inventory["frag_grenade"] = self.player.inventory.get("frag_grenade", 0) + 1
                print("Enemy dropped a frag grenade!")

            # If there's a weapon to pick up, prompt player to replace one of their two weapons
            if dropped_weapon:
                print(f"The enemy dropped a weapon: {dropped_weapon.name} (DMG {dropped_weapon.damage})")
                choice = input("Pick it up and replace one of your two weapons? (y/n) ").strip().lower()
                if choice == "y":
                    # show current weapons
                    print("Your current weapons:")
                    for idx, w in enumerate(self.player.weapons):
                        print(f"{idx}) {w.name} (DMG {w.damage})")
                    try:
                        replace_idx = int(input("Select slot to replace (0 or 1): ").strip())
                        if replace_idx not in (0, 1):
                            print("Invalid slot. Cancelling pickup.")
                        else:
                            self.player.weapons[replace_idx] = dropped_weapon
                            # ensure current_weapon index remains valid
                            if self.player.current_weapon not in (0, 1):
                                self.player.current_weapon = 0
                            print(f"Replaced slot {replace_idx} with {dropped_weapon.name}.")
                    except Exception:
                        print("Invalid input; not picking up weapon.")
                else:
                    print("You leave the weapon behind.")
            pause()

    def enemy_take_turn(self, enemy: Enemy):
        """
        Determines enemy action based on AI type and state.
        Now uses enemy.weapon (if present) for damage; falls back to enemy.damage.
        Hunters are handled so crits are limited to the desired cap.
        """
        # Basic chance to attempt grenade (if has)
        if enemy.has_grenades and self.player.inventory.get("frag_grenade", 0) >= 0:
            if enemy.ai_type == "tactical":
                grenade_prob = 0.45
            elif enemy.ai_type == "standard":
                grenade_prob = 0.18
            elif enemy.ai_type == "berserk":
                grenade_prob = 0.08
            else:  # coward
                grenade_prob = 0.05
        else:
            grenade_prob = 0.0

        # cowardly flee logic (keeps same behavior)
        if enemy.ai_type == "coward" and enemy.hp < (enemy.hp * 0.35):
            if random.random() < 0.45:
                print(f"{enemy.name} attempts to flee!")
                return

        # grenade attempt
        if random.random() < grenade_prob:
            raw_dmg = FRAG_DAMAGE
            print(f"{enemy.name} throws a frag grenade at you!")
            shield_dmg = int(raw_dmg * (1 - FRAG_SHIELD_PENETRATION))
            hp_dmg = raw_dmg - shield_dmg
            if self.player.shield > 0:
                if shield_dmg <= self.player.shield:
                    self.player.shield -= shield_dmg
                    shield_dmg = 0
                else:
                    shield_dmg -= self.player.shield
                    self.player.shield = 0
            total_hp_damage = hp_dmg + shield_dmg
            if total_hp_damage > 0:
                self.player.hp = max(0, self.player.hp - total_hp_damage)
            print(f"It explodes for {raw_dmg} total damage (after shields you take {total_hp_damage}).")
            return

        # Else perform normal attack using weapon if available
        attack_accuracy = enemy.accuracy
        if enemy.ai_type == "berserk":
            attack_accuracy *= 0.9

        # Determine damage (from weapon if present)
        if enemy.weapon:
            base_damage = enemy.weapon.damage
            # enemy critical chance uses weapon crit bonus + base
            base_crit = 0.03
            crit_chance = base_crit + (enemy.weapon.crit_bonus if enemy.weapon else 0.0)
        else:
            base_damage = enemy.damage
            crit_chance = 0.02

        if random.random() < attack_accuracy:
            # critical?
            crit = False
            if random.random() < crit_chance:
                crit = True
                # Special-case Hunter's Fuel Rod Cannon: larger crit multiplier but capped
                if enemy.weapon and enemy.weapon.name == "Fuel Rod Cannon":
                    crit_mult = 2.25  # 40 * 2.25 = 90 (the cap)
                    dmg = int(base_damage * crit_mult)
                    if dmg > 90:
                        dmg = 90
                else:
                    dmg = int(base_damage * 1.5)
            else:
                dmg = base_damage

            applied_to_shield = 0
            applied_to_hp = 0
            to_apply = dmg
            if self.player.shield > 0:
                if to_apply <= self.player.shield:
                    self.player.shield -= to_apply
                    applied_to_shield = to_apply
                    to_apply = 0
                else:
                    applied_to_shield = self.player.shield
                    to_apply -= self.player.shield
                    self.player.shield = 0
            if to_apply > 0:
                self.player.hp = max(0, self.player.hp - to_apply)
                applied_to_hp = to_apply

            if crit:
                print(f"{enemy.name} lands a CRITICAL HIT for {dmg}! (Shield absorbed {applied_to_shield}, HP damage {applied_to_hp})")
            else:
                print(f"{enemy.name} hits you for {dmg} (Shield absorbed {applied_to_shield}, HP damage {applied_to_hp}).")
        else:
            print(f"{enemy.name} fires but misses you.")

# -------------------------
# Entry point
# -------------------------
def main():
    game = Game()
    game.main_menu()


if __name__ == "__main__":
    main()
