import json
import os
import random
import sys
from PIL import Image, ImageDraw, ImageFont

# --- Game & Image Configuration ---
CANVAS_WIDTH = 400
CANVAS_HEIGHT = 600
CAR_WIDTH = 40
CAR_HEIGHT = 70
LANES = [CANVAS_WIDTH * 0.25, CANVAS_WIDTH * 0.5, CANVAS_WIDTH * 0.75]
MOVE_SPEED = 20
DOWNWARD_CAR_SPEED = 8
FORWARD_CAR_SPEED = -3

# --- Color Palette (from HTML) ---
COLOR_ROAD = (74, 85, 104)      # gray-600
COLOR_SCENERY_SIDE = (160, 82, 45) # Brownish dirt
COLOR_PLAYER_CAR = '#f6e05e'
COLOR_WHITE = (255, 255, 255)
COLOR_CRASH_BG = (0, 0, 0, 180) # Black with alpha
COLOR_FONT_CRASH = '#f6e05e'
COLOR_FONT_SUB = '#FFFFFF'

OTHER_CAR_COLORS = ['#e53e3e', '#38b2ac', '#9f7aea', '#4299e1']
PARKED_CAR_COLORS = ['#A0AEC0', '#718096', '#4A5568']

# --- File Paths ---
STATE_FILE = 'gamestate.json'
OUTPUT_IMAGE = 'highway_banner.png'
FONT_FILE_LARGE = 'PressStart2P-Regular.ttf'
FONT_FILE_SMALL = 'PressStart2P-Regular.ttf'

# --- Drawing & Utility Functions ---

def get_font(size):
    """Loads a font if available, otherwise uses Pillow's default."""
    try:
        return ImageFont.truetype(FONT_FILE_LARGE, size)
    except IOError:
        print(f"Warning: Font '{FONT_FILE_LARGE}' not found. Using default font.")
        # Pillow's default font is very basic but will prevent a crash.
        # For best results, add 'PressStart2P-Regular.ttf' to your repo.
        return ImageFont.load_default()

def parse_commands(command_string):
    """Parses command strings like 'M5L2' into a list ['M', 'M', ...]."""
    commands = []
    i = 0
    while i < len(command_string):
        char = command_string[i].upper()
        if char in ('L', 'R', 'M'):
            i += 1
            num_str = ""
            while i < len(command_string) and command_string[i].isdigit():
                num_str += command_string[i]
                i += 1
            count = int(num_str) if num_str else 1
            commands.extend([char] * count)
        else:
            i += 1 # Ignore invalid characters
    # Limit command length to prevent abuse
    return commands[:100]

def draw_car(draw, car, is_parked=False):
    """Draws a single car with details."""
    x, y, w, h = car['x'], car['y'], car['width'], car['height']
    draw.rectangle([x, y, x + w, y + h], fill=car['color'])
    if not is_parked:
        # Windshield
        draw.rectangle([x + 5, y + 10, x + w - 5, y + 25], fill='#2d3748')
        # Taillights for cars moving away
        if car.get('speed', 0) < 0:
            draw.rectangle([x + 5, y + h - 10, x + 13, y + h - 5], fill='#ef4444')
            draw.rectangle([x + w - 13, y + h - 10, x + w - 5, y + h - 5], fill='#ef4444')

def draw_scenery(draw, scenery_objects):
    """Draws all scenery objects."""
    scenery_width = (CANVAS_WIDTH / 3) * 0.5
    draw.rectangle([0, 0, scenery_width, CANVAS_HEIGHT], fill=COLOR_SCENERY_SIDE)
    draw.rectangle([CANVAS_WIDTH - scenery_width, 0, CANVAS_WIDTH, CANVAS_HEIGHT], fill=COLOR_SCENERY_SIDE)

    for obj in scenery_objects:
        x, y, w, h = obj['x'], obj['y'], obj['width'], obj['height']
        obj_type = obj['type']

        if obj_type == 'tree_round':
            draw.rectangle([x - 3, y, x + 3, y + h], fill='#8B4513') # Trunk
            draw.ellipse([x - w/2, y - h/2, x + w/2, y + h/2], fill=obj['color'])
        elif obj_type == 'tree_pine':
            draw.rectangle([x - 3, y + h/2 - 15, x + 3, y + h/2], fill='#8B4513') # Trunk
            draw.polygon([(x, y - h/2), (x - w/2, y + h/2), (x + w/2, y + h/2)], fill=obj['color'])
        elif obj_type == 'sand_patch':
            draw.rectangle([x - w/2, y, x + w/2, y + h], fill=obj['color'])
        elif obj_type == 'pond':
            draw.ellipse([x - w/2, y - h/2, x + w/2, y + h/2], fill=obj['color'])
        elif obj_type == 'store':
            draw.rectangle([x - w/2, y - h/2, x + w/2, y + h/2], fill=obj['color']) # Building
            draw.rectangle([x - w/2 - 5, y - h/2 - 5, x + w/2 + 5, y - h/2 + 5], fill='#A0AEC0') # Roof
            draw.rectangle([x - 8, y + h/2 - 20, x + 8, y + h/2], fill='#4A5568') # Door
        elif obj_type == 'parked_car':
            parked_car_state = {**obj, 'x': obj['x'] - obj['width']/2, 'y': obj['y'] - obj['height']/2}
            draw_car(draw, parked_car_state, is_parked=True)

def draw_road(draw, road_markings):
    """Draws dashed road markings."""
    for mark in road_markings:
        draw.line([mark['x'], mark['y'], mark['x'], mark['y'] + 20], fill=COLOR_WHITE, width=5)

def draw_message(draw, message, submessage):
    """Draws the CRASHED message."""
    draw.rectangle([0, CANVAS_HEIGHT/2 - 60, CANVAS_WIDTH, CANVAS_HEIGHT/2 + 60], fill=COLOR_CRASH_BG)
    font_large = get_font(40)
    font_small = get_font(14)
    draw.text((CANVAS_WIDTH/2, CANVAS_HEIGHT/2), message, font=font_large, fill=COLOR_FONT_CRASH, anchor='mm')
    draw.text((CANVAS_WIDTH/2, CANVAS_HEIGHT/2 + 30), submessage, font=font_small, fill=COLOR_FONT_SUB, anchor='mm')

# --- Main Game Class ---

class HighwayGame:
    def __init__(self, state):
        self.state = state

    def update_positions(self, is_player_moving):
        # Update player car's X position based on lane
        self.state['playerCar']['x'] = LANES[self.state['playerCar']['laneIndex']] - CAR_WIDTH / 2
        
        # All other cars move at their own speed
        for car in self.state['otherCars']:
            car['y'] += car['speed']

        if is_player_moving:
            # Move the world down
            for group in ['otherCars', 'roadMarkings', 'sceneryObjects']:
                for item in self.state[group]:
                    item['y'] += MOVE_SPEED

        # Clean up off-screen objects
        self.state['otherCars'] = [c for c in self.state['otherCars'] if -CAR_HEIGHT*2 < c['y'] < CANVAS_HEIGHT + CAR_HEIGHT]
        self.state['sceneryObjects'] = [s for s in self.state['sceneryObjects'] if s['y'] < CANVAS_HEIGHT + 50]
        self.state['roadMarkings'] = [m for m in self.state['roadMarkings'] if m['y'] < CANVAS_HEIGHT]

        # Add new road markings if needed
        last_y = max([m['y'] for m in self.state['roadMarkings']] or [-45])
        while last_y > -45:
            last_y -= 45
            self.state['roadMarkings'].append({'x': CANVAS_WIDTH / 3, 'y': last_y})
            self.state['roadMarkings'].append({'x': (CANVAS_WIDTH / 3) * 2, 'y': last_y})
    
    def spawn_car(self):
        last_car = max([c['y'] for c in self.state['otherCars']] or [-999])
        if last_car > -CAR_HEIGHT * 2.5 or random.random() < 0.2:
            return

        lane = random.randint(0, 2)
        new_car = {
            'laneIndex': lane, 'x': LANES[lane] - CAR_WIDTH / 2, 'y': -CAR_HEIGHT * 2,
            'width': CAR_WIDTH, 'height': CAR_HEIGHT,
            'color': random.choice(OTHER_CAR_COLORS),
            'speed': FORWARD_CAR_SPEED if lane == 1 else DOWNWARD_CAR_SPEED
        }
        self.state['otherCars'].append(new_car)

    def spawn_scenery(self):
        if random.random() > 0.5:
            return
        
        scenery_width = (CANVAS_WIDTH / 3) * 0.5
        side = 'left' if random.random() < 0.5 else 'right'
        types = ['tree_round', 'tree_pine', 'sand_patch', 'pond', 'store', 'parked_car']
        obj_type = random.choice(types)
        
        obj = {
            'type': obj_type, 'y': -60,
            'x': random.randint(15, int(scenery_width - 25)) if side == 'left' else CANVAS_WIDTH - scenery_width + random.randint(25, int(scenery_width - 15))
        }

        # Set properties based on type
        if obj_type == 'tree_round':
            obj.update({'width': random.randint(20, 30), 'height': random.randint(20, 30), 'color': '#228B22'})
        elif obj_type == 'tree_pine':
            obj.update({'width': random.randint(25, 35), 'height': random.randint(30, 40), 'color': '#2F4F4F'})
        elif obj_type == 'sand_patch':
            obj.update({'width': random.randint(20, 40), 'height': random.randint(20, 40), 'color': '#F4A460'})
        elif obj_type == 'pond':
            obj.update({'width': random.randint(40, 60), 'height': random.randint(30, 50), 'color': '#3182CE'})
        elif obj_type == 'store':
            obj.update({'width': 60, 'height': 50, 'color': '#E53E3E'})
        elif obj_type == 'parked_car':
            obj.update({'width': CAR_WIDTH - 5, 'height': CAR_HEIGHT - 10, 'color': random.choice(PARKED_CAR_COLORS)})
        
        self.state['sceneryObjects'].append(obj)

    def check_collision(self):
        pc = self.state['playerCar']
        for oc in self.state['otherCars']:
            if (pc['x'] < oc['x'] + oc['width'] and pc['x'] + pc['width'] > oc['x'] and
                    pc['y'] < oc['y'] + oc['height'] and pc['y'] + pc['height'] > oc['y']):
                return True
        return False

    def run_commands(self, commands):
        """Processes a list of commands and updates the game state."""
        for command in commands:
            is_moving = False
            boundary_crash = False
            
            if command == 'L':
                if self.state['playerCar']['laneIndex'] > 0: self.state['playerCar']['laneIndex'] -= 1
                else: boundary_crash = True
            elif command == 'R':
                if self.state['playerCar']['laneIndex'] < 2: self.state['playerCar']['laneIndex'] += 1
                else: boundary_crash = True
            elif command == 'M':
                is_moving = True
                self.spawn_car()
                self.spawn_scenery()
            
            self.update_positions(is_moving)

            if boundary_crash or self.check_collision():
                self.state['gameState'] = 'crashed'
                break # Stop processing commands on crash
    
    def reset(self):
        """Resets the game to its initial state."""
        self.state = {
            'playerCar': {
                'laneIndex': 1, 'x': LANES[1] - CAR_WIDTH / 2, 'y': CANVAS_HEIGHT - CAR_HEIGHT - 30,
                'width': CAR_WIDTH, 'height': CAR_HEIGHT, 'color': COLOR_PLAYER_CAR
            },
            'otherCars': [], 'roadMarkings': [], 'sceneryObjects': [],
            'gameState': 'ready'
        }
        # Pre-populate road markings
        for i in range(20):
            y = CANVAS_HEIGHT - i * 45
            self.state['roadMarkings'].append({'x': CANVAS_WIDTH / 3, 'y': y})
            self.state['roadMarkings'].append({'x': (CANVAS_WIDTH / 3) * 2, 'y': y})
        self.update_positions(False)


def main():
    # Load previous state or create a new one
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    else:
        # This will be the state for the very first run
        state = {} 

    game = HighwayGame(state)

    # Get command from command-line argument
    if len(sys.argv) < 2:
        print("Usage: python generate_image.py \"<COMMANDS>\"")
        command_str = "M1" # Default command if none provided
    else:
        command_str = sys.argv[1]

    # Handle the reset command
    if command_str.upper() == "RST":
        game.reset()
    else:
        # On the first run, the state is empty, so reset it.
        # Also resets if a game was left in a 'crashed' state.
        if not game.state or game.state.get('gameState') == 'crashed':
             game.reset()
        
        commands = parse_commands(command_str)
        if commands:
            game.state['gameState'] = 'running'
            game.run_commands(commands)
    
    # --- Render the final image ---
    image = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color=COLOR_ROAD)
    draw = ImageDraw.Draw(image, 'RGBA')

    draw_scenery(draw, game.state['sceneryObjects'])
    draw_road(draw, game.state['roadMarkings'])
    for car in game.state['otherCars']:
        draw_car(draw, car)
    draw_car(draw, game.state['playerCar'])

    if game.state['gameState'] == 'crashed':
        draw_message(draw, 'CRASHED!', 'Use RST to reset')

    # Save the output
    image.save(OUTPUT_IMAGE)
    with open(STATE_FILE, 'w') as f:
        json.dump(game.state, f, indent=2)

    print(f"Generated {OUTPUT_IMAGE} and updated {STATE_FILE}.")

if __name__ == "__main__":
    main()

