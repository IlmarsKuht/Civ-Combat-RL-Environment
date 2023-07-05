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
    HEALTH = 2
    POWER = 3
    CAN_MOVE = 4
    UNIT_TO_MOVE = 5
    