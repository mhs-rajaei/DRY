import os
from DRY import ConfigMerger
import logging
logger = logging.getLogger("DRY")  # DRY: Don’t Repeat Yourself (Merge, Extend and Override your config file)

from utils.box import load_from_yaml, load_from_json, to_json, to_yaml
from utils.util import get_recursively
from pprint import pprint


def main():
    # For usage of DRY go to config.yaml.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Loading config in YAML format
    # config_dict = load_from_yaml(filename=os.path.join(BASE_DIR, 'config/config.yaml'))
    config_dict = load_from_yaml(filename=r'F:\Downloads\Dropbox\Work\PycharmProjects\PatchMan37\config\patchman37.yaml')
    # YAML to JSON
    # to_json(config_dict, filename=os.path.join(BASE_DIR, 'config/config.json'))

    key_counter = 0
    for key, value in get_recursively(config_dict):
        # pprint([key, value])
        key_counter += 1

    print(f"\nNumber of Keys 'config_dict' is: {key_counter}\n {'-'*100}")

    # .............................................................................
    # Usage of DRY
    merger_obj = ConfigMerger(config_dict, merge_at_init=True)
    if merger_obj.return_value == -1:
        logger.error('Error in Config Merger')
        return -1

    # Get merged dict as result
    merged_config_dict = merger_obj.config_dict

    key_counter = 0
    for key, value in get_recursively(merged_config_dict):
        # pprint([key, value])
        key_counter += 1

    print(f"\nNumber of Keys 'merged_config_dict' in YAML format is: {key_counter}\n {'-'*100}")

    # ----------------------------------------------------------------------------------

    # Loading config in JSON format
    config_dict = load_from_json(filename=os.path.join(BASE_DIR, 'config/config.json'))

    # .............................................................................
    # Usage of DRY
    merger_obj = ConfigMerger(config_dict, merge_at_init=True)
    if merger_obj.return_value == -1:
        logger.error('Error in Config Merger')
        return -1

    # Get merged dict as result
    merged_config_dict = merger_obj.config_dict

    key_counter = 0
    for key, value in get_recursively(merged_config_dict):
        # pprint([key, value])
        key_counter += 1

    print(f"\nNumber of Keys 'merged_config_dict' in JSON format is: {key_counter}\n {'-'*100}")


if __name__ == "__main__":
    main()
