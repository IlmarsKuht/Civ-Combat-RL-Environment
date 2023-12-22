import math
import pygame
import random

from collections import deque
import numpy as np


from options import TileType, CnnChannels, Rewards, \
DIRECTIONS_ODD, DIRECTIONS_EVEN, HEX_SIZE

class Tile:
    PLAINS_IMAGE = pygame.image.load('./images/hexagon.png')  
    PLAINS_IMAGE = pygame.transform.scale(PLAINS_IMAGE, (HEX_SIZE, HEX_SIZE))  
    PLAINS_IMAGE = pygame.transform.rotate(PLAINS_IMAGE, 90)

    HEXAGON_MOVE_OVERLAY_IMAGE = pygame.image.load('./images/overlay_move.png')  
    HEXAGON_MOVE_OVERLAY_IMAGE = pygame.transform.scale(HEXAGON_MOVE_OVERLAY_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HEXAGON_MOVE_OVERLAY_IMAGE = pygame.transform.rotate(HEXAGON_MOVE_OVERLAY_IMAGE, 90)

    HEXAGON_ATTACK_OVERLAY_IMAGE = pygame.image.load('./images/overlay_attack.png')  
    HEXAGON_ATTACK_OVERLAY_IMAGE = pygame.transform.scale(HEXAGON_ATTACK_OVERLAY_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HEXAGON_ATTACK_OVERLAY_IMAGE = pygame.transform.rotate(HEXAGON_ATTACK_OVERLAY_IMAGE, 90)

    FOREST_IMAGE = pygame.image.load('./images/forest.png')  
    FOREST_IMAGE = pygame.transform.scale(FOREST_IMAGE, (HEX_SIZE, HEX_SIZE))  
    FOREST_IMAGE = pygame.transform.rotate(FOREST_IMAGE, 90)

    HILLS_IMAGE = pygame.image.load('./images/hills.png')  
    HILLS_IMAGE = pygame.transform.scale(HILLS_IMAGE, (HEX_SIZE, HEX_SIZE))  
    HILLS_IMAGE = pygame.transform.rotate(HILLS_IMAGE, 90)

    MOUNTAIN_IMAGE = pygame.image.load('./images/mountain.png')  
    MOUNTAIN_IMAGE = pygame.transform.scale(MOUNTAIN_IMAGE, (HEX_SIZE, HEX_SIZE))  
    MOUNTAIN_IMAGE = pygame.transform.rotate(MOUNTAIN_IMAGE, 90)

    WATER_IMAGE = pygame.image.load('./images/water.png')  
    WATER_IMAGE = pygame.transform.scale(WATER_IMAGE, (HEX_SIZE, HEX_SIZE))  
    WATER_IMAGE = pygame.transform.rotate(WATER_IMAGE, 90)

    WARRIOR_IMAGE = pygame.image.load('./images/warrior.png')
    WARRIOR_IMAGE = pygame.transform.scale(WARRIOR_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    ARCHER_IMAGE = pygame.image.load('./images/archer.png')
    ARCHER_IMAGE = pygame.transform.scale(ARCHER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

    CITY_CENTER_IMAGE = pygame.image.load('./images/city_center.png')
    CITY_CENTER_IMAGE = pygame.transform.scale(CITY_CENTER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2)) 

    ENCAMPMENT_IMAGE = pygame.image.load('./images/encampment.png')
    ENCAMPMENT_IMAGE = pygame.transform.scale(ENCAMPMENT_IMAGE, (HEX_SIZE/2, HEX_SIZE/2)) 

    PROBABILITY_MATRIX = {
        TileType.SEA:      [0.5, 0.5, 0.0, 0.0, 0.0],
        TileType.PLAINS:   [0.1, 0.4, 0.2, 0.2, 0.1],
        TileType.HILLS:    [0.0, 0.2, 0.3, 0.3, 0.2],
        TileType.FOREST:   [0.0, 0.2, 0.3, 0.4, 0.1],
        TileType.MOUNTAIN: [0.0, 0.1, 0.2, 0.2, 0.5],
    }

    TILE_IMAGES = {
        TileType.PLAINS: PLAINS_IMAGE,
        TileType.HILLS: HILLS_IMAGE,
        TileType.FOREST: FOREST_IMAGE,
        TileType.MOUNTAIN: MOUNTAIN_IMAGE,
        TileType.SEA: WATER_IMAGE,
    }


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
        tile_image = Tile.TILE_IMAGES[self.type]

        window.blit(tile_image, (self.x-HEX_SIZE/2, self.y-HEX_SIZE/2))
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
                tile_type = self.choose_tile_type(row, col, tiles)

                # Determine obstacle and move_cost based on tile_type
                if tile_type in [TileType.MOUNTAIN, TileType.SEA]:
                    obstacle = True
                    move_cost = 0  # You can adjust this if needed
                elif tile_type in [TileType.HILLS, TileType.FOREST]:
                    obstacle = False
                    move_cost = 1.5  # Higher move cost for hills and forests
                else:
                    obstacle = False
                    move_cost = 1

                if draw:
                    x = HEX_SIZE * col + (HEX_SIZE / 2 * (row % 2))
                    y = HEX_SIZE * 0.75 * row
                    tile = Tile(tile_type, move_cost, obstacle, True, x + margin, y + margin)
                else:
                    tile = Tile(tile_type, move_cost, obstacle)

                rows.append(tile)
            tiles.append(rows)
        return np.array(tiles)
    
    def choose_tile_type(self, row, col, tiles):
        if row == 0 and col == 0:
            # Randomly choose an initial tile type for the first tile
            return random.choice(list(TileType))

        # Get neighboring tile types and calculate the probability for the next tile
        neighboring_types = self.get_neighboring_tile_types(row, col, tiles)
        probabilities = self.calculate_combined_probabilities(neighboring_types)

        # Choose the next tile type based on the calculated probabilities
        return random.choices(list(TileType), weights=probabilities, k=1)[0]
    
    def get_neighboring_tile_types(self, row, col, tiles):
        neighbors = []

        # Select the direction offsets based on the row
        directions = DIRECTIONS_EVEN if row % 2 == 0 else DIRECTIONS_ODD

        for dr, dc in directions:
            nr, nc = row + dr, col + dc  # Calculate the neighbor's row and column
            if 0 <= nr < self.row_count and 0 <= nc < self.column_count:
                if nr < len(tiles) and nc < len(tiles[nr]):
                    neighbors.append(tiles[nr][nc].type)

        return neighbors
    
    def calculate_combined_probabilities(self, neighboring_types):
        if not neighboring_types:
            return [1 / len(TileType)] * len(TileType)  # Equal probability if no neighbors

        combined_probabilities = [0] * len(TileType)
        for neighbor_type in neighboring_types:
            probabilities = Tile.PROBABILITY_MATRIX[neighbor_type]
            combined_probabilities = [sum(x) for x in zip(combined_probabilities, probabilities)]

        # Normalize to ensure the sum of probabilities is 1
        total = sum(combined_probabilities)
        return [p / total for p in combined_probabilities]


    #Observations need to be redone and rethought, they make no sense now, especially the positions and the mask there
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
                        new_values = troop.get_reachable_pos(self.tiles)
                        
                        current_values = observation[:, :, CnnChannels.CAN_MOVE.value]

                        # Only update current_values where it's -1 and new_values is either 0 or 1
                        # or where current_values is 0 and new_values is 1
                        mask = ((current_values == -1) & ((new_values > 0) | (new_values == 0) | (new_values == -2))) | ((current_values == 0) & (new_values == 1))
                        current_values[mask] = new_values[mask]
                        observation[:, :, CnnChannels.CAN_MOVE.value] = current_values


        #normalize power and health between 0 and 1
        #I don't need to do all of this, it's up to the guys who do reinforcment learning to do whatever
        #they want with the observations, make it much more simple, don't need normalization.
        #Don't need complicated stuff. Rethink all of these observations.
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
                
    def action(self, action, troops):
        reward = Rewards.DEFAULT.value
        moves = None

        (from_row, from_col), (to_row, to_col) = action

        from_troop = self.tiles[from_row, from_col].troop

        #Check if there is a troop and he has moves
        if from_troop is None or from_troop.moves <= 0:
            reward = Rewards.INVALID.value
            from_troop, to_row, to_col, moves = self._get_action(troops)
        #check if the destination is valid for that troop
        else:
            valid_actions = from_troop.get_reachable_pos(self.tiles)
            moves = valid_actions[to_row, to_col]
            if not (moves > 0 or moves == -2):
                reward = Rewards.INVALID.value
                from_troop, to_row, to_col, moves = self._get_action(troops)  
        
        to_troop = self.tiles[to_row, to_col].troop
        to_building = self.tiles[to_row, to_col].building

        #fortify if the same tile it's standing on
        if from_row == to_row and from_col == to_col:
            reward = from_troop.fortify()

        #if nothing or friendly building just move
        elif (to_troop is None and to_building is None) or \
            (to_building and to_building.player_id == from_troop.player_id):
            reward = from_troop.move(to_row, to_col, moves, self.tiles)

        #Attack
        else:
            target = to_building if to_building is not None else to_troop
            reward = from_troop.attack(target, self.tiles)

        return reward
    
    def _is_adjacent(self, row, col, target_row, target_col):
        target_directions = DIRECTIONS_EVEN if target_row % 2 == 0 else DIRECTIONS_ODD
        adjacent_cells = [(target_row + dx, target_col + dy) for dx, dy in target_directions
                    if 0 <= target_row + dx < self.row_count and 0 <= target_col + dy < self.column_count]
        return (row, col) in adjacent_cells
    
    def _get_action(self, troops):

        #filter troops which have moves
        filtered_troops = [troop for troop in troops if troop.moves > 0]

        #choose a troop at random
        troop = np.random.choice(filtered_troops)

        #get all valid actions (2d array with 1 indicating valid action)
        actions = troop.get_reachable_pos(self.tiles)

        # Find the indices where actions are valid
        valid_indices = np.where(actions >= 1)

        # Choose a random index from the valid indices
        # Note: valid_indices is a tuple of arrays, one for each dimension
        random_index = np.random.choice(range(len(valid_indices[0])))

        # Get the row and column of a random valid action
        target_row = valid_indices[0][random_index]
        target_col = valid_indices[1][random_index]

        #Get the moves required to get to this position
        moves = actions[target_row, target_col]

        return troop, target_row, target_col, moves

    def _attack(self, attacker, defender):
        return  attacker.attack(defender, self.tiles)
    
    def _cleanup(self, entities):
        for entity in entities:
            entity.remove_from_tiles(self.tiles)
