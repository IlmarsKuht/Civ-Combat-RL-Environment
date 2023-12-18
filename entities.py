import pygame

from options import HEX_SIZE, Colors, FortifiedBonus, PLAYER_COLOR, BOT_COLORS, MARGIN

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

class Entity:
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



class Troop(Entity):
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


class Warrior(Troop):
    def __init__(self, moves, max_moves, health, max_health, power, player_id, row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0):
        super().__init__(moves, max_moves, health, max_health, power, player_id, row, col, WARRIOR_IMAGE, fortified, hp_power_loss)


class Archer(Troop):
    def __init__(self, range, moves, max_moves, health, max_health, power, player_id, row, col, fortified : FortifiedBonus=FortifiedBonus.NONE, hp_power_loss=0):
        super().__init__(moves, max_moves, health, max_health, power, player_id, row, col, ARCHER_IMAGE, fortified, hp_power_loss)
        self.range = range

class Center(Entity):
    def __init__(self, health, max_health, power, player_id, row, col, hp_power_loss=0):
        super().__init__(health, max_health, power, player_id, row, col, CITY_CENTER_IMAGE, hp_power_loss)




