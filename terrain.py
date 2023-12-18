import math
import pygame
import random

from collections import deque
import numpy as np


from options import TileType, CnnChannels, Rewards, \
DIRECTIONS_ODD, DIRECTIONS_EVEN, HEX_SIZE, FortifiedBonus

from entities import Warrior, Archer, Center, Troop

class Tile:
    HEXAGON_IMAGE = pygame.image.load('./images/hexagon.png')  
    HEXAGON_IMAGE = pygame.transform.scale(HEXAGON_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HEXAGON_IMAGE = pygame.transform.rotate(HEXAGON_IMAGE, 90)

    HEXAGON_MOVE_OVERLAY_IMAGE = pygame.image.load('./images/overlay_move.png')  
    HEXAGON_MOVE_OVERLAY_IMAGE = pygame.transform.scale(HEXAGON_MOVE_OVERLAY_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HEXAGON_MOVE_OVERLAY_IMAGE = pygame.transform.rotate(HEXAGON_MOVE_OVERLAY_IMAGE, 90)

    HEXAGON_ATTACK_OVERLAY_IMAGE = pygame.image.load('./images/overlay_move.png')  
    HEXAGON_ATTACK_OVERLAY_IMAGE = pygame.transform.scale(HEXAGON_ATTACK_OVERLAY_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HEXAGON_ATTACK_OVERLAY_IMAGE = pygame.transform.rotate(HEXAGON_ATTACK_OVERLAY_IMAGE, 90)

    WARRIOR_IMAGE = pygame.image.load('./images/warrior.png')
    WARRIOR_IMAGE = pygame.transform.scale(WARRIOR_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    ARCHER_IMAGE = pygame.image.load('./images/archer.png')
    ARCHER_IMAGE = pygame.transform.scale(ARCHER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    CITY_CENTER_IMAGE = pygame.image.load('./images/city_center.png')
    CITY_CENTER_IMAGE = pygame.transform.scale(CITY_CENTER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    def __init__(self, type:TileType, move_cost=1, obstacle=False, draw=False, x=None, y=None, owner=None, highlight_move=False, highlight_attack=False):
        if draw:
            self.x = x+HEX_SIZE/2
            self.y = y+HEX_SIZE/2
            self.highlight_move = highlight_move
            self.highlight_attack = highlight_attack
        self.obstacle = obstacle
        self.troop = None
        self.building = None
        self.type = type
        self.move_cost = move_cost
        self.owner = owner

    
    def _draw_centered(self, window, image, x, y):
        rect = image.get_rect(center=(x, y))
        window.blit(image, rect)

    def draw(self, window, player_id):
        #Draw hexagon
        #I have centered x and y, so I need to adjust the tiles, so everthing else can stay the same
        window.blit(Tile.HEXAGON_IMAGE, (self.x-HEX_SIZE/2, self.y-HEX_SIZE/2))
        if self.highlight_move:
            window.blit(Tile.HEXAGON_MOVE_OVERLAY_IMAGE, (self.x-HEX_SIZE/2, self.y-HEX_SIZE/2))
        if self.highlight_attack:
            window.blit(Tile.HEXAGON_ATTACK_OVERLAY_IMAGE, (self.x-HEX_SIZE/2, self.y-HEX_SIZE/2))

        # Draw Troop
        if self.troop:
            self.troop.draw(window, player_id)

        # Draw Building
        if self.building:
            self.building.draw(window, player_id)

class Terrain:
    def __init__(self, row_count, column_count, draw=False, margin=None):
        self.row_count = row_count
        self.column_count = column_count
        self.tiles = self.create_tiles(draw, margin)
        self.movement_costs = None


    def __getitem__(self, index):
        return self.tiles[index]

    def create_tiles(self, draw, margin):
        tiles = []
        for row in range(self.row_count):
            rows = []
            for col in range(self.column_count):
                if draw:
                    x = HEX_SIZE * col + (HEX_SIZE/2 * (row % 2)) 
                    y = HEX_SIZE * 0.75 * row
                    tile = Tile(TileType.PLAINS, 1, False, True, x+margin, y+margin)
                else:
                    tile = Tile(TileType.PLAINS)
                rows.append(tile)
            tiles.append(rows)
        return np.array(tiles)


    def get_best_path(self, row, col, troops):
        nearest_troop = None
        min_moves = float('inf')
        best_path = []

        for troop in troops:
            #x, y, movement_points, moves used, path to tile
            queue = deque([(troop.row, troop.col, troop.moves, 0, [(troop.row, troop.col)])])

            while queue:
                curr_x, curr_y, movement_left, moves, path = queue.popleft()
                # Not reachable
                if movement_left < 0 or self.tiles[curr_x, curr_y].obstacle:
                    continue

                # Reached target
                if curr_x == row and curr_y == col:
                    if moves < min_moves:
                        min_moves = moves
                        nearest_troop = troop
                        best_path = path

                # Can't move to here, don't look
                elif (curr_x != troop.row or curr_y != troop.col) and (self.tiles[curr_x, curr_y].troop or \
                    (self.tiles[curr_x, curr_y].building and self.tiles[curr_x, curr_y].building.player_id != troop.player_id)):
                    continue

                directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
                for dx, dy in directions:
                    nx, ny = curr_x + dx, curr_y + dy
                    if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                        new_path = path + [(nx, ny)]
                        queue.append((nx, ny, movement_left - 1, moves+1, new_path))

        return nearest_troop, min_moves, best_path
    
    #this could probably be optimized
    def get_reachable_pos(self, troops):
        observation = np.full((self.row_count, self.column_count), -1)
        for troop in troops:
            # Use a queue to perform a breadth-first search
            queue = deque([(troop.row, troop.col, 0)])
            max_moves = troop.moves
            while queue:
                curr_x, curr_y, moves = queue.popleft()
                curr_tile = self.tiles[curr_x, curr_y]
                curr_obs = observation[curr_x, curr_y]

                # Not reachable
                if moves > max_moves or curr_tile.obstacle:
                    continue
                # Not improvable
                if curr_obs > 0 and curr_obs < moves:
                    continue

                # Check the tile's troop and building
                tile_troop = curr_tile.troop
                tile_building = curr_tile.building

                #Friendly troop (not starting position)
                if (curr_x != troop.row or curr_y != troop.col) \
                    and (tile_troop and tile_troop.player_id == troop.player_id):
                    if observation[curr_x, curr_y] != 1:
                        observation[curr_x, curr_y] = 0
                    continue

                #enemy troop or building
                elif (tile_troop and tile_troop.player_id != troop.player_id) \
                    or (tile_building and tile_building.player_id != troop.player_id):
                    observation[curr_x, curr_y] = 1
                    continue
                #just move
                else:
                    observation[curr_x, curr_y] = 1
                    

                directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
                for dx, dy in directions:
                    nx, ny = curr_x + dx, curr_y + dy
                    if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                        queue.append((nx, ny, moves+self.tiles[nx, ny].move_cost))
        return observation
    
    #Important when adding new terrain!!!
    #later need to update it so that it works wit hills and forests (blocked vision etc.)
    def range_attackable_pos(self, troops): #Marks possible ranged attacks from current position
        observation = np.full((self.row_count, self.column_count), -1)
        for troop in troops:
            # row, col, range
            queue = deque([(troop.row, troop.col, 2)])
            while queue:
                curr_x, curr_y, range = queue.popleft()
                #skip if no range left
                if range < 0:
                    continue

                curr_tile = self.tiles[curr_x, curr_y]
                tile_troop = curr_tile.troop
                tile_building = curr_tile.building

                # Mark if enemy
                if (tile_troop and tile_troop.player_id != troop.player_id) \
                    or (tile_building and tile_building.player_id != troop.player_id):
                    observation[curr_x, curr_y] = 1
                    

                directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
                for dx, dy in directions:
                    nx, ny = curr_x + dx, curr_y + dy
                    if nx >= 0 and nx < self.row_count and ny >= 0 and ny < self.column_count:
                        queue.append((nx, ny, range-1))
        return observation

    
    def get_obs(self, player): 
        observation = np.full((self.row_count, self.column_count, len(CnnChannels)), -1, dtype=np.float32)

        #For now let's assume that the player with id 0 is our player and all others are enemies

        #Keep track of health and power, I need to normalize them afterwards
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
                        #this can be optimized by just passing all the troops once
                        new_values = self.get_reachable_pos([troop])
                        
                        current_values = observation[:, :, CnnChannels.CAN_MOVE.value]

                        # Only update current_values where it's -1 and new_values is either 0 or 1
                        # or where current_values is 0 and new_values is 1
                        mask = ((current_values == -1) & ((new_values == 1) | (new_values == 0))) | ((current_values == 0) & (new_values == 1))
                        current_values[mask] = new_values[mask]
                        observation[:, :, CnnChannels.CAN_MOVE.value] = current_values


        #normalize power and health between 0 and 1
        max_power = max([power for power, _ in troop_powers] + [power for power, _ in building_powers])
        max_health = max([health for health, _ in troop_healths] + [health for health, _ in building_healths])
        for power, (row, col) in troop_powers:
            observation[row, col, CnnChannels.TROOP_POWER.value] = power/max_power
        for health, (row, col) in troop_healths:
            observation[row, col, CnnChannels.TROOP_HEALTH.value] = health/max_health
        for power, (row, col) in building_powers:
            observation[row, col, CnnChannels.BUILDING_POWER.value] = power/max_power
        for health, (row, col) in building_healths:
            observation[row, col, CnnChannels.BUILDING_HEALTH.value] = health/max_health

        #I AM LAZY, NEEDT TO CHANGE CODE BUT LET'S SEE IF THIS EVEN WORKS
        # Reorder dimensions to (Channels, Rows, Columns)
        observation = np.transpose(observation, (2, 0, 1))

        return observation
    
    def draw(self, window, player_id):
        for row in self.tiles:
            for tile in row:
                tile.draw(window, player_id)

    #For interactive mode action is (row, col)
    #otherwise grid of all possibilities and mask masking the actions
    #probably the mask should be implemented in the terrain not in the environment? what do you think

    #REMOVE THE PLAYER, WE DON'T NEED HIM, JUST STRAIGHT UP PASS IN THE TROOPS
    def action(self, actions, troops):
        reward = Rewards.DEFAULT.value
        no_model_action = False
        path = []
        
        if len(actions) != 2:
            #chooses a random move if model didn't have a move
            target_row, target_col, no_model_action = self._get_action(actions, troops)
        else:
            #When a move is chosen
            target_row = actions[0]
            target_col = actions[1]

        #when getting a best path for archer, there is no path because he might not be able to move there, only shoot
        #also shouldn't 
        troop, moves, path = self.get_best_path(target_row, target_col, troops)  
        
        target_troop = self.tiles[target_row, target_col].troop
        target_building = self.tiles[target_row, target_col].building

        #fortify if the same tile it's standing on
        if target_row == troop.row and target_col == troop.col:
            reward = self._fortify(troop)
        #just move
        elif (target_troop is None and target_building is None) or \
            (target_building and target_building.player_id == troop.player_id):
            reward = self._move(target_row, target_col, troop)
            troop.moves -= moves
        #move next to target (if needed) and attack
        elif isinstance(troop, Warrior):
            #no reward update because already attacking
            self._move(path[-2][0], path[-2][1], troop)
            #then attack
            if target_building:
                reward = self._attack(troop, target_building)
            elif target_troop:
                reward = self._attack(troop, target_troop)
        elif isinstance(troop, Archer):
            #make archer not get damaged attacking
            if target_building:
                reward = self._attack(troop, target_building)
            elif target_troop:
                reward = self._attack(troop, target_troop)
                

        #give bad reward and choose
        if no_model_action:
            reward = Rewards.INVALID.value

        return reward
    
    def _is_adjacent(self, row, col, target_row, target_col):
        target_directions = DIRECTIONS_EVEN if target_row % 2 == 0 else DIRECTIONS_ODD
        adjacent_cells = [(target_row + dx, target_col + dy) for dx, dy in target_directions
                    if 0 <= target_row + dx < self.row_count and 0 <= target_col + dy < self.column_count]
        return (row, col) in adjacent_cells
    
    def _get_action(self, actions, troops):
        no_model_action = False

        #get all valid actions
        mask = self.get_reachable_pos(troops).flatten()
        attack_mask = self.range_attackable_pos(troops).flatten()
        #combine masks
        temp_mask = attack_mask > mask
        mask[temp_mask] = attack_mask[temp_mask]

        #mask invalid actions
        actions = actions*mask
        
        valid_indices = np.where(actions != 0)[0]

        # If no valid actions from model.
        if len(valid_indices) == 0:
            valid_indices = np.where(mask == 1)[0]
            no_model_action = True

        valid_actions = actions[valid_indices]
        max_action_index = np.argmax(valid_actions)

        # Map this back to the original array's indices.
        action = valid_indices[max_action_index]

        target_row, target_col = divmod(action, self.row_count) 
        return target_row, target_col, no_model_action
       
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
        #increase the power of the troop while fortified
        reward = Rewards.DEFAULT.value
        #only update moves at the end, else will mess up the calculation above
        troop.moves = 0
        return reward
    
    def _remove_fortify_bonus(self, troop):
        troop.power -= troop.fortified.value
        troop.fortified = FortifiedBonus.NONE

    def _move(self, new_row, new_col, troop):
        #don't set the moves to zero, instead minus the moves made by the player so he can move and attack
        self._remove_fortify_bonus(troop)

        self.tiles[troop.row][troop.col].troop = None
        self.tiles[new_row][new_col].troop = troop
        troop.row = new_row
        troop.col = new_col

        reward = Rewards.DEFAULT.value
        return reward

    def _attack(self, attacker, defender):
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

        reward = self._handle_fight(attacker, defender)

        return reward
    
    def _update_hp_power_loss(self, troop):
        troop.power += troop.hp_power_loss
        troop.hp_power_loss = round(10 - (troop.health/10))
        troop.power -= troop.hp_power_loss
    
    def _handle_fight(self, attacker, defender):
        move_row, move_col = None, None
        reward = Rewards.ATTACK.value
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
            kill_reward = self._kill_entity(unit_to_kill)
            reward += kill_reward if unit_to_kill==defender else -kill_reward
        #if attacker killed defender, move attacker
        if move_row is not None:
            self._move(move_row, move_col, attacker)
        return reward


    def _kill_entity(self, entity):
        if isinstance(entity, Troop):
            self.tiles[entity.row, entity.col].troop = None
            reward = Rewards.KILL_TROOP.value
        #only works for center...
        elif isinstance(entity, Center):
            self.tiles[entity.row, entity.col].building = None
            reward = Rewards.KILL_CITY.value
        return reward
    
    def _cleanup(self, id):
        reward = 0
        for row in self.tiles:
            for tile in row:
                if tile.troop and tile.troop.player_id==id:
                    reward += self._kill_entity(tile.troop)
                if tile.building and tile.building.player_id==id:
                    reward += self._kill_entity(tile.building)
        return reward
