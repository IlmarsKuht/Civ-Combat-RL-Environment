import pygame
import gymnasium as gym
import numpy as np
import random

from collections import deque

from entities import Terrain, Troop, Building, Player
from options import BuildingType, TroopType, TileType, CnnChannels, ROWS, \
    COLUMNS, DIRECTIONS_EVEN, DIRECTIONS_ODD, Rewards, HEX_SIZE

#pygame grid

MARGIN = 30

#pygame window
WIDTH, HEIGHT = 1100, 1000

#might break if rows and columns are not even or might not, who knows :)

class Civ6CombatEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    #layer can try rgb_array rendering for CNNs.
    metadata = {"render_modes": ["human"], "render_fps": 1}

    def __init__(self, max_steps=100, render_mode=None):
        super().__init__()

        #Game variables
        self.player_mask = None

        #pygame variables
        self.window = None
        self.clock = None

        #FIGURE OUT WHAT ACTION SPACES TO USE
        self.action_space = gym.spaces.Box(low=0, high=1, shape=(ROWS*COLUMNS,))
        
        #Setting up observation space
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(len(CnnChannels), COLUMNS, ROWS,), dtype=np.float32)
        
        #check if render_mode is valid
        assert render_mode is None or render_mode in self.metadata["render_modes"], f"Invalid render mode, available render modes are {self.metadata['render_modes']}"
        self.render_mode = render_mode
        
        self.max_steps = max_steps

    #Translate game state to observation
    def _get_obs(self):
        observation = self.terrain.get_obs(self.player)
        
        #Keep the mask for valid actions later
        self.player_mask = observation[CnnChannels.CAN_MOVE.value, :, :]
        self.player_mask = np.where(self.player_mask == -1, 0, self.player_mask).astype(dtype=np.uint8).flatten()

        return observation
    
    def _get_info(self):
        #additional information not returned as observation
        return {}

    def step(self, action):
        #do the action
        reward, terminated, ai_turn, debug = self.terrain.action(action, self.player, self.player_mask)
        self._clean_up(self.player)
        self._clean_up(self.bot)
        

        #get the observations and additonal info

        if self.render_mode == "human" or debug:
            self._render_frame()

        #do AI move and render again
        if ai_turn:
            #action, troop = self._rand_action(self.bot)
            # if action is not None and troop is not None:
            #     reward -= self.terrain.action(action, troop)

            # self._clean_up(self.player)
            # self._clean_up(self.bot)

            #if self.render_mode == "human":
            #   self._render_frame()
            self._reset_moves(self.player)
            #self._reset_moves(self.bot)

        
        observation = self._get_obs()
        info = self._get_info()

        self.curr_steps += 1
        #check what to do with truncated
        truncated = self.curr_steps >= self.max_steps
        if truncated:
            reward = Rewards.LOSE_CITY.value

        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        #Initialize window and clock
        if self.render_mode == "human" and self.window == None and self.clock == None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()


        self.curr_steps = 0
        #reset the game
        if self.render_mode == "human":
            self.terrain = Terrain(ROWS, COLUMNS, True, HEX_SIZE, MARGIN)
        else:
            self.terrain = Terrain(ROWS, COLUMNS)

        #initalize the players
        self.player = Player("JiaoJiao")
        self.bot = Player("Ilmars")
        

        #Set the locations of cities, troops allied and enemy with self.np_random
        
        self._civ_generator(self.player, 3)
        self._civ_generator(self.bot, 0)
        # self._create_building(self.player, 200, 50, BuildingType.CENTER, 0, 1)
        # self._create_building(self.bot, 200, 50, BuildingType.CENTER, 5, 1)
        # self._create_troop(self.player, 100, 500, 2, 2, TroopType.WARRIOR, 0, 2)
       
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return observation, info
    
    def _civ_generator(self, player, troop_amount):
        #Generate a city in a random place
        max_attempts = ROWS*COLUMNS*5

        row = random.randrange(ROWS)
        col = random.randrange(COLUMNS)
        while self.terrain[row, col].owner is not None and max_attempts > 0:
            row = random.randrange(ROWS)
            col = random.randrange(COLUMNS)
            max_attempts -= 1
        if max_attempts == 0:
            raise RuntimeError("Couldn't find space for a city, too many cities for the map size")
        self._create_building(player, 200, 200, 50, BuildingType.CENTER, row, col)

        #generate troops adjacent to the city in a random place
        if troop_amount > 0:
            positions = self._get_troop_positions(row, col, troop_amount)
            for troop_row, troop_col in positions:
                self._create_troop(player, 100, 100, 50, 2, 2, TroopType.WARRIOR, troop_row, troop_col)

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()

    
    def _render_frame(self):
        self.window.fill((0, 0, 0))  # clear the screen before drawing
        self.terrain.draw(self.window) 

        pygame.event.pump()
        pygame.display.update()  
        self.clock.tick(self.metadata["render_fps"])
        
    
    def _create_troop(self, player : Player, health, max_health, power, moves, max_moves, type : TroopType, row, col):
        self.terrain[row][col].troop = Troop(health, max_health, power, moves, max_moves, player.id, type, row, col)
        player.troops.append(self.terrain[row][col].troop)

    def _create_building(self, player : Player, health, max_health, power, type : BuildingType, row, col):
        self.terrain[row][col].building = Building(health, max_health, power, player.id, type, row, col)
        player.buildings.append(self.terrain[row][col].building)
        self._update_ownership(row, col, player.id, 3)

    def _update_ownership(self, row, col, new_owner, distance=3):
        # Create a visited set to keep track of already visited nodes
        visited = set()

        # Use a queue to perform a breadth-first search
        queue = deque([(row, col, 0)])

        while queue:
            curr_row, curr_col, d = queue.popleft()

            if (curr_row, curr_col) in visited or d > distance:
                continue

            visited.add((curr_row, curr_col))

            # Only update the ownership if current owner is None
            if self.terrain[curr_row, curr_col].owner is None:
                self.terrain[curr_row, curr_col].owner = new_owner

            # Add neighbors to the queue
            directions = DIRECTIONS_EVEN if curr_row % 2 == 0 else DIRECTIONS_ODD
            for dr, dc in directions:
                nr, nc = curr_row + dr, curr_col + dc
                if 0 <= nr < ROWS and 0 <= nc < COLUMNS:
                    queue.append((nr, nc, d + 1))

    def _get_troop_positions(self, start_row, start_col, position_count):
        visited = set()
        queue = deque([(start_row, start_col)])
        free_positions = []

        while queue and len(free_positions) < position_count:
            curr_x, curr_y = queue.popleft()
            if (curr_x, curr_y) in visited:
                continue

            visited.add((curr_x, curr_y))

            # Check the tile's troop and building
            tile = self.terrain[curr_x, curr_y]
            if tile.troop is None and tile.building is None:
                free_positions.append((curr_x, curr_y))
                if len(free_positions) == position_count:
                    break

            # Add neighboring tiles to queue
            directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
            for dx, dy in directions:
                nx, ny = curr_x + dx, curr_y + dy
                if 0 <= nx < ROWS and 0 <= ny < COLUMNS:
                    queue.append((nx, ny))
        return free_positions
        
    
    
    
    #COULD COMBINE RESET MOVES AND CLEAN UP IN ONE FUNCTION? OR NOT BECUASE CLEAN UP AFTER EVERY STEP 
    # BUT RESET MOVES ONLY AFTER THE AI MOVES
    def _reset_moves(self, player : Player):
        for troop in player.troops:
            troop.moves = troop.max_moves

    #removes dead troops from players
    def _clean_up(self, player):
        for troop in player.troops:
            if troop.health <= 0:
                player.troops.remove(troop)








