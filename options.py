from enum import Enum

class BuildingType(Enum):
    CENTER = "city_center"
    ENCAMPMENT = "encampment"

class TroopType(Enum):
    WARRIOR = "warrior"
    ARCHER = "archer"

class TileType(Enum):
    MOUNTAIN = "mountain"
    HILL = "hill"
    PLAINS = "plains"
    OCEAN = "ocean"

PLAYER_COLORS = [(255,0,0), (255,0,255), (0,0,255), (0, 255, 255)]

class CnnChannels(Enum):
    # 1 is True | 0 is False | -1 is no value
    IS_ENEMY_BUILDING = 0
    IS_ENEMY_TROOP = 1
    TROOP_HEALTH = 2
    TROOP_POWER = 3
    BUILDING_HEALTH = 4
    BUILDING_POWER = 5
    CAN_MOVE = 6

class Rewards(Enum):
    KILL_TROOP = 1
    LOSE_TROOP = -1
    KILL_CITY = 5
    LOSE_CITY = -5
    ATTACK = 0.6
    DEFAULT = 0
    INVALID = -5

DIRECTIONS_ODD = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (0, -1)]
DIRECTIONS_EVEN = [(-1, -1), (-1, 0), (0, 1), (1, 0), (1, -1), (0, -1)]

ROWS, COLUMNS = 6, 6

HEX_SIZE = 100


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