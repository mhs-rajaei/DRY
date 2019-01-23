"""
In this file, we gather useful function form multiple sources like internet, our's, etc.

"""
import os
import sys
import logging
import re
import shutil
from collections import Counter, defaultdict
import traceback
import subprocess
import hashlib


logger = logging.getLogger("DRY")


def remove_path_or_file(path):
    """ param <path> could either be relative or absolute. """
    try:
        if os.path.isfile(path):
            os.remove(path)  # remove_path_or_file the file
        elif os.path.isdir(path):
            shutil.rmtree(path)  # remove_path_or_file dir and all contains
        else:
            logger.info(f"file {path} is not a file or dir.")
            print(f"file {path} is not a file or dir.")
    except OSError as err:
        print(f"Error: {err.filename} - {err.strerror}.")
        logger.error(f"Error: {err.filename} - {err.strerror}.")


def calculate_file_hash(path):
    # BUF_SIZE is totally arbitrary, change for your app!
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!

    # md5 = hashlib.md5()
    # sha1 = hashlib.sha1()
    sha512 = hashlib.sha3_512()
    # sha512 = hashlib.sha512()
    try:
        with open(path, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                # md5.update(data)
                # sha1.update(data)
                sha512.update(data)
    except Exception as err:
        print(f"Exception occurred in calculating Hash value with exception: {err}")
        return -1, err
    # print("MD5: {0}".format(md5.hexdigest()))
    # print("SHA1: {0}".format(sha1.hexdigest()))

    return 1, sha512.hexdigest()


def move_file(src, dst_dir, save_file_name=None):
    try:
        last_part = os.path.split(src)[-1]

        os.rename(src, os.path.join(dst_dir, last_part))
        if save_file_name:
            os.rename(os.path.join(dst_dir, last_part), os.path.join(dst_dir, save_file_name))
            # os.rename(src, os.path.join(dst_dir, last_part))

    except Exception as err:
        return -1, err
    return 1, None


# https://stackoverflow.com/questions/18394147/recursive-sub-folder-search-and-return-files-in-a-list-python
def find_files(files, dirs=None, extensions=None):
    new_dirs = []
    for d in dirs:
        try:
            new_dirs += [os.path.join(d, f) for f in os.listdir(d)]
        except OSError:
            if extensions:
                if os.path.splitext(d)[1] in extensions:
                    files.append(d)
            else:
                files.append(d)

    if new_dirs:
        find_files(files, new_dirs, extensions=extensions)
    else:
        return


# Function removes any unwanted symbols
def clean_wordlist(wordlist):
    clean_list = []
    for word in wordlist:
        symbols = '!@#$%^&*()_-+={[}]|\;:"<>?/., '

        for i in range(0, len(symbols)):
            word = word.replace(symbols[i], '')

        if len(word) > 0:
            clean_list.append(word)
    create_dictionary(clean_list)


# Creates a dictionary containing each word's
# count and top_20 occurring words
def create_dictionary(clean_list):
    word_count = {}

    for word in clean_list:
        if word in word_count:
            word_count[word] += 1
        else:
            word_count[word] = 1

    ''' To get count of each word in 
        the crawled page --> 

    # operator.itemgetter() takes one  
    # parameter either 1(denotes keys) 
    # or 0 (denotes corresponding values) 

    for key, value in sorted(word_count.items(), 
                    key = operator.itemgetter(1)): 
        print ("% s : % s " % (key, value)) 

    <-- '''

    c = Counter(word_count)

    # returns the most occuring elements
    top = c.most_common(10)
    print(top)


def validate_file(file_path, hash):
    """
    Validates a file against an MD5 hash value

    :param file_path: path to the file for hash validation
    :type file_path:  string
    :param hash:      expected hash value of the file
    :type hash:       string -- MD5 hash value
    """
    m = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(1000 * 1000)  # 1MB
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest() == hash


def print_exception(exc_info):
    exc_type, exc_value, exc_traceback = exc_info
    print("*** print_tb:")
    traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
    print("*** print_exception:")
    traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
    print("*** print_exc:")
    traceback.print_exc()
    print("*** format_exc, first and last line:")
    formatted_lines = traceback.format_exc().splitlines()
    print(formatted_lines[0])
    print(formatted_lines[-1])
    print("*** format_exception:")
    print(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    print("*** extract_tb:")
    print(repr(traceback.extract_tb(exc_traceback)))
    print("*** format_tb:")
    print(repr(traceback.format_tb(exc_traceback)))
    print("*** tb_lineno:", exc_traceback.tb_lineno)


def defaultify(d):
    if isinstance(d, dict):
        return defaultdict(lambda: None, {k: defaultify(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [defaultify(e) for e in d]
    else:
        return d


def find_with_regex_and_start_end_strings(string_content, regex_pattern, start_string, end_string):

    _re = re.compile(regex_pattern, re.I)

    all_pattern = []
    all_start_occurrences = [m.start() for m in re.finditer(_re, string_content)]
    for start_occurrences in all_start_occurrences:
        start = start_occurrences + len(start_string)
        end = string_content.find(end_string, start) + len(end_string)

        desired_string = string_content[start_occurrences:end]
        all_pattern.append(desired_string)

    return all_pattern


def find_with_regex(string_content, re_string):
    _re = re.compile(re_string, re.I)
    regex_items = re.findall(_re, string_content)
    if regex_items:
        return regex_items
    else:
        return None


def recursive_items(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            yield from recursive_items(value)
        else:
            yield (key, value)


# https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-python-dictionaries-and-lists
def get_recursively(search_dict):
    """Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if isinstance(value, dict):
            results = get_recursively(value)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_recursively(item)
                    for another_result in more_results:
                        fields_found.append(another_result)
        if key:
            fields_found.append([key, value])

    return fields_found
