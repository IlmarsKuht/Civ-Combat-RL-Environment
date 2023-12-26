import pygame
from pygame.math import Vector2
import random

import numpy as np


from options import TileType, CnnChannels, Rewards, \
    DIRECTIONS_ODD, DIRECTIONS_EVEN, MARGIN, HEX_SIZE, worldToScreen, screenToWorld, \
    draw_centered

class Tile:
    BASE_PLAINS_IMAGE = pygame.transform.rotate(pygame.image.load('./images/hexagon.png'), 90)
    BASE_MOVE_OVERLAY_IMAGE = pygame.transform.rotate(pygame.image.load('./images/overlay_move.png'), 90)
    BASE_ATTACK_OVERLAY_IMAGE = pygame.transform.rotate(pygame.image.load('./images/overlay_attack.png'), 90)
    BASE_WATER_IMAGE = pygame.transform.rotate(pygame.image.load('./images/water.png'), 90)

    BASE_FOREST_IMAGE = pygame.image.load('./images/forest.png')
    BASE_HILLS_IMAGE = pygame.image.load('./images/hills.png')
    BASE_MOUNTAIN_IMAGE = pygame.image.load('./images/mountain.png')

    PLAINS_IMAGE = pygame.transform.scale(BASE_PLAINS_IMAGE, (HEX_SIZE, HEX_SIZE))
    MOVE_OVERLAY_IMAGE = pygame.transform.scale(BASE_MOVE_OVERLAY_IMAGE, (HEX_SIZE, HEX_SIZE))
    ATTACK_OVERLAY_IMAGE = pygame.transform.scale(BASE_ATTACK_OVERLAY_IMAGE, (HEX_SIZE, HEX_SIZE))
    WATER_IMAGE = pygame.transform.scale(BASE_WATER_IMAGE, (HEX_SIZE, HEX_SIZE))

    # Scale other images
    FOREST_IMAGE = pygame.transform.scale(BASE_FOREST_IMAGE, (int(HEX_SIZE * 2/3), int(HEX_SIZE * 2/3)))
    HILLS_IMAGE = pygame.transform.scale(BASE_HILLS_IMAGE, (int(HEX_SIZE * 2/3), int(HEX_SIZE * 2/3)))
    MOUNTAIN_IMAGE = pygame.transform.scale(BASE_MOUNTAIN_IMAGE, (int(HEX_SIZE * 2/3), int(HEX_SIZE * 2/3)))

    

    @classmethod
    def update_images(cls, scale):
        new_scale = HEX_SIZE * scale.x
        cls.PLAINS_IMAGE = pygame.transform.scale(cls.BASE_PLAINS_IMAGE, (new_scale, new_scale))
        cls.MOVE_OVERLAY_IMAGE = pygame.transform.scale(cls.BASE_MOVE_OVERLAY_IMAGE, (new_scale, new_scale))
        cls.ATTACK_OVERLAY_IMAGE = pygame.transform.scale(cls.BASE_ATTACK_OVERLAY_IMAGE, (new_scale, new_scale))
        cls.WATER_IMAGE = pygame.transform.scale(cls.BASE_WATER_IMAGE, (new_scale, new_scale))

        #overlay images are a little smaller so they fit in the tiles
        new_scale *= 2/3
        cls.FOREST_IMAGE = pygame.transform.scale(cls.BASE_FOREST_IMAGE, (int(new_scale), int(new_scale)))
        cls.HILLS_IMAGE = pygame.transform.scale(cls.BASE_HILLS_IMAGE, (int(new_scale), int(new_scale)))
        cls.MOUNTAIN_IMAGE = pygame.transform.scale(cls.BASE_MOUNTAIN_IMAGE, (int(new_scale), int(new_scale)))

    #These are quite random, need to adjust them
    PROBABILITY_MATRIX = {
        TileType.WATER:     [0.2, 0.4, 0.2, 0.2, 0.0],
        TileType.PLAINS:    [0.1, 0.5, 0.2, 0.1, 0.1],  
        TileType.FOREST:    [0.1, 0.2, 0.4, 0.2, 0.1],  
        TileType.HILLS:     [0.0, 0.2, 0.3, 0.4, 0.1],  
        TileType.MOUNTAIN:  [0.0, 0.2, 0.2, 0.3, 0.2],  
    }


    def __init__(self, type:TileType, move_cost=1, obstacle=False, draw=False, row=None, col=None, \
                 owner=None, highlight_move=False, highlight_attack=False):
        if draw:
            self.row = row 
            self.col = col
            self.highlight_move = highlight_move
            self.highlight_attack = highlight_attack
        self.obstacle = obstacle
        self.troop = None
        self.building = None
        self.type = type
        self.move_cost = move_cost
        self.owner = owner

    def _get_type_images(self):
        background = None
        foreground = None
        match self.type:
            case TileType.WATER:
                background = Tile.WATER_IMAGE
            case TileType.PLAINS:
                background = Tile.PLAINS_IMAGE
            case TileType.FOREST:
                background = Tile.PLAINS_IMAGE
                foreground = Tile.FOREST_IMAGE
            case TileType.HILLS:
                background = Tile.PLAINS_IMAGE
                foreground = Tile.HILLS_IMAGE
            case TileType.MOUNTAIN:
                background = Tile.PLAINS_IMAGE
                foreground = Tile.MOUNTAIN_IMAGE
        return background, foreground

    #Probably I can calculate HEX_SIZE * zoom offset whatever and only calcualte it once and use it everywhere, will it be faster?
    def draw(self, window, player_id, offset, scale):
        self.update_images(scale)
        x = (HEX_SIZE * self.col + (HEX_SIZE / 2 * (self.row % 2))) + HEX_SIZE / 2 + MARGIN 
        y = (HEX_SIZE * 0.75 * self.row) + HEX_SIZE / 2 + MARGIN
        
        background, foreground = self._get_type_images()
        #top left corner of tile
        tile_pos = worldToScreen(Vector2(x - HEX_SIZE/2, y - HEX_SIZE/2), offset, scale)
        #middle of tile
        tile_mid_pos = worldToScreen(Vector2(x, y), offset, scale)

        if background is not None:
            window.blit(background, tile_pos)

        if foreground is not None:
            draw_centered(window, foreground, tile_mid_pos)

        if self.highlight_move:
            window.blit(Tile.MOVE_OVERLAY_IMAGE, tile_pos)

        if self.highlight_attack:
            window.blit(Tile.ATTACK_OVERLAY_IMAGE, tile_pos)

        # Draw Troop
        if self.troop:
            self.troop.draw(window, player_id, offset, scale)

        # Draw Building
        if self.building:
            self.building.draw(window, player_id, offset, scale)


class Terrain:
    def __init__(self, row_count, column_count, draw=False):
        self.row_count = row_count
        self.column_count = column_count
        self.tiles = self.create_tiles(draw)
        self.movement_costs = None

    def __getitem__(self, index):
        return self.tiles[index]
    
    def create_tiles(self, draw):
        tiles = []
        for row in range(self.row_count):
            rows = []
            for col in range(self.column_count):
                tile_type = self.choose_tile_type(row, col, tiles)
                obstacle = False
                move_cost = 1

                if tile_type == TileType.MOUNTAIN:
                    obstacle = True
                    move_cost = 0
                elif tile_type == TileType.WATER:
                    obstacle = True
                    move_cost = 0
                elif tile_type == TileType.HILLS:
                    obstacle = False
                    move_cost = 1.5
                elif tile_type == TileType.FOREST:
                    obstacle = False
                    move_cost = 1.5

                if draw:
                    tile = Tile(tile_type, move_cost, obstacle, True, row=row, col=col)
                else:
                    tile = Tile(tile_type, move_cost, obstacle)

                rows.append(tile)
            tiles.append(rows)
        return np.array(tiles)
    
    def draw(self, window, player_id, offset, scale):
        for row in self.tiles:
            for tile in row:
                tile.draw(window, player_id, offset, scale)
    
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
