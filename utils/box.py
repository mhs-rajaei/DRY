#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright (c) 2017-2018 - Chris Griffith - MIT License
"""
https://raw.githubusercontent.com/cdgriffith/Box/master/box.py
"""
import string
import sys
import json
import re
import copy
from keyword import kwlist
import warnings
import logging
logger = logging.getLogger("BOX")


try:
    from collections.abc import Iterable, Mapping, Callable
except ImportError:
    from collections import Iterable, Mapping, Callable

yaml_support = True

try:
    import ruamel.yaml as yaml
except ImportError:
    try:
        import yaml
    except ImportError:
        yaml = None
        yaml_support = False

if sys.version_info >= (3, 0):
    basestring = str
else:
    from io import open


_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


# Abstract converter functions for use in any Box class


def to_json(obj, filename=None,
             encoding="utf-8", errors="strict", **json_kwargs):
    json_dump = json.dumps(obj,
                           ensure_ascii=False, **json_kwargs)
    if filename:
        with open(filename, 'w', encoding=encoding, errors=errors) as f:
            f.write(json_dump if sys.version_info >= (3, 0) else
                    json_dump.decode("utf-8"))
    else:
        return json_dump


def load_from_json(json_string=None, filename=None,
               encoding="utf-8", errors="strict", multiline=False, **kwargs):
    if filename:
        with open(filename, 'r', encoding=encoding, errors=errors) as f:
            if multiline:
                data = [json.loads(line.strip(), **kwargs) for line in f
                        if line.strip() and not line.strip().startswith("#")]
            else:
                data = json.load(f, **kwargs)
    elif json_string:
        data = json.loads(json_string, **kwargs)
    else:
        # raise BoxError('from_json requires a string or filename')
        logger.error('from_json requires a string or filename')
        return -1

    return data


def to_yaml(obj, filename=None, default_flow_style=False,
             encoding="utf-8", errors="strict",
             **yaml_kwargs):
    if filename:
        with open(filename, 'w',
                  encoding=encoding, errors=errors) as f:
            yaml.dump(obj, stream=f,
                      default_flow_style=default_flow_style,
                      **yaml_kwargs)
    else:
        return yaml.dump(obj,
                         default_flow_style=default_flow_style,
                         **yaml_kwargs)


def load_from_yaml(yaml_string=None, filename=None, encoding="utf-8", errors="strict", **kwargs):
    if filename:
        with open(filename, 'r', encoding=encoding, errors=errors) as f:
            # data = yaml.load(f, **kwargs)
            data = yaml.load(f, Loader=yaml.Loader)
    elif yaml_string:
        data = yaml.load(yaml_string, **kwargs)
    else:
        # raise BoxError('from_yaml requires a string or filename')
        logger.error('from_yaml requires a string or filename')
        return -1
    return data


# Helper functions


def _safe_key(key):
    try:
        return str(key)
    except UnicodeEncodeError:
        return key.encode("utf-8", "ignore")


def _safe_attr(attr, camel_killer=False, replacement_char='x'):
    """Convert a key into something that is accessible as an attribute"""
    allowed = string.ascii_letters + string.digits + '_'

    attr = _safe_key(attr)

    if camel_killer:
        attr = _camel_killer(attr)

    attr = attr.replace(' ', '_')

    out = ''
    for character in attr:
        out += character if character in allowed else "_"
    out = out.strip("_")

    try:
        int(out[0])
    except (ValueError, IndexError):
        pass
    else:
        out = '{0}{1}'.format(replacement_char, out)

    if out in kwlist:
        out = '{0}{1}'.format(replacement_char, out)

    return re.sub('_+', '_', out)


def _camel_killer(attr):
    """
    CamelKiller, qu'est-ce que c'est?

    Taken from http://stackoverflow.com/a/1176023/3244542
    """
    try:
        attr = str(attr)
    except UnicodeEncodeError:
        attr = attr.encode("utf-8", "ignore")

    s1 = _first_cap_re.sub(r'\1_\2', attr)
    s2 = _all_cap_re.sub(r'\1_\2', s1)
    return re.sub('_+', '_', s2.casefold() if hasattr(s2, 'casefold') else
                  s2.lower())


def _recursive_tuples(iterable, box_class, recreate_tuples=False, **kwargs):
    out_list = []
    for i in iterable:
        if isinstance(i, dict):
            out_list.append(box_class(i, **kwargs))
        elif isinstance(i, list) or (recreate_tuples and isinstance(i, tuple)):
            out_list.append(_recursive_tuples(i, box_class,
                                              recreate_tuples, **kwargs))
        else:
            out_list.append(i)
    return tuple(out_list)


def _conversion_checks(item, keys, box_config, check_only=False,
                       pre_check=False):
    """
    Internal use for checking if a duplicate safe attribute already exists

    :param item: Item to see if a dup exists
    :param keys: Keys to check against
    :param box_config: Easier to pass in than ask for specfic items
    :param check_only: Don't bother doing the conversion work
    :param pre_check: Need to add the item to the list of keys to check
    :return: the original unmodified key, if exists and not check_only
    """
    if box_config['box_duplicates'] != 'ignore':
        if pre_check:
            keys = list(keys) + [item]

        key_list = [(k,
                     _safe_attr(k, camel_killer=box_config['camel_killer_box'],
                                replacement_char=box_config['box_safe_prefix']
                                )) for k in keys]
        if len(key_list) > len(set(x[1] for x in key_list)):
            seen = set()
            dups = set()
            for x in key_list:
                if x[1] in seen:
                    dups.add("{0}({1})".format(x[0], x[1]))
                seen.add(x[1])
            if box_config['box_duplicates'].startswith("warn"):
                warnings.warn('Duplicate conversion attributes exist: '
                              '{0}'.format(dups))
            else:
                # raise BoxError('Duplicate conversion attributes exist: '
                #                '{0}'.format(dups))
                logger.error('Duplicate conversion attributes exist: '
                               '{0}'.format(dups))
                return -1
    if check_only:
        return
    # This way will be slower for warnings, as it will have double work
    # But faster for the default 'ignore'
    for k in keys:
        if item == _safe_attr(k, camel_killer=box_config['camel_killer_box'],
                              replacement_char=box_config['box_safe_prefix']):
            return k


def _get_box_config(cls, kwargs):
    return {
        # Internal use only
        '__converted': set(),
        '__box_heritage': kwargs.pop('__box_heritage', None),
        '__created': False,
        # Can be changed by user after box creation
        'default_box': kwargs.pop('default_box', False),
        'default_box_attr': kwargs.pop('default_box_attr', cls),
        'conversion_box': kwargs.pop('conversion_box', True),
        'box_safe_prefix': kwargs.pop('box_safe_prefix', 'x'),
        'frozen_box': kwargs.pop('frozen_box', False),
        'camel_killer_box': kwargs.pop('camel_killer_box', False),
        'modify_tuples_box': kwargs.pop('modify_tuples_box', False),
        'box_duplicates': kwargs.pop('box_duplicates', 'ignore'),
        'ordered_box': kwargs.pop('ordered_box', False)
    }

