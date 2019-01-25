"""
DRY: Don’t Repeat Yourself (Merge, Extend and Override your config file)
"""
import os
import logging
from config.configure import setup_logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger = setup_logging(default_path=os.path.join(BASE_DIR, 'config/logging.yaml'))
if logger is None:
    logger = logging.getLogger("DRY")  # DRY: Don’t Repeat Yourself (Merge, Extend and Override your config file)
    logger.info("Logging module configured by yaml configuration file")

from collections import Counter
from utils.util import find_with_regex
from melddict import MeldDict
import flatdict
import copy
from pprint import pprint


class ConfigMerger:
    def __init__(self, config_dict, merge_at_init, re_anchor=None, re_name=None, anchor_start_pattern='(&',
                 pointer_pattern='->', delimiter=':'):
        """
        :param config_dict: input dictionary for do merging.

        :param re_anchor: regex for extracting anchor from dictionary key.
                          this regex do something like: 'key_name(&anchor_name)' -> '(&anchor_name)')

        :param re_name: regex for extracting name of anchor(s) or pointer(s).

        :param anchor_start_pattern: pattern of starting anchor for splitting key by that. by '(&' as anchor pattern and doing split,
         we have: key_name(&anchor_name)' -> ['key_name' , 'anchor_name']

        :param pointer_pattern: string pattern for find pointers in dictionary keys. this pattern must never be used as name of keys that we
          don't want to be a pointer. just use this pattern in where that you wanna have a pointer.
          for the duplicate name of this pattern in the same key, you can add any string to this pattern.
             ->1: pointer1
             ->2: pointer2
           we do something like this:
               if pointer_pattern in the key:
                   add the value of this key to pointers.

        :param delimiter: separator in flatten dictionary. the default is ':'

        Notes:
            Don't use a pointer as a list value(element), because we don't merge this pointer.

             Priority in multiple pointers is: from newest to oldest, As Example:
                        key_name(&anchor_1)
                        key_name(&anchor_2)
                        key_name(&anchor_3)
             For this example we fist of all merge 'anchor_3' then 'anchor_2' and finally 'anchor_1'.
        """
        try:
            self.config_dict = copy.deepcopy(config_dict)

            if not re_anchor:
                self.re_anchor = r'\([\&][a-zA-Z\._0-9]{1,}\)'
            else:
                self.re_anchor = re_anchor

            if not re_name:
                self.re_name = r'[a-zA-Z\._0-9]{1,}'
            else:
                self.re_name = re_name
            self.anchor_start_pattern = anchor_start_pattern
            self.pointer_pattern = pointer_pattern

            self.flatten_config = flatdict.FlatDict(self.config_dict)

            self.all_occurrence_of_anchors = []
            for key in self.flatten_config.keys():
                if self.anchor_start_pattern in key:
                    self.all_occurrence_of_anchors.append(key)

            self.all_occurrence_of_pointers = []
            for key in self.flatten_config.keys():
                if self.pointer_pattern in key:
                    self.all_occurrence_of_pointers.append(key)

            self.valid_anchor_names = []
            self.valid_anchors = dict()

            self.valid_pointers = dict()

            self.return_value = 0
            self.recursive_dict_return_value = 0

            self.delimiter = delimiter
            # Setting delimiter
            try:
                if self.delimiter != ':':
                    self.flatten_config.set_delimiter(self.delimiter)
                    logger.info(f"Flatten dictionary delimiter set to: {self.delimiter}")
            except Exception as err:
                logger.error(err)

            if merge_at_init:
                self.merge()

        except Exception as err:
            logger.error(err, exc_info=True)

    def merge(self):
        # TODO: Check for same/exact name in anchors key name: 'key_name' and 'key_name(&anchor_name)'. Name of keys without anchor_start_pattern must be diffrent.
        # Checking Anchors
        _stat = self.anchor_validation()
        if _stat == -1:
            self.return_value = -1
            logger.error('Error in Config Merger')
            return -1
        # Checking Pointers
        _stat = self.pointers_validation()
        if _stat == -1:
            self.return_value = -1
            logger.error('Error in Config Merger')
            return -1
        # Merging...
        _stat = self.merge_pointers_with_anchors()
        if _stat == -1:
            self.return_value = -1
            logger.error('Error in Config Merger')
            return -1

        self.return_value = 1
        return 1

    def anchor_validation(self):
        try:
            # Checking for anchor occurrence and position and number of anchors in each key
            for key in self.all_occurrence_of_anchors:
                _key = key.split(self.delimiter)
                parent_idx = 0
                for k in _key:
                    _anchor = find_with_regex(k, self.re_anchor)
                    if _anchor:
                        _missing = object()
                        _return = self.valid_anchors.get(k, _missing)
                        _return_parent = object()
                        if _return is not _missing:
                            _return_parent = self.valid_anchors[k].get('parent', _missing)

                        if _return is _missing or _return_parent is _missing:

                            if len(_anchor) > 1:
                                logger.error(f"We dont support multiple anchor in one key. ERROR Key is: {key}")
                                print(f"We dont support multiple anchor in one key. ERROR Key is: {key}")
                                return -1

                            if len(k) <= len(_anchor[0]):
                                # Key Name length must be greater than zero
                                logger.error(f"Length of key name (except anchor length) must be greater than one. ERROR Key is: {k}")
                                print(f"Length of key name (except anchor length) must be greater than one. ERROR Key is: {k}")
                                return -1

                            if k[0:len(_anchor[0])] == _anchor[0]:
                                # Key Name cant start with anchor
                                logger.error(f"Key name cant start with anchor. ERROR Key is: {k}")
                                print(f"Key name cant start with anchor. ERROR Key is: {k}")
                                return -1

                            _start_idx = len(k) - len(_anchor[0])
                            if k[_start_idx:] != _anchor[0]:
                                # Anchor must be end of key name
                                logger.error(f"Anchor must be end of key name. ERROR Key is: {k}")
                                print(f"Anchor must be end of key name. ERROR Key is: {k}")
                                return -1

                            self.valid_anchors[k] = dict()
                            self.valid_anchors[k]['parent'] = _key[0:parent_idx]
                            self.valid_anchors[k]['name'] = find_with_regex(_anchor[0], self.re_name)

                            self.valid_anchor_names.append(find_with_regex(_anchor[0], self.re_name))

                    parent_idx += 1

            self.valid_anchor_names = [p[0] for p in self.valid_anchor_names]
            # Check for duplicate anchor names
            for k, v in Counter(self.valid_anchor_names).items():
                if v > 1:
                    print(f"There is duplicate in anchors name and name is: {k}")
                    logger.error(f"There is duplicate in anchors name and name is: {k}")
                    return -1

            return 1

        except Exception as err:
            logger.error(err, exc_info=True)
            return -1

    def pointers_validation(self):
        try:
            # Checking Pointers
            duplicate_counter = 1
            for key in self.all_occurrence_of_pointers:
                _key = key.split(self.delimiter)
                parent_idx = 0
                for k in _key:
                    if self.pointer_pattern in k:
                        _parent = _key[0:parent_idx]
                        pointer_value = self.flatten_config[self.delimiter.join(_parent) + self.delimiter + k]
                        if not isinstance(pointer_value, str):
                            logger.error(f"Value of pointer key is not valid. value is: {pointer_value}")
                            print(f"Value of pointer key is not valid. value is: {pointer_value}")
                            return -1
                        _pointer_name = pointer_value

                        _missing = object()
                        _return_key = self.valid_pointers.get(self.pointer_pattern, _missing)
                        # _return_key = self.valid_pointers.get(k, _missing)
                        if _return_key is _missing:
                            self.valid_pointers[self.pointer_pattern] = dict()
                            self.valid_pointers[self.pointer_pattern]['parent'] = _parent
                            self.valid_pointers[self.pointer_pattern]['name'] = _pointer_name
                            self.valid_pointers[self.pointer_pattern]['key'] = k

                        else:
                            self.valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)] = dict()
                            self.valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)]['parent'] = _parent
                            self.valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)]['name'] = _pointer_name
                            self.valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)]['key'] = k

                            duplicate_counter += 1

                            # if _pointer_name.rsplit(self.pointer_to_anchor_notion)[-1][0:-1] not in self.valid_anchor_names:
                            # pointer_name = find_with_regex(_pointer_name, self.re_name)
                            if _pointer_name not in self.valid_anchor_names:
                                print(f"There is a pointer that not match to the anchors and pointer is: {_pointer_name}")
                                logger.error(f"There is a pointer that not match to the anchors and pointer is: {_pointer_name}")
                                return -1

                    parent_idx += 1

            return 1

        except Exception as err:
            logger.error(err, exc_info=True)
            return -1

    def get_from_dict(self, config_dict, map_list):
        try:
            if map_list:
                first, rest = map_list[0], map_list[1:]

                if rest:
                    # if `rest` is not empty, run the function recursively
                    _missing = object()
                    _return = config_dict.get(first, _missing)
                    if _return is _missing:
                        # Key doesnt exist
                        print(f'Key doesnt exist: {first}')
                        logger.error(f'Key doesnt exist: {first}')
                        self.recursive_dict_return_value = -1
                        return -1
                    else:
                        return self.get_from_dict(config_dict[first], rest)
                else:
                    _missing = object()
                    _return = config_dict.get(first, _missing)
                    if _return is _missing:
                        # Key doesnt exist
                        print(f'Key doesnt exist: {first}')
                        logger.error(f'Key doesnt exist: {first}')
                        self.recursive_dict_return_value = -1
                        return -1

                    else:
                        self.recursive_dict_return_value = 1
                        return config_dict[first]
            else:
                print('Map list is empty')
                logger.error('Map list is empty')
                self.recursive_dict_return_value = -1
                return -1

        except Exception as err:
            logger.error(err, exc_info=True)
            self.recursive_dict_return_value = -1
            return -1

    def set_in_dict(self, config_dict, map_list, value):
        try:
            if map_list:
                first, rest = map_list[0], map_list[1:]

                if rest:
                    try:
                        if not isinstance(config_dict[first], dict):
                            print(f"key: {first} is not a dict")
                            logger.error(f"key: {first} is not a dict")
                            # if the key is not a dict, then make it a dict
                            # config_dict[first] = {}
                            self.recursive_dict_return_value = -1
                            return -1
                    except KeyError:
                        # if key doesn't exist, create one
                        # config_dict[first] = {}
                        print(f"key: {first} doesnt exist")
                        logger.error(f"key: {first} doesnt exist")
                        self.recursive_dict_return_value = -1
                        return -1

                    self.set_in_dict(config_dict[first], rest, value)
                else:
                    _missing = object()
                    _return = config_dict.get(first, _missing)
                    if _return is not _missing:
                        config_dict[first] = value
                        self.recursive_dict_return_value = 1
                    else:
                        print(f"At the end, key: {first} doesnt exist")
                        logger.error(f"At the end, key: {first} doesnt exist")
                        self.recursive_dict_return_value = -1
                        return -1
            else:
                print('Map list is empty')
                logger.error('Map list is empty')
                self.recursive_dict_return_value = -1
                return -1

        except Exception as err:
            logger.error(err, exc_info=True)
            self.recursive_dict_return_value = -1
            return -1

    def del_in_dict(self, config_dict, map_list, rename=False, new_name=None):
        try:
            if map_list:
                first, rest = map_list[0], map_list[1:]

                if rest:
                    try:
                        if not isinstance(config_dict[first], dict):
                            print('list map key is not a dict')
                            logger.error('list map key is not a dict')
                            # if the key is not a dict, then make it a dict
                            # config_dict[first] = {}
                            self.recursive_dict_return_value = -1
                            return -1

                    except KeyError:
                        # if key doesn't exist, create one
                        # config_dict[first] = {}
                        print(f"key: {first} doesnt exist")
                        logger.error(f"key: {first} doesnt exist")
                        self.recursive_dict_return_value = -1
                        return -1

                    self.del_in_dict(config_dict[first], rest, rename=rename, new_name=new_name)
                else:
                    # config_dict[first] = value
                    _missing = object()
                    _return = config_dict.get(first, _missing)
                    if _return is _missing:
                        # Key doesnt exist
                        print(f'Key doesnt exist: {first}')
                        logger.error(f'Key doesnt exist: {first}')
                        self.recursive_dict_return_value = -1
                        return -1
                    else:
                        if rename:
                            config_dict[new_name] = config_dict[first]
                            del config_dict[first]

                        else:
                            del config_dict[first]

                        self.recursive_dict_return_value = 1
                        return 1
            else:
                print('Map list is empty')
                logger.error('Map list is empty')
                self.recursive_dict_return_value = -1
                return -1

        except Exception as err:
            logger.error(err, exc_info=True)
            self.recursive_dict_return_value = -1
            return -1

    def update_valid_anchors(self, config_dict):
        try:
            _flatten_config = flatdict.FlatDict(config_dict).keys()
            _all_occurrence_of_anchors = []
            for key in _flatten_config:
                if self.anchor_start_pattern in key:
                    _all_occurrence_of_anchors.append(key)

            _valid_anchors = dict()
            _valid_anchor_names = []
            # Checking for anchor occurrence and position and number of anchors in each key
            for key in _all_occurrence_of_anchors:
                _key = key.split(self.delimiter)
                parent_idx = 0
                for k in _key:
                    _anchor = find_with_regex(k, self.re_anchor)
                    if _anchor:
                        _missing = object()
                        _return = _valid_anchors.get(k, _missing)
                        _return_parent = object()
                        if _return is not _missing:
                            _return_parent = _valid_anchors[k].get('parent', _missing)

                        if _return is _missing or _return_parent is _missing:
                            _valid_anchors[k] = dict()
                            _valid_anchors[k]['parent'] = _key[0:parent_idx]
                            _valid_anchors[k]['name'] = find_with_regex(_anchor[0], self.re_name)

                            _valid_anchor_names.append(find_with_regex(_anchor[0], self.re_name))

                    parent_idx += 1

            _valid_anchor_names = [p[0] for p in _valid_anchor_names]

            return _valid_anchors

        except Exception as err:
            logger.error(err, exc_info=True)
            return -1

    def update_valid_pointers(self, config_dict):
        try:
            _flatten_config = flatdict.FlatDict(config_dict)
            _all_occurrence_of_pointers = []
            for key in _flatten_config.keys():
                if self.pointer_pattern in key:
                    _all_occurrence_of_pointers.append(key)

            # Checking Pointers
            _valid_pointers = dict()
            duplicate_counter = 1
            for key in _all_occurrence_of_pointers:
                _key = key.split(self.delimiter)
                parent_idx = 0
                for k in _key:
                    if self.pointer_pattern in k:
                        _parent = _key[0:parent_idx]
                        # _pointer_name = _flatten_config[self.delimiter.join(_parent)+self.delimiter+self.pointer_pattern]
                        _pointer_name = _flatten_config[self.delimiter.join(_parent) + self.delimiter + k]

                        _missing = object()
                        # _return_key = self.valid_pointers.get(self.pointer_pattern, _missing)
                        _return_key = _valid_pointers.get(k, _missing)
                        if _return_key is _missing:
                            _valid_pointers[self.pointer_pattern] = dict()
                            _valid_pointers[self.pointer_pattern]['parent'] = _parent
                            _valid_pointers[self.pointer_pattern]['name'] = _pointer_name
                            _valid_pointers[self.pointer_pattern]['key'] = k

                        else:
                            _valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)] = dict()
                            _valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)]['parent'] = _parent
                            _valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)]['name'] = _pointer_name
                            _valid_pointers[self.pointer_pattern + '_' + str(duplicate_counter)]['key'] = k

                            duplicate_counter += 1

                        # In update we need update _flatten_config
                        # _flatten_config = flatdict.FlatDict(config_dict)

                    parent_idx += 1

            return _valid_pointers

        except Exception as err:
            logger.error(err, exc_info=True)
            return -1

    def clean_dict(self, config_dict):
        """
        Make a copy of 'config_dict' and remove all anchors with 'self.anchor_start_pattern' and pointers with 'self.pointer_pattern' in keys
        :return: cleaned dict
        """
        try:
            duplicate = copy.deepcopy(config_dict)

            _valid_anchors = self.update_valid_anchors(config_dict=duplicate)
            if _valid_anchors == -1:
                return -1
            _valid_pointers = self.update_valid_pointers(config_dict=duplicate)
            if _valid_pointers == -1:
                return -1
            while _valid_pointers.keys():
                # Remove all pointers
                # for pointer_key in _valid_pointers.keys():
                for pointer_key in reversed(list(_valid_pointers.keys())):
                    pointer_parent = _valid_pointers[pointer_key]['parent']
                    pointer_key = _valid_pointers[pointer_key]['key']
                    # Delete pointer
                    stat = self.del_in_dict(duplicate, (self.delimiter.join(pointer_parent) + self.delimiter +
                                                        pointer_key).split(self.delimiter))
                    if stat == -1:
                        return -1
                    # After delete a pointer we need update _valid_pointers
                    _valid_pointers = self.update_valid_pointers(config_dict=duplicate)
                    if _valid_pointers == -1:
                        return -1

            while _valid_anchors.keys() or _valid_pointers.keys():
                # Update all anchors
                # for anchor_key in _valid_anchors.keys():
                for anchor_key in reversed(list(_valid_anchors.keys())):
                    anchor_parent = _valid_anchors[anchor_key]['parent']
                    new_name = self.anchor_start_pattern.join(anchor_key.rsplit(self.anchor_start_pattern)[0:-1])
                    self.del_in_dict(duplicate, (self.delimiter.join(anchor_parent) + self.delimiter + anchor_key).split(self.delimiter),
                                     rename=True, new_name=new_name)
                    # After updating a key we need update _valid_anchors
                    _valid_anchors = self.update_valid_anchors(config_dict=duplicate)
                    if _valid_anchors == -1:
                        return -1

            return duplicate

        except Exception as err:
            logger.error(err, exc_info=True)
            return -1

    def merge_pointers_with_anchors(self):
        try:
            # Merge pointers with anchors
            for pointer_key in reversed(list(self.valid_pointers.keys())):
                pointer_parent = self.valid_pointers[pointer_key]['parent']
                pointer_name = self.valid_pointers[pointer_key]['name']

                for anchor_key in reversed(list(self.valid_anchors.keys())):
                    anchor_name = self.valid_anchors[anchor_key]['name'][0]
                    anchor_parent = self.valid_anchors[anchor_key]['parent']
                    if anchor_name == pointer_name:
                        _anchor_part = self.get_from_dict(self.config_dict,
                                                          (self.delimiter.join(anchor_parent) + self.delimiter + anchor_key).split(
                                                              self.delimiter))
                        if _anchor_part == -1:
                            return -1

                        _pointer_part = self.get_from_dict(self.config_dict, pointer_parent)
                        if _pointer_part == -1:
                            return -1
                        # Checking for list as merge elements
                        both_list_flag = False
                        merge_dict_parts = None
                        if isinstance(_anchor_part, list) and isinstance(_pointer_part, list):
                            # Concat lists
                            merge_dict_parts = _anchor_part + _pointer_part
                            logger.error(f"We have two list for merge. We concat lists and we dont remove repeated values")
                            both_list_flag = True
                        elif isinstance(_anchor_part, list):
                            _anchor_part = dict.fromkeys(['_anchor_part_list_as_dict'], _anchor_part)
                            logger.error(f"We have anchor part with type list. "
                                         f"We create a dict with key: '_anchor_part_list_as_dict' and add this list to that ")

                        elif isinstance(_pointer_part, list):
                            _pointer_part = dict.fromkeys(['_pointer_part_list_as_dict'], _pointer_part)
                            logger.error(f"We have pointer part with type list. "
                                         f"We create a dict with key: '_pointer_part_list_as_dict' and add this list to that ")
                        if not both_list_flag:
                            # Merge dicts
                            merge_dict_parts = MeldDict(_anchor_part) + _pointer_part

                        # Update pointer in dict with merged key
                        stat = self.set_in_dict(self.config_dict, self.delimiter.join(pointer_parent).split(self.delimiter), merge_dict_parts)
                        if stat == -1:
                            return -1

                        break

            self.config_dict = self.clean_dict(self.config_dict)
            if self.config_dict == -1:
                return -1

            return 1

        except Exception as err:
            logger.error(err, exc_info=True)
            return -1
