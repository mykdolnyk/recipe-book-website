from json import load
from config import BASE_DIR


with open(BASE_DIR / 'backend/utils/name_generation/recipe_mix_names.json', 'r') as f:
    name_data = load(fp=f)

nouns = name_data['nouns']
adjectives = name_data['adjectives']
