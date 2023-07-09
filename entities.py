import math
import pygame
import random

from collections import deque
import numpy as np


from options import BuildingType, TroopType, TileType, CnnChannels, Rewards, PLAYER_COLORS, \
DIRECTIONS_ODD, DIRECTIONS_EVEN, HEX_SIZE, FortifiedBonus, Colors


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
    def __init__(self, health, max_health, power, moves, max_moves, player_id, type : TroopType, \
                  row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0):
        self.id = Troop.__id_counter
        Troop.__id_counter += 1
        self.health = health
        self.max_health = max_health
        self.power = power
        self.moves = moves
        self.max_moves = max_moves
        self.player_id = player_id
        self.type = type
        self.row = row
        self.col = col
        self.fortified = fortified
        self.hp_power_loss = hp_power_loss

class Building:
    __id_counter = 0
    def __init__(self, health, max_health, power, player_id, type : BuildingType, row, col):
        self.id = Building.__id_counter
        Building.__id_counter += 1
        self.health = health
        self.max_health = max_health
        self.power = power
        self.player_id = player_id
        self.type = type
        self.row = row
        self.col = col




class Tile:
    HEXAGON_IMAGE = pygame.image.load('./images/hexagon.png')  
    HEXAGON_IMAGE = pygame.transform.scale(HEXAGON_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HEXAGON_IMAGE = pygame.transform.rotate(HEXAGON_IMAGE, 90)

    WARRIOR_IMAGE = pygame.image.load('./images/warrior.png')
    WARRIOR_IMAGE = pygame.transform.scale(WARRIOR_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    CITY_CENTER_IMAGE = pygame.image.load('./images/city_center.png')
    CITY_CENTER_IMAGE = pygame.transform.scale(CITY_CENTER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    def __init__(self, type:TileType, move_cost=1, obstacle=False, draw=False, x=None, y=None, size=None, owner=None):
        if draw:
            self.x = x+size/2
            self.y = y+size/2
            self.size = size
        self.obstacle = obstacle
        self.troop = None
        self.building = None
        self.type = type
        self.move_cost = move_cost
        self.owner = owner
    
    def _draw_centered(self, window, image, x, y):
        rect = image.get_rect(center=(x, y))
        window.blit(image, rect)

    def draw(self, window):
        #Draw hexagon
        #I have centered x and y, so I need to adjust the tiles, so everthing else can stay the same
        window.blit(Tile.HEXAGON_IMAGE, (self.x-self.size/2, self.y-self.size/2))

        # Draw Troop
        if self.troop:
            color = PLAYER_COLORS[self.troop.player_id % len(PLAYER_COLORS)]
            self._draw_centered(window, Tile.WARRIOR_IMAGE, self.x, self.y)
            #tag the team color
            pygame.draw.circle(window, color, (self.x, self.y), self.size/15)
            self._draw_attributes(window, self.troop)

        # Draw Building
        if self.building:
            color = PLAYER_COLORS[self.building.player_id % len(PLAYER_COLORS)]
            self._draw_centered(window, Tile.CITY_CENTER_IMAGE, self.x, self.y)
            pygame.draw.circle(window, color, (self.x, self.y), self.size/15)
            self._draw_attributes(window, self.building)

    def _draw_attributes(self, window, entity):
        # Health Bar
        health_bar_width = self.size/2
        health = entity.health / entity.max_health  # Health as a percentage
        green_width = int(health * health_bar_width)
        red_width = int((1 - health) * health_bar_width)
        health_bar_x = int(self.x-health_bar_width/2)
        health_bar_y = int(self.y+self.size/4)
        health_bar_height = self.size/25
        #Change Health color depending on fortification
        health_color = Colors.HEALTH.value
        if isinstance(entity, Troop):
            if entity.fortified == FortifiedBonus.FIRST:
                health_color = Colors.FORTIFIED.value
            elif entity.fortified == FortifiedBonus.SECOND:
                health_color = Colors.EXTRA_FORTIFIED.value
        pygame.draw.rect(window, health_color, (health_bar_x, health_bar_y, green_width, health_bar_height))  # Green part
        pygame.draw.rect(window, Colors.HEALTH_LOST.value, (health_bar_x + green_width, health_bar_y, red_width, health_bar_height))  # Red part

        # Power number
        font = pygame.font.Font(None, int(self.size/5))  
        power_text = font.render(str(entity.power), True, Colors.BLACK.value) 
        self._draw_centered(window, power_text, self.x, self.y-self.size/3)

class Terrain:
    def __init__(self, row_count, column_count, draw=False, size=None, margin=None):
        self.row_count = row_count
        self.column_count = column_count
        self.tiles = self.create_tiles(draw, size, margin)


    def __getitem__(self, index):
        return self.tiles[index]

    def create_tiles(self, draw, size, margin):
        tiles = []
        for row in range(self.row_count):
            rows = []
            for col in range(self.column_count):
                if draw:
                    x = size * col + (size/2 * (row % 2)) 
                    y = size * 3/2 * row / 2 
                    tile = Tile(TileType.PLAINS, 1, False, True, x+margin, y+margin, size)
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
        queue = deque([(troop.row, troop.col, troop.moves, 0)])
        while queue:
            curr_x, curr_y, movement_left, moves = queue.popleft()
            # Not reachable
            if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle:
                continue
            elif (curr_x != troop.row or curr_y != troop.col) \
                and (self.tiles[curr_x, curr_y].troop or \
                (self.tiles[curr_x, curr_y].building and self.tiles[curr_x, curr_y].building.player_id != troop.player_id)):
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
            queue = deque([(troop.row, troop.col, troop.moves, 0)])

            while queue:
                curr_x, curr_y, movement_left, moves = queue.popleft()
                # Not reachable
                if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle:
                    continue

                # Reached target
                if curr_x == row and curr_y == col:
                    if moves < min_moves:
                        min_moves = moves
                        nearest_troop = troop
                    break
                # Can't move to here, don't look
                elif (curr_x != troop.row or curr_y != troop.col) and (self.tiles[curr_x, curr_y].troop or \
                    (self.tiles[curr_x, curr_y].building and self.tiles[curr_x, curr_y].building.player_id != troop.player_id)):
                    continue

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
        queue = deque([(troop.row, troop.col, troop.moves)])
        while queue:
            curr_x, curr_y, movement_left = queue.popleft()
            # Not reachable
            if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle or self.tiles[curr_x, curr_y] == 1:
                continue

            # Check the tile's troop and building
            tile_troop = self.tiles[curr_x, curr_y].troop
            tile_building = self.tiles[curr_x, curr_y].building
            if (curr_x != troop.row or curr_y != troop.col) \
            and (tile_troop and tile_troop.player_id == troop.player_id):
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
        troop_powers = []
        troop_healths = []
        building_powers = []
        building_healths = []

        # Loop over each type of entity
        for row in range(self.row_count):
            for col in range(self.column_count):
                # Add this feature map to the observation
                building = self.tiles[row, col].building
                troop = self.tiles[row, col].troop

                #Update Friendly, Enemy, Health and Power channels for buildings
                if building:
                    observation[row, col, CnnChannels.IS_ENEMY_BUILDING.value] = building.player_id != player.id
                    building_powers.append((building.power, (row, col)))
                    building_healths.append((building.health, (row, col)))

                #Update Friendly, Enemy, Health and Power channels for troops
                if troop:
                    observation[row, col, CnnChannels.IS_ENEMY_TROOP.value] = troop.player_id != player.id
                    troop_powers.append((troop.power, (row, col)))
                    troop_healths.append((troop.health, (row, col)))

                    #Update UnitMoveChannel to show which unit to move
                    if troop.player_id == player.id and troop.moves > 0:
                        #mark reachable positions
                        new_values = self.get_reachable_pos(troop)
                        current_values = observation[:, :, CnnChannels.CAN_MOVE.value]

                        # Only update current_values where it's -1 and new_values is either 0 or 1
                        # or where current_values is 0 and new_values is 1
                        mask = ((current_values == -1) & ((new_values == 1) | (new_values == 0))) | ((current_values == 0) & (new_values == 1))
                        current_values[mask] = new_values[mask]
                        observation[:, :, CnnChannels.CAN_MOVE.value] = current_values


        #normalize power and health between 0 and 1
        max_troop_power = max(power for power, _ in troop_powers)
        max_troop_health = max(health for health, _ in troop_healths)
        max_building_power = max(power for power, _ in building_powers)
        max_building_health = max(health for health, _ in building_healths)
        for power, (row, col) in troop_powers:
            observation[row, col, CnnChannels.TROOP_POWER.value] = power/max_troop_power
        for health, (row, col) in troop_healths:
            observation[row, col, CnnChannels.TROOP_HEALTH.value] = health/max_troop_health
        for power, (row, col) in building_powers:
            observation[row, col, CnnChannels.BUILDING_POWER.value] = power/max_building_power
        for health, (row, col) in building_healths:
            observation[row, col, CnnChannels.BUILDING_HEALTH.value] = health/max_building_health

        #I AM LAZY, NEEDT TO CHANGE CODE BUT LET'S SEE IF THIS EVEN WORKS
        # Reorder dimensions to (Channels, Rows, Columns)
        observation = np.transpose(observation, (2, 0, 1))

        return observation
    
    def draw(self, window):
        for row in self.tiles:
            for tile in row:
                tile.draw(window)

    def action(self, actions, player, mask):
        reward = Rewards.DEFAULT.value
        terminated = False
        ai_turn = False
        troops = player.troops
        

        #first check if there even is a troop
        if len(troops) == 0 or len(player.buildings) == 0:
            #because no troops, the game is basically lost
            return Rewards.LOSE_CITY.value, True, ai_turn
        
        #get troops with moves
        troops = [troop for troop in troops if troop.moves > 0]
        #chooses a random move if model didn't have a move
        target_row, target_col, no_model_action, debug = self._get_action(actions, mask)
       

        #model doesn't specify which troop to use so I just find the closest troop
        troop = self.get_nearest_troop(target_row, target_col, troops)   
        #TROOP NOT FOUND, SO SOMETHING MUST BE WRONG WITH GET_NEAREST_TROOP
        target_troop = self.tiles[target_row, target_col].troop
        target_building = self.tiles[target_row, target_col].building

        #just move
        if (target_troop is None and target_building is None) or \
            (target_building and target_building.player_id == player.id):
            reward = self._move(target_row, target_col, troop)

        #fortify if the tile it is standing on
        elif target_row == troop.row and target_col == troop.col:
            reward = self._fortify(troop)

        #move and attack 
        else:
            if not self._is_adjacent(troop.row, troop.col, target_row, target_col):
                #move adjacent to target
                row, col = self.find_closest_adjacent_tile(target_row, target_col, troop)
                #no reward because already attacking
                self._move(row, col, troop)
            #then attack
            if target_building:
                reward, terminated = self._attack(target_row, target_col, troop, target_building)
            elif target_troop:
                reward, terminated = self._attack(target_row, target_col, troop, target_troop)

        #check if troops still have moves
        if not self._movable_troops(troops):
            ai_turn = True

        #give bad reward and choose
        if no_model_action:
            print("INVALID")
            reward = Rewards.INVALID.value

        return reward, terminated, ai_turn, debug

    
    def _movable_troops(self, troops):
        for troop in troops:
            if troop.moves > 0:
                return True
        return False
    
    def _is_adjacent(self, row, col, target_row, target_col):
        target_directions = DIRECTIONS_EVEN if target_row % 2 == 0 else DIRECTIONS_ODD
        adjacent_cells = [(target_row + dx, target_col + dy) for dx, dy in target_directions
                    if 0 <= target_row + dx < self.row_count and 0 <= target_col + dy < self.column_count]
        return (row, col) in adjacent_cells
    
    def _get_action(self, actions, mask):
        #network didn't choose any action
        no_model_action = False
        #mask invalid actions
        actions = actions*mask
        
        # Get indices of valid actions.
        valid_indices = np.where(actions != 0)[0]

        # If no valid actions.
        debug = False
        if len(valid_indices) == 0:
            debug = True
            valid_indices = np.where(mask == 1)[0]
            no_model_action = True
        # Get values of valid actions.
        valid_actions = actions[valid_indices]

        # Get the index of the highest value action.
        max_action_index = np.argmax(valid_actions)

        # Map this back to the original array's indices.
        action = valid_indices[max_action_index]

        # Get row and col coordinates.
        target_row, target_col = divmod(action, self.row_count) 
        return target_row, target_col, no_model_action, debug
       
    def _fortify(self, troop):
        #Fortification bonus calculations
        if troop.moves == troop.max_moves:
            if troop.fortified == FortifiedBonus.NONE:
                troop.fortified = FortifiedBonus.FIRST
                troop.power += FortifiedBonus.FIRST.value
            elif troop.fortified == FortifiedBonus.FIRST:
                troop.fortified = FortifiedBonus.SECOND
                troop.power -= FortifiedBonus.FIRST.value
                troop.power += FortifiedBonus.SECOND.value
        troop.moves = 0
        #increase the power of the troop while fortified
        reward = Rewards.DEFAULT.value
        return reward
    
    def _remove_fortify_bonus(self, troop):
        troop.power -= troop.fortified.value
        troop.fortified = FortifiedBonus.NONE

    def _move(self, new_row, new_col, troop):
        #don't set the moves to zero, instead minus the moves made by the player so he can move and attack
        troop.moves = 0
        self._remove_fortify_bonus(troop)

        self.tiles[troop.row][troop.col].troop = None
        self.tiles[new_row][new_col].troop = troop
        troop.row = new_row
        troop.col = new_col
        
        reward = Rewards.DEFAULT.value
        return reward

    def _attack(self, new_row, new_col, attacker, defender):
        attacker.moves = 0
        self._remove_fortify_bonus(attacker)
        #get the defending and attacking troops power
        def_power = defender.power 
        attack_power = attacker.power

        #formula: Damage(HP)=30*e^{0.04*StrengthDifference}*randomBetween(0.8-1.2)}
        rand = random.uniform(0.8, 1.2)
        damage_to_defender = 30*math.exp(0.04 * (attack_power-def_power)) * rand
        damage_to_attacker = 30*math.exp(0.04 * (def_power-attack_power)) * rand
        defender.health -= damage_to_defender
        attacker.health -= damage_to_attacker
        
        self._update_hp_power_loss(attacker)
        if isinstance(defender, Troop):
            self._update_hp_power_loss(defender)

        reward, terminated = self._handle_fight(attacker, defender)

        return reward, terminated
    
    def _update_hp_power_loss(self, troop):
        troop.power += troop.hp_power_loss
        troop.hp_power_loss = round(10 - (troop.health/10))
        troop.power -= troop.hp_power_loss
    
    def _handle_fight(self, attacker, defender):
        move_row, move_col = None, None
        reward = Rewards.ATTACK.value
        terminated = False
        unit_to_kill = None

        if defender.health <= 0 and attacker.health <= 0:
            # If both units are dead, kill the unit with the lowest health.
            unit_to_kill = min(defender, attacker, key=lambda troop: troop.health)
            # Give a little health to surviver
            if unit_to_kill == defender:
                attacker.health = 1
                move_row, move_col = defender.row, defender.col
            else:
                defender.health = 1

        elif defender.health <= 0:
            unit_to_kill = defender
            move_row, move_col = defender.row, defender.col
    
        elif attacker.health <= 0:
            unit_to_kill = attacker   

        # Finally, kill the designated unit and return the reward.
        if unit_to_kill:
            reward, terminated = self._kill_entity(unit_to_kill)
        #if attacker killed defender, move attacker
        if move_row is not None:
            self._move(move_row, move_col, attacker)

        return reward, terminated


    def _kill_entity(self, entity):
        if isinstance(entity, Troop):
            self.tiles[entity.row, entity.col].troop = None
            reward = Rewards.KILL_TROOP.value
            terminated = False
        elif isinstance(entity, Building):
            self.tiles[entity.row, entity.col].building = None
            reward = Rewards.KILL_CITY.value
            terminated = True
        return reward, terminated

