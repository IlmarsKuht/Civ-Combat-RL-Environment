import pygame
from pygame.math import Vector2
from abc import ABC, abstractmethod
import random
import math
from collections import deque
import numpy as np

from options import Colors, FortifiedBonus, PLAYER_COLOR, BOT_COLORS, MARGIN, Rewards, \
                    DIRECTIONS_ODD, DIRECTIONS_EVEN, HEX_SIZE, worldToScreen, \
                    draw_centered

class Player:
    __id_counter = 0
    def __init__(self, name):
        self.id = Player.__id_counter
        Player.__id_counter += 1
        self.name = name
        self.troops = []
        self.buildings = []

class Entity(ABC):
    BASE_WARRIOR_IMAGE = pygame.image.load('./images/warrior.png')
    BASE_ARCHER_IMAGE = pygame.image.load('./images/archer.png')
    BASE_CITY_CENTER_IMAGE = pygame.image.load('./images/city_center.png')
    WARRIOR_IMAGE = pygame.transform.scale(BASE_WARRIOR_IMAGE, (HEX_SIZE / 2, HEX_SIZE / 2))
    ARCHER_IMAGE = pygame.transform.scale(BASE_ARCHER_IMAGE, (HEX_SIZE / 2, HEX_SIZE / 2))
    CITY_CENTER_IMAGE = pygame.transform.scale(BASE_CITY_CENTER_IMAGE, (HEX_SIZE / 2, HEX_SIZE / 2))

    def update_images(self, scale):
        new_size = HEX_SIZE / 2 * scale.x
        Entity.WARRIOR_IMAGE = pygame.transform.scale(Entity.BASE_WARRIOR_IMAGE, (new_size, new_size))
        Entity.ARCHER_IMAGE = pygame.transform.scale(Entity.BASE_ARCHER_IMAGE, (new_size, new_size))
        Entity.CITY_CENTER_IMAGE = pygame.transform.scale(Entity.BASE_CITY_CENTER_IMAGE, (new_size, new_size))

    def __init__(self, health, max_health, power, player_id, row, col, hp_power_loss, attack_range):
        self.health = health
        self.max_health = max_health
        self.power = power
        self.player_id = player_id
        self.row = row
        self.col = col
        self.hp_power_loss = hp_power_loss
        self.attack_range = attack_range
    def draw(self, window, player_id, image, offset, scale):
        x = (HEX_SIZE * self.col + (HEX_SIZE / 2 * (self.row % 2))) + HEX_SIZE / 2 + MARGIN
        y = (HEX_SIZE * 0.75 * self.row) + HEX_SIZE / 2 + MARGIN

        pos = worldToScreen(Vector2(x, y), offset, scale)

        draw_centered(window, image, pos)

        # Calculate the circle's position and size for the camera
        circle_radius = HEX_SIZE / 15 * scale.x
        circle_width = int(HEX_SIZE / 25 * scale.x)

        # Draw the circle with the adjusted center and radius
        color = BOT_COLORS[self.player_id % len(BOT_COLORS)]
        pygame.draw.circle(window, color, pos, circle_radius)

        self._draw_attributes(window, x, y, offset, scale)
       
        if self.player_id == player_id:
            pygame.draw.circle(window, PLAYER_COLOR, pos, circle_radius, circle_width)

    @abstractmethod
    def kill(self, tiles):
        """
        What happens when this Entity is killed, rewards and other things.
        """

    @abstractmethod
    def remove_from_tiles(self, tiles):
        """
        removes the entity from tiles array
        """

    @abstractmethod
    def add_to_tiles(self, tiles):
        """
        adds the entity to tiles array
        """
    
    def _draw_attributes(self, window, x, y, offset, scale):
        health_bar_width = HEX_SIZE / 2
        health = self.health / self.max_health
        green_width = int(health * health_bar_width * scale.x) 
        red_width = int((1 - health) * health_bar_width * scale.x)
        health_bar_x = int(x - health_bar_width / 2)
        health_bar_y = int(y + HEX_SIZE / 4 )
        health_bar_height = HEX_SIZE / 25 * scale.x
        health_color = Colors.HEALTH.value

        pos = worldToScreen(Vector2(health_bar_x, health_bar_y), offset, scale)

        pygame.draw.rect(window, health_color, (pos.x, pos.y, green_width, health_bar_height))  # Green part
        pygame.draw.rect(window, Colors.HEALTH_LOST.value, (pos.x + green_width, pos.y, red_width, health_bar_height))  # Red part

        # Power number
        font = pygame.font.Font(None, int(HEX_SIZE/5 * scale.x))  
        power_text = font.render(str(self.power), True, Colors.BLACK.value) 
        power_y = y-HEX_SIZE/3
        power_pos = worldToScreen(Vector2(x,power_y), offset, scale)
        draw_centered(window, power_text, power_pos)



class Troop(Entity, ABC):

    def __init__(self, moves, max_moves, health, max_health, power, player_id, row, col, fortified, hp_power_loss, attack_range):
        super().__init__(health, max_health, power, player_id, row, col, hp_power_loss, attack_range)
        self.moves = moves
        self.max_moves = max_moves
        self.fortified = fortified

    def _draw_attributes(self, window, x, y, offset, scale):

        health_bar_width = HEX_SIZE / 2
        health = self.health / self.max_health
        green_width = int(health * health_bar_width * scale.x) 
        red_width = int((1 - health) * health_bar_width * scale.x)
        health_bar_x = int(x - health_bar_width / 2)
        health_bar_y = int(y + HEX_SIZE / 4 )
        health_bar_height = HEX_SIZE / 25 * scale.x

        # Determine health bar color based on fortification
        health_color = Colors.HEALTH.value
        if self.fortified == FortifiedBonus.FIRST:
            health_color = Colors.FORTIFIED.value
        elif self.fortified == FortifiedBonus.SECOND:
            health_color = Colors.EXTRA_FORTIFIED.value

        pos = worldToScreen(Vector2(health_bar_x, health_bar_y), offset, scale)

        pygame.draw.rect(window, health_color, (pos.x, pos.y, green_width, health_bar_height))  # Green part
        pygame.draw.rect(window, Colors.HEALTH_LOST.value, (pos.x + green_width, pos.y, red_width, health_bar_height))  # Red part

        # Movement points
        font = pygame.font.Font(None, int(HEX_SIZE/5*scale.x))
        movement_text = font.render(f"{self.moves}/{self.max_moves}", True, Colors.BLACK.value)
        movement_x = health_bar_x+health_bar_width/2
        movement_y = health_bar_y+HEX_SIZE/30
        move_pos = worldToScreen(Vector2(movement_x, movement_y), offset, scale)
        draw_centered(window, movement_text, move_pos)

        # Power number
        font = pygame.font.Font(None, int(HEX_SIZE/5 * scale.x))  
        power_text = font.render(str(self.power), True, Colors.BLACK.value) 
        power_y = y-HEX_SIZE/3
        power_pos = worldToScreen(Vector2(x,power_y), offset, scale)
        draw_centered(window, power_text, power_pos)

    def fortify(self):
        if self.moves == self.max_moves:
            self.health = min(self.health + 10, self.max_health)
            if self.fortified == FortifiedBonus.NONE:
                self.fortified = FortifiedBonus.FIRST
                self.power += FortifiedBonus.FIRST.value
            elif self.fortified == FortifiedBonus.FIRST:
                self.fortified = FortifiedBonus.SECOND
                self.power -= FortifiedBonus.FIRST.value
                self.power += FortifiedBonus.SECOND.value
        #only update moves at the end, else will mess up the calculation above
        self.moves = 0
        return Rewards.DEFAULT.value

    def move(self, new_row, new_col, moves, tiles):
        self._remove_fortify_bonus()
        self.remove_from_tiles(tiles)
        self.add_to_tiles(tiles, new_row, new_col)

        self.moves -= moves
        self.row = new_row
        self.col = new_col        
        return Rewards.DEFAULT.value
    
    def remove_from_tiles(self, tiles):
        tiles[self.row, self.col].troop = None
    
    def add_to_tiles(self, tiles, row, col):
        tiles[row, col].troop = self

    def kill(self, tiles):
        self.health = 0
        self.remove_from_tiles(tiles)
        return Rewards.KILL_TROOP.value

    @abstractmethod
    def attack(self, defender, tiles):
        """
        Implement seperate attack method for each Troop type to deal the damage
        """
    #can pass through team and enemy troops
    def get_reachable_pos(self, tiles):
        observation = np.full((len(tiles), len(tiles[0])), -1.0)
        queue = deque([(self.row, self.col, 0, 0)])
        max_moves = self.moves

        def is_valid_tile(x, y):
            return 0 <= x < len(tiles) and 0 <= y < len(tiles[0])

        while queue:
            curr_x, curr_y, moves, attack_moves = queue.popleft()

            curr_tile = tiles[curr_x, curr_y]
            curr_obs = observation[curr_x, curr_y]

            if (curr_obs >= 0 and curr_obs < moves) or curr_obs == -2 or curr_obs == 0 or curr_tile.obstacle:
                continue

            tile_troop = curr_tile.troop
            tile_building = curr_tile.building

            if tile_troop and tile_troop.player_id == self.player_id and (curr_x, curr_y) != (self.row, self.col):
                observation[curr_x, curr_y] = 0
                continue
            elif (tile_troop and tile_troop.player_id != self.player_id) or (tile_building and tile_building.player_id != self.player_id):
                observation[curr_x, curr_y] = -2 if attack_moves <= self.attack_range else 0
                continue
            elif moves <= self.moves:
                observation[curr_x, curr_y] = moves

            if moves < max_moves or attack_moves < self.attack_range:
                directions = DIRECTIONS_EVEN if curr_x % 2 == 0 else DIRECTIONS_ODD
                for dx, dy in directions:
                    nx, ny = curr_x + dx, curr_y + dy
                    if is_valid_tile(nx, ny):
                        queue.append((nx, ny, moves + tiles[nx, ny].move_cost, attack_moves+1))

        observation[self.row, self.col] = self.max_moves
        return observation
    
    def _remove_fortify_bonus(self):
        self.power -= self.fortified.value
        self.fortified = FortifiedBonus.NONE

    def _update_hp_power_loss(self):
        self.power += self.hp_power_loss
        self.hp_power_loss = round(10 - (self.health/10))
        self.power -= self.hp_power_loss

    @abstractmethod
    def _handle_attack_result(self, defender, tiles):
        """
        Implement method that handles the result of the fight after each troop has taken damage"""


class Warrior(Troop):
    def __init__(self, moves, max_moves, health, max_health, power, player_id, row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0, attack_range=1):
        super().__init__(moves, max_moves, health, max_health, power, player_id, row, col, fortified, hp_power_loss, attack_range)

    def draw(self, window, player_id, offset, scale):
        self.update_images(scale)
        super().draw(window, player_id, Entity.WARRIOR_IMAGE, offset, scale)

    def attack(self, defender, tiles):
        self.moves = 0
        self._remove_fortify_bonus()
       
        def_power = defender.power 
        attack_power = self.power

        #formula: Damage(HP)=30*e^{0.04*StrengthDifference}*randomBetween(0.8-1.2)}
        rand = random.uniform(0.8, 1.2)
        damage_to_defender = 30*math.exp(0.04 * (attack_power-def_power)) * rand
        damage_to_attacker = 30*math.exp(0.04 * (def_power-attack_power)) * rand
        defender.health -= damage_to_defender
        self.health -= damage_to_attacker
        
        self._update_hp_power_loss()
        if isinstance(defender, Troop):
            defender._update_hp_power_loss()

        reward = self._handle_attack_result(defender, tiles)

        return reward
    
    def _handle_attack_result(self, defender, tiles):
        reward = Rewards.ATTACK.value

        # Determine the unit to kill and potentially revive.
        if defender.health <= 0 or self.health <= 0:
            if defender.health <= 0 and self.health <= 0:
                # Both units are dead, revive the one with the most health.
                survivor, victim = (self, defender) if self.health > defender.health else (defender, self)
                survivor.health = 1
            else:
                # Only one unit is dead.
                survivor, victim = (self, defender) if defender.health <= 0 else (defender, self)

            kill_reward = victim.kill(tiles)

            # Handle rewards and movement if applicable.
            reward += kill_reward if survivor == self else -kill_reward
            if survivor == self:
                self.move(defender.row, defender.col, 0, tiles)

        return reward


class Archer(Troop):
    def __init__(self, moves, max_moves, health, max_health, power, player_id, row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0, attack_range=2):
        super().__init__(moves, max_moves, health, max_health, power, player_id, row, col, fortified, hp_power_loss, attack_range)

    def draw(self, window, player_id, offset, scale):
        self.update_images(scale)
        super().draw(window, player_id, Entity.ARCHER_IMAGE, offset, scale)

    def attack(self, defender, tiles):
        self.moves = 0
        self._remove_fortify_bonus()
        #get the defending and attacking troops power
        def_power = defender.power 
        attack_power = self.power

        #formula: Damage(HP)=30*e^{0.04*StrengthDifference}*randomBetween(0.8-1.2)}
        rand = random.uniform(0.8, 1.2)
        damage_to_defender = 30*math.exp(0.04 * (attack_power-def_power)) * rand

        defender.health -= damage_to_defender
        
        if isinstance(defender, Troop):
            defender._update_hp_power_loss()

        reward = self._handle_attack_result(defender, tiles)

        return reward
    
    def _handle_attack_result(self, defender, tiles):
        reward = Rewards.ATTACK.value

        if defender.health <= 0:
            reward += defender.kill(tiles)

        return reward

class Center(Entity):
    def __init__(self, health, max_health, power, player_id, row, col, hp_power_loss=0, attack_range=0):
        super().__init__(health, max_health, power, player_id, row, col, hp_power_loss, attack_range)

    def draw(self, window, player_id, offset, scale):
        self.update_images(scale)
        super().draw(window, player_id, Entity.CITY_CENTER_IMAGE, offset, scale)

    def kill(self, tiles):
        self.health = 0
        self.remove_from_tiles(tiles)
        return Rewards.KILL_CITY.value
    
    def remove_from_tiles(self, tiles):
        tiles[self.row, self.col].building = None

    def add_to_tiles(self, tiles, row, col):
        tiles[row, col].building = self