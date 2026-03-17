# data/moves.py
"""All move definitions. MOVES dict is keyed by move ID."""
from models.monster import Move

MOVES: dict[int, Move] = {
    1:  Move(1,  "たいあたり",   "normal",   "physical", 40,  100),
    2:  Move(2,  "ひっかく",     "normal",   "physical", 40,  100),
    3:  Move(3,  "ひのこ",       "fire",     "special",  40,  100),
    4:  Move(4,  "みずでっぽう", "water",    "special",  40,  100),
    5:  Move(5,  "つるのムチ",   "grass",    "physical", 45,  100),
    6:  Move(6,  "かみつく",     "dark",     "physical", 60,  100),
    7:  Move(7,  "いわおとし",   "rock",     "physical", 50,   90),
    8:  Move(8,  "でんきショック","electric", "special",  40,  100),
    9:  Move(9,  "たたく",       "normal",   "physical", 40,  100),
    10: Move(10, "つばさでうつ", "flying",   "physical", 60,  100),
    11: Move(11, "どろかけ",     "ground",   "special",  55,   95),
    12: Move(12, "かぜおこし",   "flying",   "special",  40,  100),
    13: Move(13, "シャドーボール","ghost",    "special",  80,  100),
    14: Move(14, "こおりのつぶて","ice",      "physical", 40,  100),
    15: Move(15, "メタルクロー", "steel",    "physical", 50,   95),
    16: Move(16, "かえんほうしゃ","fire",     "special",  90,  100),
    17: Move(17, "なみのり",     "water",    "special",  90,  100),
    18: Move(18, "ソーラービーム","grass",    "special", 120,  100),
    19: Move(19, "10まんボルト", "electric", "special",  90,  100),
    20: Move(20, "じしん",       "ground",   "physical",100,  100),
}
