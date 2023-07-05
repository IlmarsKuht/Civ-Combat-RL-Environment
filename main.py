import pygame

import gymnasium as gym

import numpy as np

import random

from entities import Terrain, Troop, Building, Player
from options import BuildingType, TroopType, TileType, CnnChannels

#pygame grid
COLUMNS, ROWS = 6, 6
HEX_SIZE = 60
MARGIN = 70

#pygame window
WIDTH, HEIGHT = 800, 700

#might break if rows and columns are not even or might not, who knows :)

class Civ6CombatEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    #layer can try rgb_array rendering for CNNs.
    metadata = {"render_modes": ["human"], "render_fps": 5}

    def __init__(self, render_mode=None):
        super().__init__()

        #Game variables
        self.ai_turn = False
        self.unit_chosen = None

        #pygame variables
        self.window = None
        self.clock = None

        #FIGURE OUT WHAT ACTION SPACES TO USE
        self.action_space = gym.spaces.MultiDiscrete([ROWS, COLUMNS])
        
        #Setting up observation space
        self.observation_space = gym.spaces.Box(
            low=-1, 
            high=1,  
            shape=(COLUMNS, ROWS, len(CnnChannels)), 
            dtype=np.float32 
        )
        
        #check if render_mode is valid
        assert render_mode is None or render_mode in self.metadata["render_modes"], f"Invalid render mode, available render modes are {self.metadata['render_modes']}"
        self.render_mode = render_mode

    #Translate game state to observation
    def _get_obs(self):
        observation, troop_chosen = self.terrain.get_obs(self.player)
        self.troop_chosen = troop_chosen
        if troop_chosen is None:
            self.ai_turn = True
        
        #IF UNIT CHOSEN IS FALSE THEN THE AI SHOULD NOW MOVE 
        return observation
    
    def _get_info(self):
        #additional information not returned as observation
        return {}

    def step(self, action):
        #do the action
        reward = 0
        if self.troop_chosen:
            reward += self.terrain.action(action, self.troop_chosen)
            self._clean_up(self.player)
            self._clean_up(self.bot)
        else:
            print("No troop chosen")
        #check if the game has ended or truncated
        terminated, truncated = False, False     

        #get the observations and additonal info
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        #do AI move and render again
        if self.ai_turn:
            action, troop = self._rand_action(self.bot)
            if action is not None and troop is not None:
                reward -= self.terrain.action(action, troop)

            self._reset_moves(self.player)
            self._reset_moves(self.bot)
            self._clean_up(self.player)
            self._clean_up(self.bot)
            observation = self._get_obs()
            info = self._get_info()

            if self.render_mode == "human":
                self._render_frame()


        return observation, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        #reset the game
        if self.render_mode == "human":
            self.terrain = Terrain(ROWS, COLUMNS, True, HEX_SIZE, MARGIN)
        else:
            self.terrain = Terrain(ROWS, COLUMNS)

        #initalize the players
        self.player = Player("JiaoJiao")
        self.bot = Player("Ilmars")
        

        #Set the locations of cities, troops allied and enemy with self.np_random
        
        self._create_building(self.player, 200, 50, BuildingType.CENTER, 0, 1)
        self._create_building(self.bot, 200, 50, BuildingType.CENTER, 4, 1)

        self._create_troop(self.player, 100, 30, 2, 2, TroopType.WARRIOR, 0, 2)
        self._create_troop(self.bot, 100, 25, 2, 2, TroopType.WARRIOR, 4, 2)
        
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        return observation, info
    
    def _render_frame(self):
        #Initialize window and clock
        if self.window == None and self.clock == None:
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()


        self.window.fill((0, 0, 0))  # clear the screen before drawing
        self.terrain.draw(self.window) 

        pygame.event.pump()
        pygame.display.update()  
        self.clock.tick(self.metadata["render_fps"])
        

    def close(self):
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
    
    def _create_troop(self, player : Player, health, power, moves, max_moves, type : TroopType, row, col):
        self.terrain[row][col].troop = Troop(health, power, moves, max_moves, player.id, type, row, col)
        player.troops.append(self.terrain[row][col].troop)

    def _create_building(self, player : Player, health, power, type : BuildingType, row, col):
        self.terrain[row][col].building = Building(health, power, player.id, type, row, col)
        player.buildings.append(self.terrain[row][col].building)

    def _rand_action(self, player : Player):
        if len(player.troops) != 0:
            troop = random.choice(player.troops)
        else:
            return None, None
        possible_moves = self.terrain.get_reachable_pos(troop)

        # Get the coordinates of all reachable positions
        reachable_positions = np.argwhere(possible_moves == 1)

        if len(reachable_positions) == 0:
            # No reachable positions available
            return None

        # Select a random position from the reachable positions
        rand_pos = random.choice(reachable_positions)

        return rand_pos, troop  # rand_pos is a numpy array [row, col]
    
    
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


def main():
    from stable_baselines3.common.env_checker import check_env
    env = Civ6CombatEnv(render_mode="human")
    #check_env(env)
    env.reset()
    while True:
        env.step(env.action_space.sample())
         


if __name__ == "__main__":
    main()






