from enum import Enum

class TileType(Enum):
    SEA = 1
    PLAINS = 2
    FOREST = 3
    HILLS = 4
    MOUNTAIN = 5

PLAYER_COLOR = (255, 215, 0)
BOT_COLORS = ((255,0,0), (255,0,255), (0,0,255), (0, 255, 255))

class CnnChannels(Enum):
    # 1 is True | 0 is False | -1 is no value
    IS_ENEMY_BUILDING = 0 # bool values
    IS_ENEMY_TROOP = 1 # bool values
    TROOP_HEALTH = 2 # real values
    TROOP_POWER = 3 # real values
    BUILDING_HEALTH = 4 # real values
    BUILDING_POWER = 5 # real values
    CAN_MOVE = 6 # bool values

class Rewards(Enum):
    KILL_TROOP = 5
    KILL_CITY = 25
    ATTACK = 3
    DEFAULT = 0
    INVALID = -25
    WIN_GAME = 100

DIRECTIONS_ODD = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (0, -1))
DIRECTIONS_EVEN = ((-1, -1), (-1, 0), (0, 1), (1, 0), (1, -1), (0, -1))

HEX_SIZE = 120

MARGIN = 30

#pygame window
WIDTH, HEIGHT = 1100, 1000


#fortified bonus is given when a troop has fortified and not used any movement
# Each turn of max movement and fortified increases starting from first to second
#if moves and fortifies None bonus (doesn't matter now you can't move without using all movement)
class FortifiedBonus(Enum):
    NONE = 0
    FIRST = 3
    SECOND = 6

class Colors(Enum):
    HEALTH = (0, 200, 0) #Green
    HEALTH_LOST = (200, 0, 0)
    FORTIFIED = (128, 234, 255) #Light blue
    EXTRA_FORTIFIED = (0, 60, 179) #Dark blue
    WHITE = (220, 220, 220)
    BLACK = (20, 20, 20)