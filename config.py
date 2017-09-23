from os import path
import json

config_file = path.join(path.dirname(__file__), 'config.json')
with open(config_file, 'r') as config_json:
    config = json.load(config_json)
