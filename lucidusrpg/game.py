import random
import json
import os

# -----------------------------
# Terminal Colors
# -----------------------------
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"

SHADOW_STONE_EFFECTS = [
    f"{MAGENTA}Restore 30 HP{RESET}",
    f"{MAGENTA}Gain +5 STR this fight{RESET}",
    f"{MAGENTA}Gain +5 AGI this fight{RESET}",
    f"{MAGENTA}Gain +5 VIT this fight{RESET}",
    f"{MAGENTA}Double crit chance for 1 attack{RESET}",
    f"{MAGENTA}Immediate small heal +10 HP{RESET}",
    f"{MAGENTA}Ignore enemy defense this attack{RESET}",
    f"{MAGENTA}Next attack guaranteed critical{RESET}",
    f"{MAGENTA}Block next enemy attack completely{RESET}",
    f"{MAGENTA}Gain +2 XP instantly{RESET}"
]




# -----------------------------
# JSON save file
# -----------------------------
SAVE_FILE = "player_data.json"
LORE_FILE = "lore.txt"

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
    "inventory": [],
    "equipped_weapon": None,
    "equipped_armor": {"helmet": None, "chest": None, "leggings": None, "boots": None},
    "special_counter": 0
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
    {"name": "Wolf Pack", "rank": "D", "health": 22, "attack_min": 3, "attack_max": 6, "crit": 0.1},
    {"name": "Dark Mage", "rank": "C", "health": 18, "attack_min": 5, "attack_max": 9, "crit": 0.15},
    {"name": "Bandit Leader", "rank": "B", "health": 28, "attack_min": 6, "attack_max": 12, "crit": 0.2},
    {"name": "Giant Rat", "rank": "E", "health": 12, "attack_min": 2, "attack_max": 5, "crit": 0.05},
    {"name": "Wraith", "rank": "A", "health": 35, "attack_min": 7, "attack_max": 14, "crit": 0.25},
    {"name": "Harpy", "rank": "C", "health": 20, "attack_min": 4, "attack_max": 8, "crit": 0.15},
    {"name": "Dark Knight", "rank": "B", "health": 30, "attack_min": 6, "attack_max": 12, "crit": 0.2},
    {"name": "Slime King", "rank": "D", "health": 18, "attack_min": 3, "attack_max": 7, "crit": 0.1}
]

BOSSES = [
    {"name": "Dragon", "rank_offset": 2, "health": 100, "attack_min": 10, "attack_max": 20, "crit": 0.25},
    {"name": "Cerberus", "rank_offset": 2, "health": 90, "attack_min": 8, "attack_max": 18, "crit": 0.2},
    {"name": "Ancient Deity", "rank_offset": 2, "health": 120, "attack_min": 12, "attack_max": 24, "crit": 0.3}
]

ROOM_TYPES = ["monster","treasure","trap","intermission","boss"]

# -----------------------------
# Prologue
# -----------------------------
def prologue():
    print("\n" + "="*60)
    print(f"{CYAN}You are a hunter of rank E, venturing into the shadows of a hidden dungeon.")
    print("Rumors speak of monsters and treasures beyond imagination, yet death awaits every corner.\n")
    print("Your heartbeat echoes as you step into the first room. Tonight, you fight not just for gold,")
    print("but for survival, and for the chance to grow stronger than ever." + RESET)
    print("="*60 + "\n")

# -----------------------------
# Load/Save
# -----------------------------
def load_player():
    global player
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE,"r") as f:
            player=json.load(f)
        print(f"Loaded player data: Level {player['level']} {player['rank']} {player['name']}")
    else:
        player = DEFAULT_PLAYER.copy()
        save_player()
        print("Created new player.")

def save_player():
    with open(SAVE_FILE,"w") as f:
        json.dump(player,f,indent=2)
    print("[Game Saved]")

# -----------------------------
# Leveling
# -----------------------------
def xp_cap(level):
    return 20*(2**(level-1))

def gain_xp(amount):
    player['xp'] += amount
    while player['xp'] >= player['xp_cap']:
        player['xp'] -= player['xp_cap']
        level_up()
    print(f"XP: {player['xp']} / {player['xp_cap']}")

def level_up():
    player['level'] +=1
    player['xp_cap'] = xp_cap(player['level'])
    player['max_hp'] +=10
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
    if choice=="1":
        player['stats']['STR']+=2
        print("Strength increased by 2!")
    elif choice=="2":
        player['stats']['VIT']+=1
        player['max_hp']+=10
        player['current_hp'] = player['max_hp']
        print("Vitality increased by 1! Max HP +10")
    elif choice=="3":
        player['stats']['AGI']+=1
        print("Agility increased by 1! Hit/Dodge chance improved")
    elif choice=="4":
        player['stats']['CRIT']+=1
        print("Critical increased by 1! Crit chance improved")
    else:
        print("Invalid choice, defaulting to Strength +2")
        player['stats']['STR']+=2

# -----------------------------
# Inventory / Items
# -----------------------------
def show_inventory():
    if player['inventory']:
        print("Inventory:")
        for idx,item in enumerate(player['inventory'],1):
            if isinstance(item,str):
                print(f"{idx}. {item}")
            else:
                stats = " / ".join([f"{k}:{v}" for k,v in item.items() if k!="type"])
                print(f"{idx}. {item['name']} ({stats})")
    else:
        print("Inventory is empty.")

def use_item():
    if not player['inventory']:
        print("No items to use.")
        return
    show_inventory()
    choice=input("Enter item number to use: ").strip()
    if choice.isdigit():
        idx=int(choice)-1
        if 0<=idx<len(player['inventory']):
            item=player['inventory'].pop(idx)
            if isinstance(item,str):
                if "Health Potion" in item:
                    heal=int(item.split("+")[1].split()[0])
                    player['current_hp']=min(player['max_hp'],player['current_hp']+heal)
                    print(f"Used {item}. HP restored to {player['current_hp']}")
                elif "Shadow Stone" in item:
                    effect = random.choice(SHADOW_STONE_EFFECTS)
                    print(f"You activate the Shadow Stone: {effect}")
    
                    # Apply effect logic
                    if "Restore 30 HP" in effect:
                        player['current_hp'] = min(player['max_hp'], player['current_hp'] + 30)
            elif "Immediate small heal +10 HP" in effect:
                player['current_hp'] = min(player['max_hp'], player['current_hp'] + 10)
            elif "Gain +5 STR" in effect:
                player['stats']['STR'] += 5
            elif "Gain +5 AGI" in effect:
                player['stats']['AGI'] += 5
            elif "Gain +5 VIT" in effect:
                player['stats']['VIT'] += 5
            elif "Double crit chance" in effect:
                player['temp_double_crit'] = True
            elif "Ignore enemy defense" in effect:
                player['temp_ignore_defense'] = True
            elif "Next attack guaranteed critical" in effect:
                player['temp_guaranteed_crit'] = True
            elif "Block next enemy attack" in effect:
                player['temp_block_next_attack'] = True
            elif "Gain +2 XP" in effect:
                gain_xp(2)

                print(f"{YELLOW}Shadow Stone activated: {effect}{RESET}")
            else:
                print(f"You cannot use {item['name']} directly.")
        else:
            print("Invalid choice.")
    else:
        print("Invalid input.")

# -----------------------------
# Equip Weapons / Armor
# -----------------------------
def equip_item():
    show_inventory()
    choice = input("Enter item number to equip: ").strip()
    if not choice.isdigit(): return
    idx=int(choice)-1
    if idx<0 or idx>=len(player['inventory']): return
    item = player['inventory'][idx]
    if not isinstance(item, dict):
        print("Cannot equip this item.")
        return
    if item['type']=="weapon":
        player['equipped_weapon']=item
        player['inventory'].pop(idx)
        print(f"{GREEN}Equipped {item['name']}!{RESET}")
    elif item['type'] == "armor":
        slot = item['slot']
        # If something is already equipped in this slot, return it to inventory
        if player['equipped_armor'][slot] is not None:
            player['inventory'].append(player['equipped_armor'][slot])
        # Equip the new item
        player['equipped_armor'][slot] = item
        player['inventory'].pop(idx)
        print(f"{GREEN}Equipped {item['name']} in slot {slot}!{RESET}")
    else:
        print("Unknown item type.")

# -----------------------------
# Combat
# -----------------------------
def combat(enemies, boss=False):
    if not isinstance(enemies, list):
        enemies = [enemies]

    # Initialize temporary Shadow Stone effects
    player['temp_double_crit'] = False
    player['temp_guaranteed_crit'] = False
    player['temp_ignore_defense'] = False
    player['temp_block_next_attack'] = False
    player['temp_dodge'] = False

    print()
    for idx, e in enumerate(enemies, 1):
        rank = e.get('rank', 'E')  # default if missing
        print(f"{YELLOW}Enemy {idx} approaches!{RESET}")
        print(f"{RED}!!! ({rank}) {e['name']} appears !!!{RESET}\n")
        e['current_hp'] = e['health']

    while any(e['current_hp'] > 0 for e in enemies) and player['current_hp'] > 0:
        weapon_name = player['equipped_weapon']['name'] if player.get('equipped_weapon') else "None"
        print(f"{CYAN}Your HP: {player['current_hp']} | Weapon: {weapon_name}{RESET}")

        for idx, e in enumerate(enemies, 1):
            if e['current_hp'] > 0:
                print(f"{RED}{e['name']} HP: {e['current_hp']}{RESET}")

        action = input(f"{YELLOW}Actions: [attack] [use item] [dodge] [special] [run]\nChoose action: {RESET}").strip().lower()

        if action not in ["attack","use item","dodge","special","run"]:
            print(f"{RED}Invalid input. Try again.{RESET}")
            continue  # does not consume a turn

        # Player attacks
        if action == "attack":
            for e in enemies:
                if e['current_hp'] <= 0:
                    continue
                hit_chance = 0.85 + player['stats']['AGI']*0.01
                if random.random() < hit_chance:
                    weapon = player['equipped_weapon'] if player.get('equipped_weapon') else {'min_damage':5,'max_damage':10}
                    damage = random.randint(weapon['min_damage'], weapon['max_damage']) + player['stats']['STR']

                    # Apply Shadow Stone effects
                    if player.get('temp_double_crit', False) and random.random() < 0.2:
                        damage *= 2
                        print(f"{MAGENTA}Shadow Stone Effect: Double Crit!{RESET}")
                    if player.get('temp_guaranteed_crit', False):
                        damage *= 2
                        print(f"{MAGENTA}Shadow Stone Effect: Guaranteed Crit!{RESET}")
                        player['temp_guaranteed_crit'] = False  # one-time

                    e['current_hp'] -= damage
                    print(f"{GREEN}You dealt {damage} damage to {e['name']}.{RESET}")
                else:
                    print(f"{RED}You missed!{RESET}")

        elif action == "use item":
            use_item()

        elif action == "dodge":
            print(f"{YELLOW}You prepare to dodge the next attack!{RESET}")
            player['temp_dodge'] = True

        elif action == "special":
            if player.get('special_counter', 0) >= 3 or boss:
                print(f"{CYAN}You unleash your special ability!{RESET}")
                for e in enemies:
                    if e['current_hp'] <= 0:
                        continue
                    damage = random.randint(10+player['stats']['STR'], 20+player['stats']['STR'])
                    e['current_hp'] -= damage
                    print(f"{GREEN}Special hits {e['name']} for {damage} damage!{RESET}")
                if not boss:
                    player['special_counter'] = 0
            else:
                print(f"{RED}Special not ready. {3 - player.get('special_counter',0)} more normal fights needed.{RESET}")

        elif action == "run":
            if boss:
                print(f"{RED}Cannot run from a boss!{RESET}")
            elif random.random() < 0.5:
                print(f"{CYAN}You successfully escaped!{RESET}")
                return
            else:
                print(f"{RED}Failed to escape!{RESET}")

        # Enemy turn
        for e in enemies:
            if e['current_hp'] <= 0:
                continue
            if random.random() < 0.8:
                if player.get('temp_dodge', False):
                    if random.random() < 0.5 + player['stats']['AGI']*0.01:
                        print(f"{CYAN}You dodged {e['name']}'s attack!{RESET}")
                        continue
                    player['temp_dodge'] = False
                edamage = random.randint(e['attack_min'], e['attack_max'])
                if random.random() < e['crit']:
                    edamage *= 2
                    print(f"{RED}{e['name']} CRITICAL HIT!{RESET}")
                if player.get('equipped_armor'):
                    armor = player['equipped_armor']
                    edamage = max(0, edamage - armor.get('defense', 0))
                player['current_hp'] -= edamage
                print(f"{RED}{e['name']} hits you for {edamage} damage!{RESET}")
            else:
                print(f"{CYAN}{e['name']} missed!{RESET}")

    if player['current_hp'] <= 0:
        print(f"{RED}You died...{RESET}")
        player['inventory'] = []
        player['current_hp'] = player['max_hp']
        save_player()
        while True:
            choice = input(f"{YELLOW}Do you want to [continue] or [save & quit]? {RESET}").strip().lower()
            if choice == "continue":
                return
            elif choice == "save & quit":
                save_player()
                exit()
            else:
                print(f"{RED}Invalid input.{RESET}")
        return

    print(f"{GREEN}You defeated the enemy!{RESET}")
    if not boss:
        for e in enemies:
            xp_values = {"E":5,"D":10,"C":20,"B":40,"A":80,"S":150}
            gain_xp(xp_values.get(e.get('rank','E'),10))
        player['special_counter'] = player.get('special_counter', 0) + 1
    save_player()


# -----------------------------
# Dungeon generation
# -----------------------------
def generate_dungeon():
    num_rooms = random.randint(5,15)
    dungeon = []
    boss_inserted = False
    for _ in range(num_rooms):
        room_type = random.choices(
            ROOM_TYPES,
            weights=[0.55,0.2,0.1,0.1,0.05], k=1
        )[0]
        if room_type=="boss":
            if boss_inserted:
                room_type="monster"
            else:
                boss_inserted=True
        dungeon.append(room_type)
    if not boss_inserted:
        dungeon[-1]="boss"
    return dungeon

# -----------------------------
# Select enemy
# -----------------------------
def select_enemy():
    possible = [e for e in ENEMIES if RANKS.index(e['rank']) <= RANKS.index(player['rank'])+2]
    enemy=random.choice(possible)
    if random.random()<0.1:
        enemy=enemy.copy()
        enemy['health']+=5
        enemy['attack_min']+=2
        enemy['attack_max']+=2
        enemy['name']="Enchanted "+enemy['name']
    return enemy

# -----------------------------
# Story/Intermission rooms
# -----------------------------
def story_room():
    if not os.path.exists(LORE_FILE):
        print(f"{CYAN}You see nothing but silence...{RESET}")
        return
    with open(LORE_FILE,"r") as f:
        lore=f.read().split("\n\n")
    paragraph=random.choice(lore)
    print(f"{CYAN}{paragraph}{RESET}")
    input("Press Enter to leave this story room...")

# -----------------------------
# Dungeon loop
# -----------------------------
def start_dungeon():
    print(f"{CYAN}[Dungeon generated! You enter a dark corridor...]{RESET}")
    dungeon=generate_dungeon()
    for room_num,room in enumerate(dungeon,1):
        print(f"\n--- Room {room_num} ---")
        if room=="monster":
            enemy = select_enemy()
            combat(enemy)
        elif room=="treasure":
            loot = random.choice(["Health Potion +20","Shadow Stone"])
            player['inventory'].append(loot)
            print(f"You found {loot}!")
            save_player()
        elif room=="trap":
            damage=random.randint(5,15)
            player['current_hp']-=damage
            print(f"A trap hits you for {damage} damage!")
            if player['current_hp']<=0:
                combat([],boss=False)
            save_player()
        elif room=="intermission":
            story_room()
        elif room=="boss":
            boss=random.choice(BOSSES)
            boss_copy=boss.copy()
            boss_copy['rank']=RANKS[min(RANKS.index(player['rank'])+2,len(RANKS)-1)]
            combat(boss_copy,boss=True)
    print(f"{GREEN}Dungeon cleared!{RESET}")
    input("Press Enter to return to the menu...")

# ========================
# RAID SYSTEM FRAMEWORK
# ========================

import os
import random

# Raid configuration
RAIDS = {
    1: {
        "name": "The Shattered Depths",
        "rooms": 30,
        "boss_rooms": [10, 25],
        "lore_file": "raid1_lore.txt"
    },
    2: {
        "name": "The Ashen Citadel",
        "rooms": 40,
        "boss_rooms": [15, 35],
        "lore_file": "raid2_lore.txt"
    }
}

# Function to load raid lore
def load_raid_lore(file_path):
    if not os.path.exists(file_path):
        return {}
    lore = {}
    with open(file_path, "r") as f:
        current_key = None
        for line in f:
            line = line.strip()
            if line.startswith("##"):  # Lore section header
                current_key = line[2:].strip()
                lore[current_key] = []
            elif current_key:
                lore[current_key].append(line)
    return {k: "\n".join(v) for k, v in lore.items()}

# Generate normal raid enemies (keep dungeon enemies separate)
def generate_raid_enemies():
    enemy_pool = [
        {"name": "Goblin", "health": 15, "attack_min": 3, "attack_max": 6, "crit": 0.1, "rank": "E"},
        {"name": "Lesser Spider", "health": 12, "attack_min": 2, "attack_max": 5, "crit": 0.05, "rank": "D"},
        {"name": "Skeleton Warrior", "health": 20, "attack_min": 4, "attack_max": 8, "crit": 0.1, "rank": "C"}
    ]
    num_enemies = random.randint(1, 3)
    return [random.choice(enemy_pool).copy() for _ in range(num_enemies)]

# Puzzle room system
def puzzle_room(lore_text):
    print(f"{MAGENTA}{lore_text}{RESET}")
    print("Solve the puzzle to continue. (Guess the number between 1-5)")
    number = random.randint(1,5)
    attempts = 0
    while True:
        guess = input("Enter your guess: ").strip()
        if not guess.isdigit():
            print(f"{RED}Invalid input.{RESET}")
            continue
        guess = int(guess)
        attempts += 1
        if guess == number:
            print(f"{GREEN}You solved the puzzle!{RESET}")
            return True
        else:
            print(f"{RED}Wrong! Try again.{RESET}")
        if attempts >= 3:
            print(f"{RED}The puzzle overwhelms you, but you proceed cautiously.{RESET}")
            return False

# Raid boss combat system
def raid_boss_combat(boss):
    print(f"{RED}Boss: {boss['name']} appears!{RESET}")
    boss['current_hp'] = boss['health']
    damage_phase_active = False
    damage_phase_counter = 0
    turns_in_phase = 0

    while boss['current_hp'] > 0 and player['current_hp'] > 0:
        input(f"\nPress Enter to continue your turn against {boss['name']}...")

        # Player attacks
        weapon = player.get('equipped_weapon')
        if not weapon:
            print("you have no weapon equipped! You swing your fists instead.")
            weapon = {'min_damage': 5, 'max_damage': 10, 'name': 'Fists'}

        damage = random.randint(weapon['min_damage'], weapon['max_damage']) + player['stats']['STR']
        boss['current_hp'] -= damage
        print(f"You hit {boss['name']} for {damage} damage! Boss HP: {max(0,boss['current_hp'])}")

        # Damage phase triggering
        if not damage_phase_active and random.random() < 0.3:
            damage_phase_active = True
            damage_phase_counter = random.randint(2,4)
            turns_in_phase = 0
            print(f"{RED}{boss['name']} enters a damage phase! You must dodge attacks!{RESET}")

        # Boss attacks if damage phase active
        if damage_phase_active:
            print(f"{RED}{boss['name']} attacks! Solve the dodge puzzle to avoid damage.{RESET}")
            dodge_number = random.randint(1,3)
            guess = input("Guess the correct number (1-3) to dodge: ").strip()
            if guess.isdigit() and int(guess) == dodge_number:
                print(f"{GREEN}You dodged the attack!{RESET}")
            else:
                boss_attack = random.randint(boss['attack_min'], boss['attack_max'])
                if player.get('equipped_armor'):
                    armor = player['equipped_armor']
                    boss_attack = max(0, boss_attack - armor.get('defense',0))
                player['current_hp'] -= boss_attack
                print(f"{RED}{boss['name']} hits you for {boss_attack} damage!{RESET} HP: {player['current_hp']}")
            turns_in_phase += 1
            if turns_in_phase >= damage_phase_counter:
                damage_phase_active = False

    if player['current_hp'] <= 0:
        print(f"{RED}You died!{RESET}")
        player['current_hp'] = player['max_hp']
        save_player()
    else:
        print(f"{GREEN}You defeated {boss['name']}!{RESET}")
        # Optional: drop exotic loot
        if random.random() < 0.05:
            loot = {"name":"Exotic Weapon", "min_damage":20,"max_damage":35}
            player['inventory'].append(loot)
            print(f"{MAGENTA}You received an exotic weapon: {loot['name']}!{RESET}")


# Raid main function
def start_raid(raid_id):
    raid = RAIDS[raid_id]
    lore = load_raid_lore(raid["lore_file"])
    print(f"\n{CYAN}=== RAID: {raid['name']} ==={RESET}")
    print(lore.get("intro", "The air grows heavy as you step into the raid..."))

    room = 1
    while room <= raid["rooms"]:
        input(f"\nPress Enter to enter Raid Room {room}...")
        print(f"\n--- Raid Room {room} ---")

        # Boss check
        if room in raid["boss_rooms"]:
            print(f"{RED}A Boss blocks your path!{RESET}")
            print(lore.get(f"boss_{room}", "The boss looms over you..."))
            raid_boss_combat({"name": f"Boss {room}", "max_hp": 50 + room*5, "attack_min":5, "attack_max":10})
            room += 1
            continue

        # Puzzle room every 7th room
        if room % 7 == 0:
            solved = False
            extra_attempts = 3
            while not solved:
                success = puzzle_room(lore.get(f"puzzle_{room}", "A strange mechanism hums before you."))
                if success:
                    solved = True
                else:
                    # Deal small damage and give extra attempts
                    player['current_hp'] -= 5
                    print(f"{RED}You take 5 damage for failing the puzzle! Current HP: {player['current_hp']}{RESET}")
                    extra_attempts -= 1
                    if extra_attempts <= 0:
                        print(f"{RED}You finally force your way through the puzzle.{RESET}")
                        solved = True

        else:
            # Normal enemies
            enemies = generate_raid_enemies()
            print("Combat encounter!")
            for e in enemies:
                print(f"{e['name']} appears!")
            combat(enemies)  # Reuse dungeon combat function

        room += 1

    print(f"\n{GREEN}You have completed {raid['name']}!{RESET}")
    print(lore.get("outro", "The raid echoes with silence as you emerge victorious..."))



# Raid menu integration
def raid_menu():
    print("\n=== Raid Menu ===")
    for raid_id, raid in RAIDS.items():
        print(f"{raid_id}. {raid['name']} ({raid['rooms']} rooms)")
    print("0. Back")
    choice = input("Choose a raid: ").strip()
    if choice == "0":
        return
    if choice.isdigit() and int(choice) in RAIDS:
        start_raid(int(choice))
    else:
        print("Invalid choice.")

# ========================
# RAID LOOT AND EXOTIC ITEMS
# ========================

# Exotic weapon pool for raids
RAID_EXOTIC_WEAPONS = [
    {"name":"Void Reaver", "min_damage":25, "max_damage":40},
    {"name":"Celestial Fang", "min_damage":30, "max_damage":45},
    {"name":"Stormbreaker", "min_damage":28, "max_damage":42},
    {"name":"Eclipse Edge", "min_damage":32, "max_damage":50}
]

# Special Shadow Stone effects in raids (purple text)
RAID_SHADOW_STONE_EFFECTS = [
    "Double Crit Chance", 
    "Guaranteed Crit Next Attack", 
    "Ignore Enemy Defense", 
    "Heal +20 HP", 
    "Gain Extra Turn", 
    "Reflect Next Damage", 
    "Boost STR by 3", 
    "Boost AGI by 3", 
    "Shield 15 Damage", 
    "Instant Kill Minor Enemy"
]

# Function to apply a Shadow Stone effect in raids
def apply_raid_shadowstone():
    effect = random.choice(RAID_SHADOW_STONE_EFFECTS)
    print(f"{MAGENTA}Shadow Stone Effect Activated: {effect}!{RESET}")

    if effect == "Double Crit Chance":
        player['temp_double_crit'] = True
    elif effect == "Guaranteed Crit Next Attack":
        player['temp_guaranteed_crit'] = True
    elif effect == "Ignore Enemy Defense":
        player['temp_ignore_defense'] = True
    elif effect == "Heal +20 HP":
        player['current_hp'] = min(player['max_hp'], player['current_hp'] + 20)
        print(f"{GREEN}Healed 20 HP!{RESET}")
    elif effect == "Gain Extra Turn":
        player['extra_turn'] = True
    elif effect == "Reflect Next Damage":
        player['temp_reflect'] = True
    elif effect == "Boost STR by 3":
        player['stats']['STR'] += 3
    elif effect == "Boost AGI by 3":
        player['stats']['AGI'] += 3
    elif effect == "Shield 15 Damage":
        player['temp_shield'] = 15
    elif effect == "Instant Kill Minor Enemy":
        player['temp_instant_kill'] = True

# ========================
# RAID BOSS COMBAT SYSTEM
# ========================
def raid_boss_combat(boss):
    """
    Handles multi-phase raid boss combat with dodge-based puzzle mechanics.
    boss: dict containing boss info: name, max_hp, phases (list of dicts)
    """
    print(f"\n{RED}--- Boss Encounter: {boss['name']} ---{RESET}")
    boss['current_hp'] = boss['max_hp']
    phase_index = 0
    puzzles_completed = 0
    damage_phase_active = False
    damage_phase_turns = 0

    while boss['current_hp'] > 0 and player['current_hp'] > 0:
        # Check if a new damage phase should trigger
        if not damage_phase_active and (puzzles_completed >= 4 or boss.get('enemies_killed',0) >= 10):
            damage_phase_active = True
            damage_phase_turns = random.randint(1,5)
            print(f"{RED}Boss enters a damage phase! You must dodge carefully.{RESET}")

        print(f"\nYour HP: {player['current_hp']} | Boss HP: {boss['current_hp']}")
        print("Actions: [attack] [use item] [dodge] [special]")

        action = input("Choose action: ").strip().lower()
        if action not in ['attack','use item','dodge','special']:
            print(f"{RED}Invalid input. Try again.{RESET}")
            continue

        # Player action
        if action == "attack":
            weapon = player.get('equipped_weapon', {'min_damage':5,'max_damage':10,'name':'Fists'})
            damage = random.randint(weapon['min_damage'], weapon['max_damage']) + player['stats']['STR']

            # Shadow Stone effects
            if player.get('temp_double_crit', False) and random.random() < 0.2:
                damage *= 2
                print(f"{MAGENTA}Shadow Stone Effect: Double Crit!{RESET}")
            if player.get('temp_guaranteed_crit', False):
                damage *= 2
                print(f"{MAGENTA}Shadow Stone Effect: Guaranteed Crit!{RESET}")
                player['temp_guaranteed_crit'] = False

            boss['current_hp'] -= damage
            print(f"You deal {damage} damage to {boss['name']}!")

        elif action == "use item":
            use_item()

        elif action == "dodge":
            player['temp_dodge'] = True
            print("You prepare to dodge the next attack!")

        elif action == "special":
            if player.get('special_counter',0) >= 3:
                damage = random.randint(10+player['stats']['STR'], 20+player['stats']['STR'])
                boss['current_hp'] -= damage
                print(f"Special hits {boss['name']} for {damage} damage!")
                player['special_counter'] = 0
            else:
                print(f"Special not ready. {3 - player.get('special_counter',0)} more normal fights needed.")

        # Boss attack / dodge puzzle
        if damage_phase_active:
            puzzle_number = random.randint(1,10)
            print(f"{RED}Boss prepares a powerful attack! Solve the puzzle to dodge.{RESET}")
            try:
                guess = int(input("Pick a number between 1-10: "))
            except ValueError:
                guess = 0
            if guess == puzzle_number or player.get('temp_dodge',False):
                print(f"{GREEN}You dodged the attack!{RESET}")
            else:
                boss_damage = random.randint(10,20)
                player['current_hp'] -= boss_damage
                print(f"{RED}Boss hits you for {boss_damage} damage!{RESET}")

            damage_phase_turns -= 1
            player['temp_dodge'] = False
            if damage_phase_turns <= 0:
                damage_phase_active = False
                print(f"{CYAN}Damage phase ends. You can breathe again...{RESET}")

    if player['current_hp'] <= 0:
        print(f"{RED}You died...{RESET}")
        player['current_hp'] = player['max_hp']
        save_player()
        while True:
            choice = input("Do you want to [continue] or [save & quit]? ").strip().lower()
            if choice == "continue":
                return
            elif choice == "save & quit":
                save_player()
                exit()
            else:
                print("Invalid input.")
    else:
        print(f"{GREEN}You defeated {boss['name']}!{RESET}")
        # Rare chance for exotic item
        if random.random() < 0.05:
            exotic_weapon = {"name":"Exotic Blade","min_damage":15,"max_damage":25}
            player['inventory'].append(exotic_weapon)
            print(f"{MAGENTA}You found an EXOTIC WEAPON: {exotic_weapon['name']}!{RESET}")
        save_player()


# -----------------------------
# Main loop
# -----------------------------
if __name__=="__main__":
    prologue()
    load_player()
    while True:
        print(f"\n{BLUE}=== Dungeon Menu ==={RESET}")
        print("1. Enter Dungeon")
        print("2. Check Status / Inventory")
        print("3. Equip Weapon/Armor")
        print("4. Save & Quit")
        print("5. Enter Raid")
        choice = input("Choose an option: ").strip()
        if choice=="1":
            start_dungeon()
        elif choice=="2":
            print(f"{BLUE}Level {player['level']} {player['rank']} {player['name']}{RESET}")
            print(f"HP: {player['current_hp']} / {player['max_hp']}")
            print(f"XP: {player['xp']} / {player['xp_cap']}")
            print("Stats:", player['stats'])
            show_inventory()
        elif choice=="3":
            equip_item()
        elif choice=="4":
            save_player()
            print(f"{BLUE}Exiting game.{RESET}")
            break
        elif choice == "5":
            raid_menu()
        else:
            print(f"{RED}Invalid choice.{RESET}")

# -----------------------------
# ENEMY SCALING AND LOOT HELPER
# -----------------------------
def scale_enemy(enemy):
    """
    Returns a scaled copy of the enemy based on player level and rank.
    HP and attack are increased for a more challenging fight.
    """
    enemy = enemy.copy()  # avoid modifying original
    level_factor = 1 + (player['level'] * 0.15)  # 15% increase per player level
    enemy['current_hp'] = int(enemy['health'] * level_factor)
    enemy['attack_min'] = max(1, int(enemy['attack_min'] * level_factor))
    enemy['attack_max'] = max(enemy['attack_min'], int(enemy['attack_max'] * level_factor))
    return enemy

def drop_loot(enemy):
    """
    Generates loot for an enemy if the player survived the fight.
    Each enemy can drop 1-3 items from a weighted loot table.
    """
    loot_table = enemy.get('loot_table', [
        {"item": "Health Potion +20", "chance": 0.4},
        {"item": "Shadow Stone", "chance": 0.1},
        {"item": "Dagger", "chance": 0.05},
        {"item": "Leather Armor", "chance": 0.05}
    ])
    num_drops = random.randint(1,3)
    dropped = []
    for _ in range(num_drops):
        drop = random.choices(loot_table, weights=[i['chance'] for i in loot_table])[0]
        player['inventory'].append(drop['item'])
        dropped.append(drop['item'])
    if dropped:
        print(f"{GREEN}{enemy['name']} dropped: {', '.join(dropped)}{RESET}")

# -----------------------------
# HELPER TO SPAWN ENEMY WITH SCALING
# -----------------------------
def get_scaled_enemy():
    """Selects an enemy and scales it automatically."""
    enemy = select_enemy()  # use your existing select_enemy()
    return scale_enemy(enemy)

# -----------------------------
# OPTIONAL: CALL AFTER COMBAT
# -----------------------------
def reward_player_after_combat(enemy, boss=False):
    """
    Call this function after combat ends.
    Grants XP and loot only if player survived.
    """
    if player['current_hp'] > 0 and not boss:
        xp_values = {"E":5,"D":10,"C":20,"B":40,"A":80,"S":150}
        gain_xp(xp_values.get(enemy.get('rank','E'),10))
        drop_loot(enemy)
        # Increment special counter
        player['special_counter'] = player.get('special_counter',0)+1
    save_player()


# ========================
# RAID COMBAT & PUZZLE SYSTEM
# ========================

import random

# Raid enemies and loot pools
RAID_ENEMIES = {
    1: [
        {"name": "Shattered Goblin", "health": 30, "attack_min": 5, "attack_max": 10, "crit": 0.1, "rank": "D"},
        {"name": "Cave Fiend", "health": 40, "attack_min": 6, "attack_max": 12, "crit": 0.15, "rank": "C"},
    ],
    2: [
        {"name": "Ashen Soldier", "health": 35, "attack_min": 7, "attack_max": 14, "crit": 0.1, "rank": "D"},
        {"name": "Molten Brute", "health": 50, "attack_min": 8, "attack_max": 16, "crit": 0.2, "rank": "B"},
    ],
}

RAID_LOOT = {
    1: [
        {"name": "Shard Blade", "type": "weapon", "min_damage": 8, "max_damage": 15},
        {"name": "Mystic Helm", "type": "armor", "slot": "helmet", "defense": 5},
        {"name": "Shadow Stone", "type": "consumable", "effect": "random"},
    ],
    2: [
        {"name": "Ashen Sword", "type": "weapon", "min_damage": 10, "max_damage": 18},
        {"name": "Flame Chestplate", "type": "armor", "slot": "chest", "defense": 6},
        {"name": "Shadow Stone", "type": "consumable", "effect": "random"},
    ],
}

# Puzzle examples
RAID_PUZZLES = [
    {"prompt": "Guess the correct number between 1 and 5:", "answer": "3"},
    {"prompt": "Type the word 'shadow' backwards:", "answer": "wodahs"},
    {"prompt": "Enter the sum of 7 + 4:", "answer": "11"},
]

def raid_puzzle(room_id):
    print(f"{MAGENTA}Puzzle {room_id}: Solve it to proceed!{RESET}")
    puzzle = random.choice(RAID_PUZZLES)
    print(puzzle['prompt'])
    answer = input("Your answer: ").strip()
    if answer.lower() == puzzle['answer'].lower():
        print(f"{GREEN}Correct!{RESET}")
        return True
    else:
        print(f"{RED}Incorrect!{RESET}")
        return False

def raid_combat(enemies, boss=False):
    if not isinstance(enemies, list):
        enemies = [enemies]

    # Initialize temporary Shadow Stone effects
    player['temp_double_crit'] = False
    player['temp_guaranteed_crit'] = False
    player['temp_ignore_defense'] = False
    player['temp_block_next_attack'] = False
    player['temp_dodge'] = False

    print()
    for idx, e in enumerate(enemies, 1):
        rank = e.get('rank', 'D')
        print(f"Enemy {idx} approaches!")
        print(f"!!! ({rank}) {e['name']} appears !!!\n")
        e['current_hp'] = e['health']

    while any(e['current_hp'] > 0 for e in enemies) and player['current_hp'] > 0:
        weapon_name = player['equipped_weapon']['name'] if player['equipped_weapon'] else "None"
        print(f"Your HP: {player['current_hp']} | Weapon: {weapon_name}")
        for idx, e in enumerate(enemies,1):
            if e['current_hp'] > 0:
                print(f"{e['name']} HP: {e['current_hp']}")

        action = input(f"Actions: [attack] [use item] [dodge] [special] [run]\nChoose action: ").strip().lower()
        if action not in ["attack","use item","dodge","special","run"]:
            print(f"{RED}Invalid input. Try again.{RESET}")
            continue  # does not consume a turn

        # Player attacks
        if action == "attack":
            for e in enemies:
                if e['current_hp'] <= 0:
                    continue
                hit_chance = 0.85 + player['stats']['AGI']*0.01
                if random.random() < hit_chance:
                    weapon = player.get('equipped_weapon', {'min_damage':5,'max_damage':10})
                    damage = random.randint(weapon['min_damage'], weapon['max_damage']) + player['stats']['STR']

                    # Shadow Stone effects
                    if player.get('temp_double_crit', False) and random.random() < 0.2:
                        damage *= 2
                        print(f"{MAGENTA}Shadow Stone Effect: Double Crit!{RESET}")
                    if player.get('temp_guaranteed_crit', False):
                        damage *= 2
                        print(f"{MAGENTA}Shadow Stone Effect: Guaranteed Crit!{RESET}")
                        player['temp_guaranteed_crit'] = False

                    e['current_hp'] -= damage
                    print(f"You dealt {damage} damage to {e['name']}.")
                else:
                    print("You missed!")

        elif action == "use item":
            use_item()
        elif action == "dodge":
            print("You prepare to dodge the next attack!")
            player['temp_dodge'] = True
        elif action == "special":
            if player.get('special_counter',0) >= 3 or boss:
                print("You unleash your special ability!")
                for e in enemies:
                    if e['current_hp'] <= 0:
                        continue
                    damage = random.randint(10+player['stats']['STR'], 20+player['stats']['STR'])
                    e['current_hp'] -= damage
                    print(f"Special hits {e['name']} for {damage} damage!")
                if not boss:
                    player['special_counter'] = 0
            else:
                print(f"Special not ready. {3 - player.get('special_counter',0)} more normal fights needed.")

        elif action == "run":
            if boss:
                print("Cannot run from a boss!")
            elif random.random() < 0.5:
                print("You successfully escaped!")
                return
            else:
                print("Failed to escape!")

        # Enemy turn
        for e in enemies:
            if e['current_hp'] <= 0:
                continue
            if random.random() < 0.8:
                if player.get('temp_dodge',False):
                    if random.random() < 0.5 + player['stats']['AGI']*0.01:
                        print(f"You dodged {e['name']}'s attack!")
                        continue
                    player['temp_dodge'] = False
                edamage = random.randint(e['attack_min'], e['attack_max'])
                if random.random() < e['crit']:
                    edamage *= 2
                    print(f"{e['name']} CRITICAL HIT!")
                if player.get('equipped_armor'):
                    armor = player['equipped_armor']
                    edamage = max(0, edamage - armor.get('defense',0))
                player['current_hp'] -= edamage
                print(f"{e['name']} hits you for {edamage} damage!")
            else:
                print(f"{e['name']} missed!")

    if player['current_hp'] <= 0:
        print("You died in the raid...")
        player['current_hp'] = player['max_hp']
        save_player()
        while True:
            choice = input("Do you want to [continue] or [save & quit]? ").strip().lower()
            if choice == "continue":
                return
            elif choice == "save & quit":
                save_player()
                exit()
            else:
                print("Invalid input.")

    print(f"{GREEN}You defeated the raid enemies!{RESET}")

    # Gain XP only if not boss (optional)
    if not boss:
        for e in enemies:
            xp_values = {"E":5,"D":10,"C":20,"B":40,"A":80,"S":150}
            gain_xp(xp_values.get(e.get('rank','E'),10))
        player['special_counter'] = player.get('special_counter',0)+1

    # Loot drops
    for e in enemies:
        loot = random.choice(RAID_LOOT.get(player.get('current_raid',1), []))
        if loot:
            player['inventory'].append(loot)
            print(f"You found {loot['name']}!")

    save_player()

