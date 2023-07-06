import math
import pygame
import random

import numpy as np


from options import BuildingType, TroopType, TileType, CnnChannels, Rewards, PLAYER_COLORS, \
DIRECTIONS_ODD, DIRECTIONS_EVEN


class Player:
    __id_counter = 0
    def __init__(self, name):
        self.id = Player.__id_counter
        Player.__id_counter += 1
        self.name = name
        self.troops = []
        self.buildings = []

class Troop:
    __id_counter = 0
    def __init__(self, health, power, moves, max_moves, player_id, type : TroopType, row, col):
        self.id = Troop.__id_counter
        Troop.__id_counter += 1
        self.health = health
        self.power = power
        self.moves = moves
        self.max_moves = moves
        self.player_id = player_id
        self.type = type
        self.row = row
        self.col = col

class Building:
    __id_counter = 0
    def __init__(self, health, power, player_id, type : BuildingType, row, col):
        self.id = Building.__id_counter
        Building.__id_counter += 1
        self.health = health
        self.power = power
        self.player_id = player_id
        self.type = type
        self.row = row
        self.col = col

class Tile:
    def __init__(self, type:TileType, move_cost=1, obstacle=False, draw=False, x=None, y=None, size=None):
        if draw:
            self.x = x
            self.y = y
            self.size = size
            self.points = self.calculate_points()
        self.obstacle = False
        self.troop = None
        self.building = None
        self.type = type
        self.move_cost = move_cost

    def calculate_points(self):
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = math.pi / 180 * angle_deg
            x = self.x + self.size * math.cos(angle_rad)
            y = self.y + self.size * math.sin(angle_rad)
            points.append([x, y])
        return points

    def draw(self, window):
        #Draw hexagon
        pygame.draw.polygon(window, (255, 255, 255), self.points, 1)

        # Draw Troop
        if self.troop:
            color = PLAYER_COLORS[self.troop.player_id % len(PLAYER_COLORS)]
            troop_rect = pygame.Rect(self.x - self.size/4, self.y - self.size/4, self.size/2, self.size/2)  # creating a rectangle
            self._draw_entity(window, self.troop, troop_rect, color, self.y - self.size/4 + troop_rect.height + 5, self.y - self.size/2, 100)

        # Draw Building
        if self.building:
            color = PLAYER_COLORS[self.building.player_id % len(PLAYER_COLORS)]
            building_rect = pygame.Rect(self.x - self.size/4, self.y - self.size/4, self.size/2, self.size/2)  # creating a rectangle
            self._draw_entity(window, self.building, building_rect, color, self.y + building_rect.height + 5, self.y - self.size/2, 200)

    def _draw_entity(self, window, entity, entity_rect, entity_color, health_bar_y, power_text_y, max_health):
        # Entity itself
        pygame.draw.rect(window, entity_color, entity_rect)

        # Health Bar
        health_bar_width = self.size / 2
        health = entity.health / max_health  # Health as a percentage
        green_width = health * health_bar_width
        red_width = (1 - health) * health_bar_width
        pygame.draw.rect(window, (0, 255, 0), (self.x - self.size/4, health_bar_y, green_width, 5))  # Green part
        pygame.draw.rect(window, (255, 0, 0), (self.x - self.size/4 + green_width, health_bar_y, red_width, 5))  # Red part

        # Power number
        font = pygame.font.Font(None, 24)  # You can choose the font and size
        power_text = font.render(str(entity.power), True, (255, 255, 255))  # Black text
        power_text_rect = power_text.get_rect(center=(self.x, power_text_y))  # Above the entity
        window.blit(power_text, power_text_rect)

class Terrain:
    def __init__(self, row_count, column_count, draw=False, size=None, margin=None):
        if draw:
            self.size = size
            self.margin = margin
        self.row_count = row_count
        self.column_count = column_count
        self.tiles = self.create_tiles(draw)


    def __getitem__(self, index):
        return self.tiles[index]

    def create_tiles(self, draw):
        tiles = []
        for row in range(self.row_count):
            rows = []
            for col in range(self.column_count):
                if draw:
                    x = self.size * math.sqrt(3) * (col + 0.5 * (row % 2))
                    y = self.size * 3/2 * row
                    tile = Tile(TileType.PLAINS, 1, False, True, x+self.margin, y+self.margin, self.size)
                else:
                    tile = Tile(TileType.PLAINS)
                rows.append(tile)
            tiles.append(rows)
        return np.array(tiles)
    
    #I NEED TO COMBINE SOMEHOW THESE 3 LARGE FUNCTIONS

    def find_closest_adjacent_tile(self, row, col, troop):
        target_row, target_col = None, None
        
        # Get all adjacent cells of the target
        target_directions = DIRECTIONS_EVEN if row % 2 == 0 else DIRECTIONS_ODD
        adjacent_cells = [(row + dx, col + dy) for dx, dy in target_directions
                        if 0 <= row + dx < self.row_count and 0 <= col + dy < self.column_count]

        # Use a queue to perform a breadth-first search
        # x, y, movement_points, how many moves
        queue = [(troop.row, troop.col, troop.moves, 0)]
        while queue:
            curr_x, curr_y, movement_left, moves = queue.pop(0)
            # Not reachable
            if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle:
                continue
            # Reached adjacent cell to target
            if (curr_x, curr_y) in adjacent_cells:
                target_row, target_col = curr_x, curr_y
                break
            directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
            for dx, dy in directions:
                nx, ny = curr_x + dx, curr_y + dy
                if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                    queue.append((nx, ny, movement_left - 1, moves+1))

        return target_row, target_col


    def get_nearest_troop(self, row, col, troops):
        nearest_troop = None
        min_moves = float('inf')

        for troop in troops:
            #x, y, movement_points, how many moves
            queue = [(troop.row, troop.col, troop.moves, 0)]

            while queue:
                curr_x, curr_y, movement_left, moves = queue.pop(0)
                # Not reachable
                if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle:
                    continue

                # Reached target
                if curr_x == row and curr_y == col:
                    if moves < min_moves:
                        min_moves = moves
                        nearest_troop = troop
                    break

                directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
                for dx, dy in directions:
                    nx, ny = curr_x + dx, curr_y + dy
                    if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                        queue.append((nx, ny, movement_left - 1, moves+1))

        return nearest_troop
    
    #this could probably be optimized
    def get_reachable_pos(self, troop):
        observation = np.full((self.row_count, self.column_count), -1)
        # Use a queue to perform a breadth-first search
        queue = [(troop.row, troop.col, troop.moves)]
        while queue:
            curr_x, curr_y, movement_left = queue.pop(0)
            # Not reachable
            if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle or self.tiles[curr_x, curr_y] == 1:
                continue

            # Check the tile's troop and building
            tile_troop = self.tiles[curr_x, curr_y].troop
            tile_building = self.tiles[curr_x, curr_y].building
            if (curr_x != troop.row or curr_y != troop.col) \
            and ((tile_troop and tile_troop.player_id == troop.player_id) \
            or (tile_building and tile_building.player_id == troop.player_id)):
                observation[curr_x, curr_y] = 0
                continue
            elif (tile_troop and tile_troop.player_id != troop.player_id) \
                or (tile_building and tile_building.player_id != troop.player_id):
                observation[curr_x, curr_y] = 1
                continue
            else:
                observation[curr_x, curr_y] = 1

            directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
            for dx, dy in directions:
                nx, ny = curr_x + dx, curr_y + dy
                if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                    queue.append((nx, ny, movement_left - 1))
        return observation

    
    def get_obs(self, player): 
        observation = np.full((self.row_count, self.column_count, len(CnnChannels)), -1, dtype=np.float32)

        #For now let's assume that the player with id 0 is our player and all others are enemies

        #Keep track of them, I need to normalize them afterwards
        #Format [(value, (x, y)), (value2, (x2, y2))]
        powers = []
        healths = []

        ai_turn = True

        # Loop over each type of entity
        for row in range(self.row_count):
            for col in range(self.column_count):
                # Add this feature map to the observation
                building = self.tiles[row, col].building
                troop = self.tiles[row, col].troop

                #Update Friendly, Enemy, Health and Power channels for buildings
                if building:
                    observation[row, col, CnnChannels.IS_ENEMY_BUILDING.value] = building.player_id != player.id
                    powers.append((building.power, (row, col)))
                    healths.append((building.health, (row, col)))

                #Update Friendly, Enemy, Health and Power channels for troops
                if troop:
                    observation[row, col, CnnChannels.IS_ENEMY_TROOP.value] = troop.player_id != player.id
                    powers.append((troop.power, (row, col)))
                    healths.append((troop.health, (row, col)))

                    #Update UnitMoveChannel to show which unit to move
                    if troop.player_id == player.id and troop.moves > 0:
                        ai_turn = False
                        #mark reachable positions
                        observation[:, :, CnnChannels.CAN_MOVE.value] = self.get_reachable_pos(troop)


        #normalize power and health between 0 and 1
        max_power = max(power for power, _ in powers)
        max_health = max(health for health, _ in healths)
        for power, (row, col) in powers:
            observation[row, col, CnnChannels.POWER.value] = power/max_power
        for health, (row, col) in healths:
            observation[row, col, CnnChannels.HEALTH.value] = health/max_health

        #I AM LAZY, NEEDT TO CHANGE CODE BUT LET'S SEE IF THIS EVEN WORKS
        # Reorder dimensions to (Channels, Rows, Columns)
        observation = np.transpose(observation, (2, 0, 1))

        return observation, ai_turn
    
    #NEED TO FIND ONE ACTION FROM ACTION SPACE
    #returns reward and termianted
    def action(self, actions, player):
        reward = Rewards.DEFAULT.value
        terminated = False
        troops = player.troops

        #first check if there even is a troop
        if len(troops) == 0:
            #because no troops, the game is basically lost
            return Rewards.LOSE_CITY.value, True
        print(actions)
        #get a random action from the space
        actions = np.where(actions == 1)[0]  # get indices of valid actions
        print(actions)
        for action in actions:
            print(divmod(action, self.row_count))
        #if no valid actions

        if len(actions) == 0:
            print("No actions")
            return Rewards.DEFAULT.value, terminated
        action = np.random.choice(actions) 
        target_row, target_col = divmod(action, self.row_count)  #get row and col coordinates

        #model doesn't specify which troop to use so I just find the closest troop
        troop = self.get_nearest_troop(target_row, target_col, troops)   
        target_troop = self.tiles[target_row, target_col].troop
        target_building = self.tiles[target_row, target_col].building

        #just move
        if target_troop is None and target_building is None:
            reward = self._move(target_row, target_col, troop)
        #fortify if the tile it is standing on
        elif target_row == troop.row and target_row == troop.col:
            reward = self._fortify(troop)
        else:
            #check if troop is already adjacent
            target_directions = DIRECTIONS_EVEN if target_row % 2 == 0 else DIRECTIONS_ODD
            adjacent_cells = [(target_row + dx, target_col + dy) for dx, dy in target_directions
                        if 0 <= target_row + dx < self.row_count and 0 <= target_col + dy < self.column_count]
            if (troop.row, troop.col) not in adjacent_cells:
                #move adjacent to target
                row, col = self.find_closest_adjacent_tile(target_row, target_col, troop)
                if row is None or col is None:
                    print("Couldn't find adjacent tile")
                else:
                    reward = self._move(row, col, troop)

            #then attack
            reward = self._attack(action, troop, target_building or target_troop)

        return reward, terminated

    def draw(self, window):
        for row in self.tiles:
            for tile in row:
                tile.draw(window)
       
    def _fortify(self, troop):
        troop.moves = 0
        #increase the power of the troop while fortified

        reward = Rewards.DEFAULT.value
        return reward
    

    def _move(self, new_row, new_col, troop):
        #don't set the moves to zero, instead minus the moves made by the player so he can move and attack
        troop.moves = 0

        self.tiles[troop.row][troop.col].troop = None
        self.tiles[new_row][new_col].troop = troop
        troop.row = new_row
        troop.col = new_col
        
        reward = Rewards.DEFAULT.value
        return reward

    def _attack(self, new_row, new_col, attacker, defender):
        attacker.moves = 0
        #get the defending and attacking troops power
        def_power = defender.power
        attack_power = attacker.power

        #formula: Damage(HP)=30*e^{0.04*StrengthDifference}*randomBetween(0.8-1.2)}
        rand = random.uniform(0.8, 1.2)
        damage_to_defender = 30*math.exp(0.04 * (attack_power-def_power)) * rand
        damage_to_attacker = 30*math.exp(0.04 * (def_power-attack_power)) * rand
        defender.health -= damage_to_defender
        attacker.health -= damage_to_attacker
        print(f"Attacking troop at {new_row}, {new_col}, damage dealt: {damage_to_defender}, damage received: {damage_to_attacker}")

        reward = Rewards.ATTACK.value

        if defender.health <= 0 or attacker.health <= 0:
            #kill the unit with the least health, otherwise just the one with less than 1 health
            unit_to_kill = min((defender, attacker), key=lambda troop: troop.health) \
                                if defender.health <= 0 and attacker.health <= 0 else defender if defender.health <= 0 else attacker
            reward = self._kill_entity(unit_to_kill)

        return reward

    def _kill_entity(self, row, col, entity):
        if isinstance(entity, Troop):
            self.tiles[row, col].troop = None
            reward = Rewards.KILL_TROOP.value
        elif isinstance(entity, Building):
            self.tiles[row, col].building = None
            reward = Rewards.KILL_CITY.value
        return reward

