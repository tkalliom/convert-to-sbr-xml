class Node(object):
  _required_attributes = set()
  _optional_attributes = set()

  def __init__(self):
    self._attributes = {}
    self._children = []

  def __setitem__(self, key, value):
    if key not in self._required_attributes and key not in self._optional_attributes:
      raise KeyError("Unknown key {}.".format(key))
    self._attributes[key] = value

  def __getitem__(self, key):
    return self._attributes[key]

  def __contains__(self, key):
    return key in self._attributes

  def calculated_attributes(self):
    return {}
