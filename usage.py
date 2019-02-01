import os
import sys
from DRY import ConfigMerger
import logging
logger = logging.getLogger("DRY")  # DRY: Dont Repeat Yourself (Merge, Extend and Override your config file)

from utils.box import load_from_yaml, load_from_json, to_json, to_yaml
from utils.util import get_recursively
from pprint import pprint
PY3 = sys.version_info[0] == 3
import shutil
import ruamel.yaml as yaml
EDITING_ENABLED = True
yaml_version = '1.1'
indent_spaces = 4
block_seq_indent = 0
YAML_FILE = '.yaml'


def _strip_empty_lines(data):
    ldata = data.split('\n')

    rdata = []
    for index, line in enumerate(ldata):
        if len(line.strip()) == 0:
            line = line.strip()
        rdata.append(line)

    fdata = '\n'.join(rdata)
    if fdata[0] == '\n':
        fdata = fdata[1:]
    return fdata

def _format_yaml_dump2(sdata):
    """
    Format yaml-dump to make file more readable, used by yaml_save_roundtrip()
    (yaml structure must be dumped to a stream before using this function)
    | Currently does the following:
    | - Insert empty line after section w/o a value
    | - Insert empty line before section (key w/o a value)
    | - Adjust indentation of list entries
    | - Remove double line spacing introduced by ruamel.yaml
    | - Multiline strings: Remove '4' inserted by ruamel.yaml after '|'
    | - Remove empty line after section w/o a value, if the following line is a child-line
    :param data: string to format

    :return: formatted string
    """

    # Strip lines containing only spaces and strip empty lines inserted by ruamel.yaml
    sdata = _strip_empty_lines(sdata)
    sdata = sdata.replace('\n\n\n', '\n')
    sdata = sdata.replace('\n\n', '\n')
    #    sdata = sdata.replace(': |4\n', ': |\n')    # Multiline strings: remove '4' inserted by ruyaml

    ldata = sdata.split('\n')
    rdata = []
    for index, line in enumerate(ldata):
        # Remove empty line after section w/o a value, if the following line is a child-line
        if len(line.strip()) == 0:
            try:
                nextline = ldata[index + 1]
            except:
                nextline = ''
            indentprevline = len(ldata[index - 1]) - len(ldata[index - 1].lstrip(' '))
            indentnextline = len(nextline) - len(nextline.lstrip(' '))
            if indentnextline != indentprevline + indent_spaces:
                rdata.append(line)
        # Insert empty line after section w/o a value
        elif len(line.lstrip()) > 0 and line.lstrip()[0] == '#':
            if line.lstrip()[-1:] == ':':
                rdata.append('')
            # only insert empty line, if last line was not a comment
            elif len(ldata[index - 1].strip()) > 0 and ldata[index - 1][0] != '#':
                # Only insert empty line, if next line is not commented out
                if len(ldata[index + 1].strip()) > 0 and ldata[index + 1][-1:] == ':' and ldata[index + 1][0] != '#':
                    rdata.append('')
            rdata.append(line)

        # Insert empty line before section (key w/o a value)
        elif line[-1:] == ':':
            # only, if last line is not empty and last line is not a comment
            if len(ldata[index - 1].lstrip()) > 0 and not (len(ldata[index - 1].lstrip()) > 0 and ldata[index - 1].lstrip()[0] == '#'):
                # no empty line before list attributes
                if ldata[index + 1].strip() != '':
                    if ldata[index + 1].strip()[0] != '-':
                        rdata.append('')
                else:
                    rdata.append('')
                rdata.append(line)
            else:
                rdata.append(line)
        else:
            rdata.append(line)

    sdata = '\n'.join(rdata)

    sdata = sdata.replace('\n---\n\n', '\n---\n')
    if sdata[0] == '\n':
        sdata = sdata[1:]
    return sdata


def yaml_save_roundtrip(filename, data, create_backup=False):
    """
    Dump yaml using the RoundtripDumper and correct linespacing in output file

    :param filename: name of the yaml file to save to
    :param data: data structure to save
    """

    if not EDITING_ENABLED:
        return
    sdata = yaml.dump(data)

    #    with open(filename+'_raw'+YAML_FILE, 'w') as outfile:
    #        outfile.write( sdata )

    if create_backup:
        if os.path.isfile(filename + YAML_FILE):
            shutil.copy2(filename + YAML_FILE, filename + '.bak')

    sdata = _format_yaml_dump2(sdata)
    with open(filename + YAML_FILE, 'w') as outfile:
        outfile.write(sdata)

def main():
    # For usage of DRY go to config.yaml.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Loading config in YAML format
    # config_dict = load_from_yaml(filename=os.path.join(BASE_DIR, 'config/config.yaml'))
    # config_dict = load_from_yaml(filename='patchman37.yaml')
    # config_dict = load_from_yaml(filename='patchman27.yaml')
    # config_dict = load_from_yaml(filename='patchman27_1.yaml')
    config_dict = load_from_yaml(filename='py27_patchman37.yaml')
    # config_dict = load_from_yaml(filename=r'F:\Downloads\Dropbox\Work\PycharmProjects\PatchMan37\config\patchman37.yaml')
    # YAML to JSON
    # to_json(config_dict, filename=os.path.join(BASE_DIR, 'config/config.json'))

    key_counter = 0
    for key, value in get_recursively(config_dict):
        # pprint([key, value])
        key_counter += 1

    print("\nNumber of Keys 'config_dict' is: {0}\n {1}".format(key_counter, '-'*100))

    # .............................................................................
    # Usage of DRY
    merger_obj = ConfigMerger(config_dict, merge_at_init=True)
    if merger_obj.return_value == -1:
        logger.error('Error in Config Merger')
        return -1

    # Get merged dict as result
    merged_config_dict = merger_obj.config_dict
    pprint(merged_config_dict)
    if PY3:
        to_yaml(merged_config_dict, filename='py37_patchman37.yaml')
        # yaml_save_roundtrip(filename='smartphone_py37_patchman37.yaml', data=merged_config_dict)
    else:
        to_yaml(merged_config_dict, filename='py27_patchman37.yaml')

    key_counter = 0
    for key, value in get_recursively(merged_config_dict):
        # pprint([key, value])
        key_counter += 1

    print("\nNumber of Keys 'merged_config_dict' in YAML format is: {0}\n {1}".format(key_counter, '-'*100))

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

    print("\nNumber of Keys 'merged_config_dict' in JSON format is: {0}\n {1}".format(key_counter, '-'*100))


if __name__ == "__main__":
    main()
