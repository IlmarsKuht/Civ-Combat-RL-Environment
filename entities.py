import math
import pygame
import random

import numpy as np


from options import BuildingType, TroopType, TileType, CnnChannels, Rewards, PLAYER_COLORS


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
    
    #this could probably be optimized
    def get_reachable_pos(self, troop):
        observation = np.full((self.row_count, self.column_count), -1)
        # Define the directions for the six neighbors in a hexagonal grid
        directions_odd = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (0, -1)]
        directions_even = [(-1, -1), (-1, 0), (0, 1), (1, 0), (1, -1), (0, -1)]
        # Use a queue to perform a breadth-first search
        queue = [(troop.row, troop.col, troop.moves)]
        while queue:
            curr_x, curr_y, movement_left = queue.pop(0)
            # Not reachable
            if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle:
                continue

            # Check the tile's troop and building
            tile_troop = self.tiles[curr_x, curr_y].troop
            tile_building = self.tiles[curr_x, curr_y].building
            if (curr_x != troop.row or curr_y != troop.col) and ((tile_troop and tile_troop.player_id == troop.player_id) or (tile_building and tile_building.player_id == troop.player_id)):
                observation[curr_x, curr_y] = 0
                continue
            elif (tile_troop and tile_troop.player_id != troop.player_id) or (tile_building and tile_building.player_id != troop.player_id):
                observation[curr_x, curr_y] = 1
                continue
            else:
                observation[curr_x, curr_y] = 1

            directions = directions_even if curr_x % 2 == 0 else directions_odd
            for dx, dy in directions:
                nx, ny = curr_x + dx, curr_y + dy
                if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                    
                    queue.append((nx, ny, movement_left - 1))
        return observation

    
    def get_obs(self, player): 
        observation = np.full((self.row_count, self.column_count, len(CnnChannels)), -1, dtype=np.float32)

        #For now let's assume that the player with id 0 is our player and all others are enemies
        troop_chosen = None

        #Keep track of them, I need to normalize them afterwards
        #Format [(value, (x, y)), (value2, (x2, y2))]
        powers = []
        healths = []

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
                    if not troop_chosen and troop.player_id == player.id and troop.moves > 0:
                        observation[row, col, CnnChannels.UNIT_TO_MOVE.value] = 1
                        troop_chosen = troop
                        #mark reachable positions
                        observation[:, :, CnnChannels.CAN_MOVE.value] = self.get_reachable_pos(troop)


        #normalize power and health between 0 and 1
        max_power = max(power for power, _ in powers)
        max_health = max(health for health, _ in healths)
        for power, (row, col) in powers:
            observation[row, col, CnnChannels.POWER.value] = power/max_power
        for health, (row, col) in healths:
            observation[row, col, CnnChannels.HEALTH.value] = health/max_health
        return observation, troop_chosen
    
    def action(self, action, troop):
        # Move the troop to the new tile and clear the old tile

        new_row, new_col = action
        reward = 0
        #ATTACK NOT WORKING FOR BUILDINGS YET
        tile_troop = self.tiles[new_row, new_col].troop
        tile_building = self.tiles[new_row, new_col].building
        if tile_troop is None and tile_building is None:
            reward = self._move(action, troop)
        elif tile_troop and tile_troop.row==troop.row and tile_troop.col==troop.col:
            reward = self._fortify(troop)
        #attacking check if the distance is bigger than 1, if yes then first move to the target, then attack
        elif tile_troop:
            reward = self._attack_troop(action, troop)
        elif tile_building:
            reward = self._attack_building(action, troop)

        return reward

    def draw(self, window):
        for row in self.tiles:
            for tile in row:
                tile.draw(window)
       
    def _fortify(self, troop):
        troop.moves = 0
        reward = Rewards.DEFAULT.value
        return reward
    def _move(self, action, troop):
        #don't set the moves to zero, instead minus the moves made by the player so he can move and attack
        troop.moves = 0

        new_row, new_col = action
        self.tiles[troop.row][troop.col].troop = None
        self.tiles[new_row][new_col].troop = troop
        troop.row = new_row
        troop.col = new_col
        
        
        reward = Rewards.DEFAULT.value
        return reward

    def _attack_troop(self, action, attacker):
        attacker.moves = 0
        row, col = action
        #get the defending and attacking troops power
        defender = self.tiles[row, col].troop
        def_power = defender.power

        attack_power = attacker.power
        #formula: Damage(HP)=30*e^{0.04*StrengthDifference}*randomBetween(0.8-1.2)}
        rand = random.uniform(0.8, 1.2)
        damage_to_defender = 30*math.exp(0.04 * (attack_power-def_power)) * rand
        damage_to_attacker = 30*math.exp(0.04 * (def_power-attack_power)) * rand

        defender.health -= damage_to_defender
        attacker.health -= damage_to_attacker
        print(f"Attacking troop at {row}, {col}, damage dealt: {damage_to_defender}, damage received: {damage_to_attacker}")

        #NEED A CONDITION WHERE BOTH UNITS CAN'T DIE, PROBABLY THE UNIT THAT HAS HIGHER HEALTH THAN THE OTHER ONE STAYS ALIVE
        reward = Rewards.ATTACK.value

        if defender.health <= 0:
            self._kill_troop(defender)
            reward = Rewards.KILL_TROOP.value
        elif attacker.health <= 0:
            self._kill_troop(attacker)
            reward = Rewards.LOSE_TROOP.value
        return reward
    
    def _attack_building(self, action, attacker):
        attacker.moves = 0
        row, col = action
        #get the defending and attacking troops power
        defender = self.tiles[row, col].building
        def_power = defender.power

        attack_power = attacker.power
        #formula: Damage(HP)=30*e^{0.04*StrengthDifference}*randomBetween(0.8-1.2)}
        rand = random.uniform(0.8, 1.2)
        damage_to_defender = 30*math.exp(0.04 * (attack_power-def_power)) * rand
        damage_to_attacker = 30*math.exp(0.04 * (def_power-attack_power)) * rand

        defender.health -= damage_to_defender
        attacker.health -= damage_to_attacker
        print(f"Attacking city at {row}, {col}, damage dealt: {damage_to_defender}, damage received: {damage_to_attacker}")

        #NEED A CONDITION WHERE BOTH UNITS CAN'T DIE, PROBABLY THE UNIT THAT HAS HIGHER HEALTH THAN THE OTHER ONE STAYS ALIVE
        reward = Rewards.ATTACK.value

        if defender.health <= 0:
            self._kill_city(defender)
            reward = Rewards.KILL_CITY.value
        elif attacker.health <= 0:
            self._kill_troop(attacker)
            reward = Rewards.KILL_TROOP.value
        return reward
        

        #have to check what reward to return, because I don't know if my troops are being attacked or enemies :)
        #So don't know + reward for attacking or - reward for being attacked

    def _kill_troop(self, troop):
        self.tiles[troop.row, troop.col].troop = None
    def _kill_city(self, troop):
        self.tiles[troop.row, troop.col].troop = None



