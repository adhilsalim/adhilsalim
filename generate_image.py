import json
import random
import sys
from PIL import Image, ImageDraw, ImageFont

# --- Game Configuration ---
CANVAS_WIDTH = 400
CANVAS_HEIGHT = 600
CAR_WIDTH = 40
CAR_HEIGHT = 70
LANES = [CANVAS_WIDTH * 0.25, CANVAS_WIDTH * 0.5, CANVAS_WIDTH * 0.75]
MOVE_SPEED = 20
DOWNWARD_CAR_SPEED = 8
FORWARD_CAR_SPEED = -3

# --- Asset Colors & Styles ---
COLOR_PALETTE = {
    "player_car": "#f6e05e", "road": "#4a5568", "scenery_ground": "#a0522d",
    "lane_line": "#FFFFFF", "crash_text": "#f6e05e", "crash_bg": "rgba(0, 0, 0, 0.7)",
    "other_cars": ['#e53e3e', '#38b2ac', '#9f7aea', '#4299e1'],
    "tree_round": "#228B22", "tree_pine": "#2F4F4F", "tree_trunk": "#8B4513",
    "sand": "#F4A460", "pond": "#3182CE", "store": "#E53E3E",
    "store_roof": "#A0AEC0", "store_door": "#4A5568",
    "parked_cars": ['#A0AEC0', '#718096', '#4A5568']
}
# A simple font is used here. For GitHub Actions, you'd need to add a .ttf font file to your repo.
# For simplicity, we'll let Pillow use its default font if a specific one isn't found.
try:
    FONT_BIG = ImageFont.truetype("font.ttf", 40)
except IOError:
    FONT_BIG = ImageFont.load_default()

class Game:
    """Manages the game state and rendering."""

    def __init__(self, state):
        self.state = state
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_PALETTE["road"])
        self.draw = ImageDraw.Draw(self.image)

    def parse_commands(self, command_string):
        # Limit command length
        command_string = command_string.upper()[:20]
        if "RST" in command_string:
            return ["RST"]
        
        parsed = []
        import re
        matches = re.findall(r'([LRM])(\d*)', command_string)
        for command, count_str in matches:
            count = int(count_str) if count_str else 1
            for _ in range(count):
                parsed.append(command)
        return parsed

    def execute_commands(self, commands):
        if not commands or self.state['game_over']:
            if "RST" in commands: # Allow reset even if crashed
                 self.state = self.get_default_state()
            return

        for command in commands:
            if self.state['game_over']:
                break
            
            is_moving_forward = False
            boundary_crash = False

            if command == 'L':
                if self.state['player']['lane'] > 0:
                    self.state['player']['lane'] -= 1
                else:
                    boundary_crash = True
            elif command == 'R':
                if self.state['player']['lane'] < 2:
                    self.state['player']['lane'] += 1
                else:
                    boundary_crash = True
            elif command == 'M':
                is_moving_forward = True
                self.update_world()
            
            if self.check_collision() or boundary_crash:
                self.state['game_over'] = True

        self.state['player']['x'] = LANES[self.state['player']['lane']] - CAR_WIDTH / 2


    def update_world(self):
        # Move everything down
        for car in self.state['other_cars']:
            car['y'] += MOVE_SPEED + car['speed']
        for scenery in self.state['scenery']:
            scenery['y'] += MOVE_SPEED

        # Filter off-screen objects
        self.state['other_cars'] = [c for c in self.state['other_cars'] if c['y'] < CANVAS_HEIGHT + CAR_HEIGHT]
        self.state['scenery'] = [s for s in self.state['scenery'] if s['y'] < CANVAS_HEIGHT + 50]

        # Spawn new objects
        self.spawn_car()
        self.spawn_scenery()


    def spawn_car(self):
        if random.random() < 0.2: # 80% chance
            lane = random.randint(0, 2)
            new_car = {
                "lane": lane,
                "x": LANES[lane] - CAR_WIDTH / 2,
                "y": -CAR_HEIGHT * 2,
                "color": random.choice(COLOR_PALETTE['other_cars']),
                "speed": FORWARD_CAR_SPEED if lane == 1 else DOWNWARD_CAR_SPEED
            }
            # Prevent immediate overlap
            can_spawn = True
            for car in self.state['other_cars']:
                if car['lane'] == new_car['lane'] and new_car['y'] < car['y'] + CAR_HEIGHT * 2.5:
                    can_spawn = False
                    break
            if can_spawn:
                self.state['other_cars'].append(new_car)

    def spawn_scenery(self):
        if random.random() < 0.5: # 50% chance
            scenery_width = (CANVAS_WIDTH / 3) * 0.5
            side = 'left' if random.random() < 0.5 else 'right'
            types = ['tree_round', 'tree_pine', 'sand_patch', 'pond', 'store', 'parked_car']
            obj_type = random.choice(types)
            
            x_pos = random.randint(15, int(scenery_width - 25))
            if side == 'right':
                x_pos += CANVAS_WIDTH - scenery_width
            
            new_obj = {'type': obj_type, 'x': x_pos, 'y': -60}
            # Add dimensions and colors based on type
            if obj_type == 'tree_round':
                new_obj.update({'w': 25, 'h': 25, 'color': COLOR_PALETTE['tree_round']})
            elif obj_type == 'store':
                new_obj.update({'w': 60, 'h': 50, 'color': COLOR_PALETTE['store']})
            # ... add other types similarly
            self.state['scenery'].append(new_obj)


    def check_collision(self):
        px, py = self.state['player']['x'], self.state['player']['y']
        pw, ph = CAR_WIDTH, CAR_HEIGHT
        for car in self.state['other_cars']:
            cx, cy = car['x'], car['y']
            cw, ch = CAR_WIDTH, CAR_HEIGHT
            if px < cx + cw and px + pw > cx and py < cy + ch and py + ph > cy:
                return True
        return False

    def draw_frame(self):
        # Scenery ground
        scenery_width = int((CANVAS_WIDTH / 3) * 0.5)
        self.draw.rectangle([0, 0, scenery_width, CANVAS_HEIGHT], fill=COLOR_PALETTE['scenery_ground'])
        self.draw.rectangle([CANVAS_WIDTH - scenery_width, 0, CANVAS_WIDTH, CANVAS_HEIGHT], fill=COLOR_PALETTE['scenery_ground'])

        # Draw scenery, other cars, then player car
        for car in self.state['other_cars']:
            self.draw.rectangle([car['x'], car['y'], car['x'] + CAR_WIDTH, car['y'] + CAR_HEIGHT], fill=car['color'])
        
        player = self.state['player']
        self.draw.rectangle([player['x'], player['y'], player['x'] + CAR_WIDTH, player['y'] + CAR_HEIGHT], fill=COLOR_PALETTE['player_car'])

        if self.state['game_over']:
            self.draw.rectangle([0, CANVAS_HEIGHT / 2 - 60, CANVAS_WIDTH, CANVAS_HEIGHT / 2 + 60], fill=COLOR_PALETTE['crash_bg'])
            self.draw.text((CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2), "CRASHED!", font=FONT_BIG, anchor="mm", fill=COLOR_PALETTE['crash_text'])

    def save_image(self, path="highway_banner.png"):
        self.image.save(path)

    @staticmethod
    def get_default_state():
        return {
            "player": {
                "lane": 1,
                "x": LANES[1] - CAR_WIDTH / 2,
                "y": CANVAS_HEIGHT - CAR_HEIGHT - 30,
            },
            "other_cars": [],
            "scenery": [],
            "game_over": False
        }

def main():
    command_input = sys.argv[1] if len(sys.argv) > 1 else ""
    state_file = 'gamestate.json'

    # Load current state or create a new one
    try:
        with open(state_file, 'r') as f:
            current_state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        current_state = Game.get_default_state()

    game = Game(current_state)
    commands = game.parse_commands(command_input)
    
    # If RST, we just need the default state, no execution
    if commands and commands[0] == 'RST':
        game.state = game.get_default_state()
    else:
        game.execute_commands(commands)

    # Save the new state
    with open(state_file, 'w') as f:
        json.dump(game.state, f, indent=2)

    # Generate and save the image
    game.draw_frame()
    game.save_image()
    print("Generated highway_banner.png and updated gamestate.json")

if __name__ == "__main__":
    main()
