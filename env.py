import pygame
import gymnasium as gym
import numpy as np
import random

from collections import deque

from terrain import Terrain
from entities import Warrior, Archer, Center, Player
from options import CnnChannels, DIRECTIONS_EVEN, DIRECTIONS_ODD, Rewards, \
    HEX_SIZE, MARGIN, WIDTH, HEIGHT, Colors

#pygame grid

#might break if rows and columns are not even or might not, who knows :)

class Civ6CombatEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    #layer can try rgb_array rendering for CNNs.
    metadata = {"render_modes": ["human", "interactable"], "render_fps": 2}

    def __init__(self, rows=6, columns=6, max_steps=100, render_mode=None, bots=1, start_troops=2, fps=None):
        super().__init__()
        if fps:
            self.metadata["render_fps"] = fps
        #Game variables
        self.row_count = rows
        self.col_count = columns
        self.bot_count = bots
        self.start_troop_count = start_troops
        self.bots = []

        #Game stats
        self.last_game_won = None
        self.score = 0
        self.all_scores = 0
        self.wins = 0
        self.losses = 0

        #pygame variables
        self.window = None
        self.clock = None

        self.action_space = gym.spaces.Tuple((
            gym.spaces.Tuple((gym.spaces.Discrete(rows), gym.spaces.Discrete(columns))), # Tuple for 'what to move'
            gym.spaces.Tuple((gym.spaces.Discrete(rows), gym.spaces.Discrete(columns)))  # Tuple for 'where to move'
        ))
        
        #Setting up observation space
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(len(CnnChannels), self.col_count, self.row_count,), dtype=np.float32)
        
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

    def step(self, action):
        #do the action
        reward = self.terrain.action(action, self.player.troops)

        second_reward, terminated, truncated = self._after_step()
        reward += second_reward
        
        observation = self._get_obs()
        info = self._get_info()

        #doesn't update instantly, only shows the scores updated in the last step
        self.score += reward
        return observation, reward, terminated, truncated, info
    
    def _after_step(self):
        reward = 0
        terminated = False
        truncated = False

        #cleanup before AI move and after
        reward -= self._cleanup(self.player)
        for bot in self.bots:
            reward += self._cleanup(bot)

        if self.render_mode in ["human", "interactable"]:
            self._render_frame()

        #do ai move, reset player moves
        ai_turn = all([troop.moves==0 for troop in self.player.troops])
        if ai_turn:
            self._reset_moves(self.player)
            for bot in self.bots:
                reward += self._ai_sim(bot)
                self._reset_moves(bot)

            reward -= self._cleanup(self.player)
            for bot in self.bots:
                reward += self._cleanup(bot)

        self.curr_steps += 1
        truncated = self.curr_steps >= self.max_steps

        #check if player lost
        if len(self.player.troops) == 0 or len(self.player.buildings) == 0 or truncated:
            terminated = True
            reward -= Rewards.WIN_GAME.value
            self.last_game_won = False
            self.losses += 1

        #check if player won
        if all([len(bot.buildings)==0 for bot in self.bots]):
            terminated = True
            reward += Rewards.WIN_GAME.value
            self.last_game_won = True
            self.wins += 1

        return reward, terminated, truncated
    
    def _ai_sim(self, bot : Player):
        reward = 0
        troops = deque([troop for troop in bot.troops if troop.moves > 0])
        while troops:
            troop = troops.popleft()
            possible_moves = self.terrain.get_reachable_pos(troop)
            indices = np.where((possible_moves > 0) | (possible_moves == -2))
            random_index = np.random.choice(range(len(indices[0])))

            # Get the row and column of a random valid action
            target_row = indices[0][random_index]
            target_col = indices[1][random_index]

            reward -= self.terrain.action(((troop.row, troop.col), (target_row, target_col)), troops)
            if self.render_mode in ["human", "interactable"]:
                self._render_frame()
            #if still has moves, put it back
            if troop.moves > 0:
                troops.append(troop)
        return reward
    
    #removes dead troops and buildings from players
    def _cleanup(self, player : Player):
        #if eliminating a CIV you also kill all the troops so bonus reward
        reward = 0
        for building in player.buildings:
            if building.health <= 0:
                player.buildings.remove(building)
        if len(player.buildings) == 0:
            reward += self.terrain._cleanup(player.id)
            player.troops = []
        else: 
            for troop in player.troops:
                if troop.health <= 0:
                    player.troops.remove(troop)
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

        #add the old score to total before resetting
        self.all_scores += self.score
        self.score = 0

        self.curr_steps = 0
        #reset the game
        if self.render_mode in ["human", "interactable"]:
            self.terrain = Terrain(self.row_count, self.col_count, True, MARGIN)
        else:
            self.terrain = Terrain(self.row_count, self.col_count)

        #initalize the players
        self.player = Player("Hero")
        self.bots = []
        for i in range(self.bot_count):
            self.bots.append(Player(f"{i}"))
        

        #Set the locations of cities, troops allied and enemy with self.np_random
        
        self._civ_generator(self.player, self.start_troop_count)
        for bot in self.bots:
            self._civ_generator(bot, self.start_troop_count)
       
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode in ["human", "interactable"]:
            self._render_frame()

        return observation, info
    
    def _civ_generator(self, player, troop_amount):
        #Generate a city in a random place
        max_attempts = self.row_count*self.col_count*5

        row = random.randrange(self.row_count)
        col = random.randrange(self.col_count)
        while self.terrain[row, col].owner is not None and max_attempts > 0:
            row = random.randrange(self.row_count)
            col = random.randrange(self.col_count)
            max_attempts -= 1
        if max_attempts == 0:
            raise RuntimeError("Couldn't find space for a city, too many cities for the map size")
        self._create_center(player, 200, 200, 50, row, col)

        #generate troops adjacent to the city in a random place
        if troop_amount > 0:
            #I MAKE 2 TIMES MORE TROOPS, REMOVE LATER PROBABLY
            positions = self._get_troop_positions(row, col, troop_amount)
            for troop_row, troop_col in positions:
                self._create_warrior(player, 2, 2, 100, 100, 55, troop_row, troop_col)
            positions = self._get_troop_positions(row, col, troop_amount)
            for troop_row, troop_col in positions:
                self._create_archer(player, 2, 2, 2, 100, 100, 55, troop_row, troop_col)
                

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()

    def _render_frame(self):
        self.window.fill((0, 0, 0))  # clear the screen before drawing
        self.terrain.draw(self.window, self.player.id)
        self._render_game_info()

        pygame.event.pump()
        pygame.display.update()  
        self.clock.tick(self.metadata["render_fps"])
    
    def _render_game_info(self):
        x = MARGIN
        y = HEX_SIZE * 0.75 * (self.row_count+1) + MARGIN
        font_size = int(HEX_SIZE/5)
        font = pygame.font.Font(None, font_size)
        average_score = self.all_scores / (self.wins+self.losses) if self.wins+self.losses != 0 else 0
        scores_text = font.render(f"Last Game Won: {self.last_game_won} | Score: {self.score} | Average Score: {average_score:.2f}", True, Colors.WHITE.value)
        ratio = self.wins*100 / (self.wins+self.losses) if self.wins+self.losses != 0 else 0
        win_losses_text = font.render(f"Wins: {self.wins} | Losses: {self.losses} | Win Ratio: {ratio:.2f}%", True, Colors.WHITE.value)
        self.window.blit(scores_text, (x, y))
        y += font_size
        self.window.blit(win_losses_text, (x, y))
        
    
    def _create_warrior(self, player : Player, moves, max_moves, health, max_health, power, row, col):
        self.terrain[row][col].troop = Warrior(moves, max_moves, health, max_health, power,  player.id, row, col)
        player.troops.append(self.terrain[row][col].troop)
    
    def _create_archer(self, player : Player, range, moves, max_moves, health, max_health, power, row, col):
        self.terrain[row][col].troop = Archer(range, moves, max_moves, health, max_health, power,  player.id, row, col)
        player.troops.append(self.terrain[row][col].troop)

    def _create_center(self, player : Player, health, max_health, power, row, col):
        self.terrain[row][col].building = Center(health, max_health, power, player.id, row, col)
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
                if 0 <= nr < self.row_count and 0 <= nc < self.col_count:
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
                if 0 <= nx < self.row_count and 0 <= ny < self.col_count:
                    queue.append((nx, ny))
        return free_positions
        
    def _reset_moves(self, player : Player):
        for troop in player.troops:
            troop.moves = troop.max_moves


    #Some problem with this probably, have to press M two times to move
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

                    if 0 <= row < self.row_count and 0 <= col < self.col_count:
                        tile = self.terrain[row, col]
                        if troop_to_move:
                            #Move the troop to the tile if he can move there
                            if tile.highlight_move or tile.highlight_attack:
                                #Clear the highlight_moves off the board
                                for tile_row in range(self.row_count):
                                    for tile_col in range(self.col_count):
                                        self.terrain[tile_row, tile_col].highlight_move = False
                                        self.terrain[tile_row, tile_col].highlight_attack = False
                                _, _, terminated, truncated, _ = self.step(((troop_to_move.row, troop_to_move.col), (row, col)))
                            else:
                                #Clear the highlight_moves off the board
                                for tile_row in range(self.row_count):
                                    for tile_col in range(self.col_count):
                                        self.terrain[tile_row, tile_col].highlight_move = False
                                        self.terrain[tile_row, tile_col].highlight_attack = False
                            troop_to_move = None

                        #if friendly troop with moves
                        elif tile.troop and tile.troop.moves > 0 and tile.troop.player_id == self.player.id:
                            troop_to_move = tile.troop
                            #highlight_move the moves of the troop
                            obs = self.terrain.get_reachable_pos(troop_to_move)
                            #Could vectorize these for loops using numpy vector operations
                            for tile_row in range(self.row_count):
                                for tile_col in range(self.col_count):
                                    if obs[tile_row, tile_col] > 0:
                                        self.terrain[tile_row, tile_col].highlight_move = True
                                        self.terrain[tile_row, tile_col].highlight_attack = False
                                    elif obs[tile_row, tile_col] == -2:
                                        self.terrain[tile_row, tile_col].highlight_attack = True
                                        self.terrain[tile_row, tile_col].highlight_move = False
                        if terminated or truncated:
                            self.reset()
                            terminated, truncated = False, False
                        else:
                            self._render_frame()


            






