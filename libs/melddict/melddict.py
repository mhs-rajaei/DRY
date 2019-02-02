import sys

PY3 = sys.version_info[0] == 3
if PY3:
    # Python 3
    from collections.abc import Iterable, Mapping
    # Mapping = dict
    # Iterable = (list, tuple)
else:
    # Python 2
    from collections import Iterable, Mapping

from copy import deepcopy


class MeldDict(dict):
    """
    A dict subclass which supports adding and subtracting.
    """

    meld_iters = True
    """
    Whether or not to meld Iterables as well.

    When adding, corresponding values which are both Iterable are converted to
    a list of all the items. When subtracting, corresponding values which are
    both Iterable are converted to a list with common items removed, while
    other items are ignored. Corresponding values where the types don't match
    are replaced or ignored.
    """

    remove_emptied = False
    """
    Whether or not to remove Mappings or Iterables that are completely empty
    after subtraction.
    """

    def add(self, other):
        """
        Recursively merge another Mapping into this one, adding to or replacing
        the existing key / values.

        Corresponding values which are both Mappings will be converted to
        a MeldDict and added (i.e., recursively).

        Corresponding values that are both Iterable (but not strings) will be
        added or replaced according to :attr:`meld_iters`.

        Otherwise, corresponding values will be replaced. Non-corresponding
        values from the other Mapping will be inserted into this one.

        You can also perform addition using the forward, reverse, and in-place
        operators::

            meld_dict = MeldDict({...})
            norm_dict = {...}

            meld_dict + norm_dict
            norm_dict + meld_dict
            meld_dict += norm_dict
            norm_dict += meld_dict
        """
        if not isinstance(other, Mapping):
            raise TypeError('can only add Mapping '
                            '(not "{}")'.format(type(other).__name__))
        for key, that in other.items():
            if key not in self:
                self[key] = that
                continue
            this = self[key]
            if isinstance(this, Mapping) and isinstance(that, Mapping):
                self[key] = MeldDict(this).add(that)
            elif (isinstance(this, Iterable) and isinstance(that, Iterable) and
                  not (isinstance(this, str) or isinstance(that, str)) and self.meld_iters):
                self[key] = list(this) + list(that)
            else:
                self[key] = that
        return self

    def subtract(self, other):
        """
        Recursively subtract another Mapping from this one, removing
        corresponding the existing key / values.

        Corresponding values which are both Mappings will be converted to
        a MeldDict and subtracted.

        Corresponding values that are both Iterable (but not strings) will be
        subtracted or not according to :attr:`meld_iters`.

        Otherwise, corresponding keys will be deleted. Non-corresponding
        keys will be ignored.

        You can also perform subtraction using the forward, reverse, and
        in-place operators::

            meld_dict = MeldDict({...})
            norm_dict = {...}

            meld_dict - norm_dict
            norm_dict - meld_dict
            meld_dict -= norm_dict
            norm_dict -= meld_dict
        """
        if not isinstance(other, Mapping):
            raise TypeError('can only subtract Mapping '
                            '(not "{}")'.format(type(other).__name__))
        to_remove = []
        for key, this in self.items():
            if key not in other:
                continue
            that = other[key]
            if isinstance(this, Mapping) and isinstance(that, Mapping):
                self[key] = MeldDict(this).subtract(that)
                if not self[key] and self.remove_emptied:
                    to_remove.append(key)
            elif (isinstance(this, Iterable) and isinstance(that, Iterable) and
                  not (isinstance(this, str) or isinstance(that, str)) and
                  self.meld_iters):
                self[key] = [item for item in this if item not in that]
                if not self[key] and self.remove_emptied:
                    to_remove.append(key)
            else:
                # can't modify dict while iterating
                to_remove.append(key)
        for key in to_remove:
            del self[key]
        return self

    def __add__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return MeldDict(deepcopy(self)).add(other)

    def __radd__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return MeldDict(deepcopy(other)).add(self)

    def __iadd__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return self.add(other)

    def __sub__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return MeldDict(deepcopy(self)).subtract(other)

    def __rsub__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return MeldDict(deepcopy(other)).subtract(self)

    def __isub__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return self.subtract(other)
