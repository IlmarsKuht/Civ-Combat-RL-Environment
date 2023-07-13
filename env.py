import pygame
import gymnasium as gym
import numpy as np
import random

from collections import deque

from entities import Terrain, Troop, Building, Player
from options import BuildingType, TroopType, TileType, CnnChannels, ROWS, \
    COLUMNS, DIRECTIONS_EVEN, DIRECTIONS_ODD, Rewards, HEX_SIZE, MARGIN, \
    WIDTH, HEIGHT

#pygame grid

#might break if rows and columns are not even or might not, who knows :)

class Civ6CombatEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    #layer can try rgb_array rendering for CNNs.
    metadata = {"render_modes": ["human", "interactable"], "render_fps": 5}

    def __init__(self, max_steps=100, render_mode=None):
        super().__init__()

        #Game variables

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
        
        return observation
    
    def _get_info(self):
        #additional information not returned as observation
        return {}

    def step(self, action, troop=None):
        #if troop not chosen get all troops with moves
        troops = [troop] if troop else [player_troop for player_troop in self.player.troops if player_troop.moves > 0]
        #do the action
        reward = self.terrain.action(action, troops=troops)

        if self.render_mode in ["human", "interactable"]:
            self._render_frame()

        second_reward, terminated, truncated = self._after_step()
        reward += second_reward
        
        observation = self._get_obs()
        info = self._get_info()
        return observation, reward, terminated, truncated, info
    
    def _after_step(self):
        reward = 0
        terminated = False
        truncated = False

        #do ai move, reset player moves
        ai_turn = all([troop.moves==0 for troop in self.player.troops])
        if ai_turn:
            #it's already negated
            self._reset_moves(self.player)
            for bot in self.bots:
                reward += self._ai_sim(bot)
                self._reset_moves(bot)
            if self.render_mode in ["human", "interactable"]:
                self._render_frame()

        self._clean_up(self.player)
        for bot in self.bots:
            self._clean_up(bot)

        self.curr_steps += 1
        truncated = self.curr_steps >= self.max_steps

        #check if player lost
        if len(self.player.troops) == 0 or len(self.player.buildings) == 0 or truncated:
            terminated = True
            reward -= Rewards.WIN_GAME.value

        #check if player won
        if all([len(bot.buildings)==0 for bot in self.bots]):
            terminated = True
            reward += Rewards.WIN_GAME.value
        return reward, terminated, truncated
    
    def _ai_sim(self, bot : Player):
        reward = 0
        for troop in [troop for troop in bot.troops if troop.moves > 0]:
            possible_moves = self.terrain.get_reachable_pos([troop])
            indices = np.where(possible_moves == 1)
            indices = list(zip(indices[0], indices[1]))
            random_move = random.choice(indices)
            reward -= self.terrain.action(random_move, [troop])
        return reward


    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        #Initialize window and clock
        if self.render_mode in ["human", "interactable"] and self.window == None and self.clock == None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()


        self.curr_steps = 0
        #reset the game
        if self.render_mode in ["human", "interactable"]:
            self.terrain = Terrain(ROWS, COLUMNS, True, HEX_SIZE, MARGIN)
        else:
            self.terrain = Terrain(ROWS, COLUMNS)

        #initalize the players
        self.player = Player("JiaoJiao")
        self.bots = [Player("Ilmars"), Player("ChouChou")]
        

        #Set the locations of cities, troops allied and enemy with self.np_random
        
        self._civ_generator(self.player, 7)
        for bot in self.bots:
            self._civ_generator(bot, 2)
       
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode in ["human", "interactable"]:
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
                self._create_troop(player, 100, 100, 55, 2, 2, TroopType.WARRIOR, troop_row, troop_col)

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
        
    def _reset_moves(self, player : Player):
        for troop in player.troops:
            troop.moves = troop.max_moves

    #removes dead troops from players
    def _clean_up(self, player):
        for troop in player.troops:
            if troop.health <= 0:
                player.troops.remove(troop)
        for building in player.buildings:
            if building.health <= 0:
                player.buildings.remove(building)



    def start_interactable(self):
        if self.render_mode != "interactable":
            raise RuntimeError("Render mode is not in interactable mode")

        self.reset()

        running = True
        troop_to_move = None
        terminated, truncated = False, False

        while running: 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    
                    #get mouse position
                    x, y= pygame.mouse.get_pos()
    
                    # Convert pixel coordinates to tile coordinates
                    # inverting the hex grid placement formula in entities
                    row = round((y-HEX_SIZE/2-MARGIN)/(HEX_SIZE*3/4))
                    col = round(((x-HEX_SIZE/2-MARGIN) - ((HEX_SIZE / 2) * (row % 2)))/HEX_SIZE)

                    if 0 <= row < ROWS and 0 <= col < COLUMNS:
                        tile = self.terrain[row, col]
                        if troop_to_move:
                            #Move the troop to the tile if he can move there
                            if tile.highlight == True:
                                _, _, terminated, truncated, _ = self.step((row, col), troop=troop_to_move)
                            #Clear the highlights off the board
                            for tile_row in range(ROWS):
                                for tile_col in range(COLUMNS):
                                    self.terrain[tile_row, tile_col].highlight = False
                            troop_to_move = None

                        #if friendly troop with moves
                        elif tile.troop and tile.troop.moves > 0 and tile.troop.player_id == self.player.id:
                            troop_to_move = tile.troop
                            #highlight the moves of the troop
                            obs = self.terrain.get_reachable_pos([troop_to_move])
                            for tile_row in range(ROWS):
                                for tile_col in range(COLUMNS):
                                    self.terrain[tile_row, tile_col].highlight = True if obs[tile_row, tile_col] == 1 else False

                        if terminated or truncated:
                            self.reset()
                            terminated, truncated = False, False
                        else:
                            self._render_frame()


            






