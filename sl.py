import random
import json
import os

# -----------------------------
# JSON save file
# -----------------------------
SAVE_FILE = "player_data.json"

# -----------------------------
# Rank & level system
# -----------------------------
RANKS = ["E", "D", "C", "B", "A", "S"]

# -----------------------------
# Player default
# -----------------------------
DEFAULT_PLAYER = {
    "name": "Shadow Hunter",
    "level": 1,
    "xp": 0,
    "xp_cap": 20,
    "rank": "E",
    "stats": {"STR": 5, "VIT": 5, "AGI": 5, "CRIT": 5},
    "max_hp": 50,
    "current_hp": 50,
    "inventory": []
}

player = {}

# -----------------------------
# Enemy definitions
# -----------------------------
ENEMIES = [
    {"name": "Goblin", "rank": "E", "health": 15, "attack_min": 3, "attack_max": 6, "crit": 0.1},
    {"name": "Lesser Spider", "rank": "D", "health": 18, "attack_min": 4, "attack_max": 7, "crit": 0.1},
    {"name": "Skeleton Warrior", "rank": "C", "health": 20, "attack_min": 4, "attack_max": 8, "crit": 0.15},
    {"name": "Orc", "rank": "B", "health": 25, "attack_min": 5, "attack_max": 10, "crit": 0.15},
    {"name": "Troll", "rank": "A", "health": 30, "attack_min": 6, "attack_max": 12, "crit": 0.2},
]

BOSSES = [
    {"name": "Dungeon Boss", "rank_offset": 2, "health": 80, "attack_min": 8, "attack_max": 15, "crit": 0.2}
]

ROOM_TYPES = ["monster", "treasure", "trap", "boss"]

# -----------------------------
# Prologue narrative
# -----------------------------
def prologue():
    print("\n" + "="*60)
    print("You are a hunter of rank E, venturing into the shadows of a hidden dungeon.")
    print("Rumors speak of monsters and treasures beyond imagination, yet death awaits every corner.\n")
    print("Your heartbeat echoes as you step into the first room. Tonight, you fight not just for gold,")
    print("but for survival, and for the chance to grow stronger than ever.")
    print("="*60 + "\n")

# -----------------------------
# Load / Save functions
# -----------------------------
def load_player():
    global player
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            player = json.load(f)
        print(f"Loaded player data: Level {player['level']} {player['rank']} {player['name']}")
    else:
        player = DEFAULT_PLAYER.copy()
        save_player()
        print("Created new player.")

def save_player():
    with open(SAVE_FILE, "w") as f:
        json.dump(player, f, indent=2)
    print("[Game Saved]")

# -----------------------------
# Leveling system
# -----------------------------
def xp_cap(level):
    return 20 * (2 ** (level - 1))

def gain_xp(amount):
    player['xp'] += amount
    while player['xp'] >= player['xp_cap']:
        player['xp'] -= player['xp_cap']
        level_up()
    print(f"XP: {player['xp']} / {player['xp_cap']}")

def level_up():
    player['level'] += 1
    player['xp_cap'] = xp_cap(player['level'])
    player['max_hp'] += 10
    player['current_hp'] = player['max_hp']
    print(f"\n*** You leveled up to Level {player['level']}! ***")
    print(f"Max HP increased to {player['max_hp']}")
    choose_stat()
    save_player()

def choose_stat():
    print("Choose a stat to increase:")
    print("1. Strength (+2 Attack)")
    print("2. Vitality (+10 HP)")
    print("3. Agility (+3% Hit/Dodge chance)")
    print("4. Critical (+3% Crit chance)")
    choice = input("Enter number: ").strip()
    if choice == "1":
        player['stats']['STR'] += 2
        print("Strength increased by 2!")
    elif choice == "2":
        player['stats']['VIT'] += 1
        player['max_hp'] += 10
        player['current_hp'] = player['max_hp']
        print("Vitality increased by 1! Max HP +10")
    elif choice == "3":
        player['stats']['AGI'] += 1
        print("Agility increased by 1! Hit/Dodge chance improved")
    elif choice == "4":
        player['stats']['CRIT'] += 1
        print("Critical increased by 1! Crit chance improved")
    else:
        print("Invalid choice, defaulting to Strength +2")
        player['stats']['STR'] += 2

# -----------------------------
# Inventory
# -----------------------------
def show_inventory():
    if player['inventory']:
        print("Inventory:")
        for idx, item in enumerate(player['inventory'],1):
            print(f"{idx}. {item}")
    else:
        print("Inventory is empty.")

def use_item():
    if not player['inventory']:
        print("No items to use.")
        return
    show_inventory()
    choice = input("Enter item number to use: ").strip()
    if choice.isdigit():
        idx = int(choice)-1
        if 0 <= idx < len(player['inventory']):
            item = player['inventory'].pop(idx)
            if "Health Potion" in item:
                heal = int(item.split("+")[1].split()[0])
                player['current_hp'] = min(player['max_hp'], player['current_hp']+heal)
                print(f"Used {item}. HP restored to {player['current_hp']}")
            elif "Shadow Stone" in item:
                print(f"You feel a dark power from {item} surge through you!")
        else:
            print("Invalid choice.")
    else:
        print("Invalid input.")

# -----------------------------
# Combat
# -----------------------------
def combat(enemy):
    print(f"\n!!! A ({enemy['rank']}) {enemy['name']} appears !!!\n")
    enemy_hp = enemy['health']
    while enemy_hp > 0 and player['current_hp'] > 0:
        print(f"Your HP: {player['current_hp']} | {enemy['name']} HP: {enemy_hp}")
        action = input("Choose action: [attack] [use item] [run] ").strip().lower()
        if action == "attack":
            # Player attack
            if random.random() < 0.85 + player['stats']['AGI']*0.01:
                damage = random.randint(5+player['stats']['STR'], 10+player['stats']['STR'])
                if random.random() < 0.1 + player['stats']['CRIT']*0.01:
                    damage *= 2
                    print("CRITICAL HIT!")
                enemy_hp -= damage
                print(f"You dealt {damage} damage to {enemy['name']}.")
            else:
                print("You missed!")
            # Enemy attack
            if enemy_hp > 0:
                if random.random() < 0.8:
                    edamage = random.randint(enemy['attack_min'], enemy['attack_max'])
                    if random.random() < enemy['crit']:
                        edamage *=2
                        print(f"{enemy['name']} CRITICAL HIT!")
                    player['current_hp'] -= edamage
                    print(f"{enemy['name']} hits you for {edamage} damage!")
                else:
                    print(f"{enemy['name']} missed!")
        elif action == "use item":
            use_item()
        elif action == "run":
            if random.random() < 0.5:
                print("Escaped!")
                return
            else:
                print("Failed to escape!")
        else:
            print("Invalid action.")
    if player['current_hp'] <= 0:
        print("You died...")
        player['inventory'] = []
        player['current_hp'] = player['max_hp']
        save_player()
        print("You respawn at the dungeon entrance, your stats intact but inventory lost.")
        return
    print(f"You defeated the {enemy['name']}!")
    xp_values = {"E":5,"D":10,"C":20,"B":40,"A":80,"S":150}
    gain_xp(xp_values.get(enemy['rank'],10))
    save_player()

# -----------------------------
# Dungeon generation
# -----------------------------
def generate_dungeon():
    num_rooms = random.randint(4,10)
    dungeon = []
    for _ in range(num_rooms):
        room_type = random.choices(
            ROOM_TYPES,
            weights=[0.6,0.2,0.1,0.1], k=1
        )[0]
        dungeon.append(room_type)
    return dungeon

# -----------------------------
# Enemy selection
# -----------------------------
def select_enemy():
    possible = [e for e in ENEMIES if RANKS.index(e['rank']) <= RANKS.index(player['rank'])+2]
    enemy = random.choice(possible)
    # 10% chance enemy is enchanted: increase stats
    if random.random() < 0.1:
        enemy = enemy.copy()
        enemy['health'] += 5
        enemy['attack_min'] += 2
        enemy['attack_max'] += 2
        enemy['name'] = "Enchanted " + enemy['name']
    return enemy

# -----------------------------
# Dungeon loop
# -----------------------------
def start_dungeon():
    print("\n[Dungeon generated! You enter a dark corridor...]")
    dungeon = generate_dungeon()
    room_count = 0
    while room_count < len(dungeon) and player['current_hp'] > 0:
        room = dungeon[room_count]
        room_count +=1
        print(f"\n--- Room {room_count} ---")
        if room == "monster":
            enemy = select_enemy

