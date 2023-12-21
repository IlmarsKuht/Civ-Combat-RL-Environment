import pygame
from abc import ABC, abstractmethod
import random
import math

from options import HEX_SIZE, Colors, FortifiedBonus, PLAYER_COLOR, BOT_COLORS, MARGIN, Rewards

WARRIOR_IMAGE = pygame.image.load('./images/warrior.png')
WARRIOR_IMAGE = pygame.transform.scale(WARRIOR_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

ARCHER_IMAGE = pygame.image.load('./images/archer.png')
ARCHER_IMAGE = pygame.transform.scale(ARCHER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

CITY_CENTER_IMAGE = pygame.image.load('./images/city_center.png')
CITY_CENTER_IMAGE = pygame.transform.scale(CITY_CENTER_IMAGE, (HEX_SIZE/2, HEX_SIZE/2))  

def _draw_centered(window, image, x, y):
    rect = image.get_rect(center=(x, y))
    window.blit(image, rect)

class Player:
    __id_counter = 0
    def __init__(self, name):
        self.id = Player.__id_counter
        Player.__id_counter += 1
        self.name = name
        self.troops = []
        self.buildings = []

class Entity(ABC):
    def __init__(self, health, max_health, power, player_id, row, col, image, hp_power_loss=0):
        self.health = health
        self.max_health = max_health
        self.power = power
        self.player_id = player_id
        self.row = row
        self.col = col
        self.image = image
        self.hp_power_loss = hp_power_loss
    
    def draw(self, window, player_id):
        #Center coordinates of the middle of the tile
        self.x = (HEX_SIZE * self.col + (HEX_SIZE/2 * (self.row % 2)))+HEX_SIZE/2+MARGIN
        self.y = (HEX_SIZE * 0.75 * self.row)+HEX_SIZE/2+MARGIN

        color = BOT_COLORS[self.player_id % len(BOT_COLORS)]
        _draw_centered(window, self.image, self.x, self.y)
        #tag the team color
        pygame.draw.circle(window, color, (self.x, self.y), HEX_SIZE/15)
        self._draw_attributes(window)
        #if player then higlight it (draw outline)
        if self.player_id == player_id:
            pygame.draw.circle(window, PLAYER_COLOR, (self.x, self.y), HEX_SIZE/15, 2)

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
    
    def _draw_attributes(self, window):
        # Health Bar
        health_bar_width = HEX_SIZE/2
        health = self.health / self.max_health  # Health as a percentage
        green_width = int(health * health_bar_width)
        red_width = int((1 - health) * health_bar_width)
        health_bar_x = int(self.x-health_bar_width/2)
        health_bar_y = int(self.y+HEX_SIZE/4)
        health_bar_height = HEX_SIZE/25
        #Change Health color depending on fortification
        health_color = Colors.HEALTH.value

        pygame.draw.rect(window, health_color, (health_bar_x, health_bar_y, green_width, health_bar_height))  # Green part
        pygame.draw.rect(window, Colors.HEALTH_LOST.value, (health_bar_x + green_width, health_bar_y, red_width, health_bar_height))  # Red part

        # Power number
        font = pygame.font.Font(None, int(HEX_SIZE/5))  
        power_text = font.render(str(self.power), True, Colors.BLACK.value) 
        power_y = self.y-HEX_SIZE/3
        _draw_centered(window, power_text, self.x, power_y)



class Troop(Entity, ABC):
    def __init__(self, moves, max_moves, health, max_health, power, player_id, row, col, image, fortified, hp_power_loss=0):
        super().__init__(health, max_health, power, player_id, row, col, image, hp_power_loss)
        self.moves = moves
        self.max_moves = max_moves
        self.fortified = fortified

    #Troop overrides Entities _draw_attributes
    def _draw_attributes(self, window):
        # Health Bar
        health_bar_width = HEX_SIZE/2
        health = self.health / self.max_health  # Health as a percentage
        green_width = int(health * health_bar_width)
        red_width = int((1 - health) * health_bar_width)
        health_bar_x = int(self.x-health_bar_width/2)
        health_bar_y = int(self.y+HEX_SIZE/4)
        health_bar_height = HEX_SIZE/25
        #Change Health color depending on fortification
        health_color = Colors.HEALTH.value
        if self.fortified == FortifiedBonus.FIRST:
            health_color = Colors.FORTIFIED.value
        elif self.fortified == FortifiedBonus.SECOND:
            health_color = Colors.EXTRA_FORTIFIED.value
        pygame.draw.rect(window, health_color, (health_bar_x, health_bar_y, green_width, health_bar_height))  # Green part
        pygame.draw.rect(window, Colors.HEALTH_LOST.value, (health_bar_x + green_width, health_bar_y, red_width, health_bar_height))  # Red part

        # Movement points
        font = pygame.font.Font(None, int(HEX_SIZE/5))
        movement_text = font.render(f"{self.moves}/{self.max_moves}", True, Colors.BLACK.value)
        movement_x = health_bar_x+health_bar_width/2
        movement_y = health_bar_y+HEX_SIZE/30
        _draw_centered(window, movement_text, movement_x, movement_y)

        # Power number
        font = pygame.font.Font(None, int(HEX_SIZE/5))  
        power_text = font.render(str(self.power), True, Colors.BLACK.value) 
        power_y = self.y-HEX_SIZE/3
        _draw_centered(window, power_text, self.x, power_y)

    def fortify(self):
        #Fortification bonus calculations
        if self.moves == self.max_moves:
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
    def __init__(self, moves, max_moves, health, max_health, power, player_id, row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0):
        super().__init__(moves, max_moves, health, max_health, power, player_id, row, col, WARRIOR_IMAGE, fortified, hp_power_loss)

    def attack(self, defender, tiles):
        self.moves = 0
        self._remove_fortify_bonus()
        #get the defending and attacking troops power
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
    def __init__(self, range, moves, max_moves, health, max_health, power, player_id, row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0):
        super().__init__(moves, max_moves, health, max_health, power, player_id, row, col, ARCHER_IMAGE, fortified, hp_power_loss)
        self.range = range

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
    def __init__(self, health, max_health, power, player_id, row, col, hp_power_loss=0):
        super().__init__(health, max_health, power, player_id, row, col, CITY_CENTER_IMAGE, hp_power_loss)

    def kill(self, tiles):
        self.health = 0
        self.remove_from_tiles(tiles)
        return Rewards.KILL_CITY.value
    
    def remove_from_tiles(self, tiles):
        tiles[self.row, self.col].building = None

    def add_to_tiles(self, tiles, row, col):
        tiles[row, col].building = self