"""
KeyedList sorted dictionary class.
"""


# CEBALERT: Do most uses of KeyedList look like they would be better
# served by something that's really a dictionary, but which maintains
# order (rather than something that's really a list, but allows some
# dictionary-style access)? If so, we could use one of the many online
# ordered dictionaries instead.
# http://cheeseshop.python.org/pypi/Ordered%20Dictionary/0.2.2
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496761
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/107747
#
# Sometimes having a KeyedList is confusing, because you can't use
# natural syntax such as "x in y" when y is a KeyedList.
#
# JB: Sure, we could use one of those instead; no good reason to
# maintain our own not-quite-full-featured version.


class KeyedList(list):
    """
    Extends the built-in type 'list' to support dictionary-like
    access using [].  The internal representation is as an ordinary
    list of (key,value) pairs, not a hash table like an ordinary
    dictionary, so that the elements will remain ordered.

    Note: Not all list operations will work as expected, because
    [] does not return the name tuple.

    Redefined functions::

        __getitem__ ([,])
        __setitem__ ([,])
        append  --  Now takes a tuple (key,value) so that value
                    can be later accessed by [key].

    New functions modeled from dictionaries::

        get
        set
        has_key
        keys
        items
        update

    Key values are not allowed to be None, because None is a
    default return value for get() when there is no object
    by that name.
    """

    def __getitem__(self,key):
        """The bracket [] accessor."""
        for (name,value) in self:
            if name == key:
                return value

        # Though not often useful for this class, the list interface
        # provides for access by an integer key:
        if isinstance(key,int):
            for (index,(name,value)) in enumerate(self):
                if index == key:
                    return value

        raise KeyError(key)


    def __setitem__(self,k,v):
        """
        The bracket [] mutator.
        Overwrite value if key already exists, otherwise append.
        """
        return self.set(k,v)


    def append(self, (key, value)):
        """
        Append a new object to the end of the existing list.

        Accepts a 2-tuple (key, value).

        Strictly speaking, this operation did not need to be redefined
        in this subclass, but by forcing the tuple in the function
        parameters, we may be able to catch an erroneous assignment.
        """
        super(KeyedList,self).append(tuple((key,value)))


    def get(self, key, default=None):
        """
        Get the value with the specified key.

        Returns None if no value with that key exists.
        """
        for (name,value) in self:
            if name == key:
                return value

        return default


    def set(self, key, value):
        """
        If the key already exists in the list, change the entry.
        Otherwise append the new (key,value) to the end of the list.
        """
        for (k,v) in self:
            if k == key:
                i = self.index((k,v))
                self.pop(i)
                self.insert(i,(key, value))
                return True
        self.append((key, value))
        return True


    def has_key(self,key):
        """Return True iff key is found in the ordered list."""
        for (name,value) in self:
            if name == key:
                return True
        return False


    def items(self):
        """
        Provide the item function supported by dictionaries.
        A keyed list already is stored in this format, so just returns
        the actual underlying list.
        """
        return list(self)


    def keys(self):
        """A copy of the list of keys."""
        return [k for (k,v) in self.items()]


    def values(self):
        """A copy of the list of values."""
        return [v for (k,v) in self.items()]


    def update(self,b):
        """Updates (and overwrites) key/value pairs from b."""
        for (k,v) in b.items():
            self.set(k,v)
