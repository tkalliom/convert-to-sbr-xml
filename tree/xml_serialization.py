from xml.etree import ElementTree

def _xmlstring(val):
  if isinstance(val, str):
    return val
  try:
    return str(val)
  except UnicodeEncodeError:
    return val

def _handle_node(element, node):
  for attribute_name in node._required_attributes:
    if attribute_name not in node:
      raise RuntimeError("Required attribute {} missing".format(attribute_name))
    element.set(attribute_name, _xmlstring(node[attribute_name]))
  for attribute_name in node._optional_attributes:
    if attribute_name in node:
      element.set(attribute_name, _xmlstring(node[attribute_name]))
  calculated_attributes = node.calculated_attributes()
  for attribute_name in calculated_attributes.keys():
    element.set(attribute_name, _xmlstring(calculated_attributes[attribute_name]))

  if node._children:
    for child in node._children:
      child_element = ElementTree.SubElement(element, child.__class__.__name__.lower())
      _handle_node(child_element, child)


def serialize(node):
  root = ElementTree.Element(node.__class__.__name__.lower())
  _handle_node(root, node)
  # ElementTree.tostring does not escape \r and minidom (which would have pretty printing) does not even escape \n
  return ElementTree.tostring(root, encoding='UTF-8').replace(b'\r', b'&#13;')
