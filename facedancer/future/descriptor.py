#
# This file is part of FaceDancer.
#
""" Functionality for working with objects with associated USB descriptors. """

from dataclasses import dataclass

from .magic import AutoInstantiable

from enum import IntEnum


class USBDescribable(object):
    """
    Abstract base class for objects that can be created from USB descriptors.
    """

    # Override me!
    DESCRIPTOR_TYPE_NUMBER = None

    @classmethod
    def handles_binary_descriptor(cls, data):
        """
        Returns true iff this class handles the given descriptor. By default,
        this is based on the class's DESCRIPTOR_TYPE_NUMBER declaration.
        """
        return data[1] == cls.DESCRIPTOR_TYPE_NUMBER



    @classmethod
    def from_binary_descriptor(cls, data):
        """
        Attempts to create a USBDescriptor subclass from the given raw
        descriptor data.
        """

        for subclass in cls.__subclasses__():
            # If this subclass handles our binary descriptor, use it to parse the given descriptor.
            if subclass.handles_binary_descriptor(data):
                return subclass.from_binary_descriptor(data)

        return None



@dataclass
class USBDescriptor(USBDescribable, AutoInstantiable):
    """ Class for arbitrary USB descriptors; minimal concrete implementation of USBDescribable. """

    number      : int
    raw         : bytes

    type_number : int            = None
    parent      : USBDescribable = None

    def __call__(self, index=0):
        """ Converts the descriptor object into raw bytes. """
        return self.raw

    def get_identifier(self):
        return self.number


@dataclass
class USBClassDescriptor(USBDescriptor):
    """ Class for arbitrary USB Class descriptors. """


@dataclass
class USBStringDescriptor(USBDescriptor):
    """ Class representing a USB string descriptor. """

    DESCRIPTOR_TYPE_NUMBER = 3

    # Property: the python version of the relevant string.
    python_string : str = None

    @classmethod
    def from_string(cls, string, *, index=None):

        # Grab the raw string
        raw_string = string.encode('utf-16')[2:]
        raw = bytes([len(raw_string) + 2, cls.DESCRIPTOR_TYPE_NUMBER, *raw_string])

        return cls(raw=raw, number=index, type_number=3, python_string=string)



class StringDescriptorManager:
    """ Manager class that collects active string descriptors. """

    def __init__(self):
        self.next_index = 1

        # Maps indexes => string descriptors.
        self.descriptors = {}

        # Maps python strings => indexes.
        self.indexes     = {}



    def _allocate_index(self):
        """ Grabs a unique, ascending string index for the current string. """

        index = self.next_index
        self.next_index += 1

        return index


    def add_string(self, string):
        """ Adds a python string to the string manager, and returns an index. """

        index = self._allocate_index()

        self.descriptors[index] = USBStringDescriptor.from_string(string, index=index)
        self.indexes[string]    = index

        return index


    def get_index(self, string):
        """ Returns the index of the given string; creating it if the string isn't already known. """

        # Special case: return 0 for None, allowing null strings to be represented.
        if string is None:
            return 0

        if string in self.indexes:
            return self.indexes[string]

        return self.add_string(string)


    def __getitem__(self, index):
        """ Gets the relevant string descriptor. """

        if isinstance(index, str):
            index = self.get_index(index)

        return self.descriptors.get(index, None)


class USBDescriptorTypeNumber(IntEnum):
    DEVICE                    = 1
    CONFIGURATION             = 2
    STRING                    = 3
    INTERFACE                 = 4
    ENDPOINT                  = 5
    DEVICE_QUALIFIER          = 6
    OTHER_SPEED_CONFIGURATION = 7
    INTERFACE_POWER           = 8
    HID                       = 33
    REPORT                    = 34
