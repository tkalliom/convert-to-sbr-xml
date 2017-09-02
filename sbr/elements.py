from tree.elements import Node

class _Collection(Node):
  _required_attributes = {"backup_set", "backup_date"}

  def calculated_attributes(self):
    return {'count': len(self._children)}

  def append(self, event):
    self._children.append(event)

  def extend(self, events):
    self._children.extend(events)

  def sort(self):
    self._children.sort(key=lambda event: int(event["date"]))
  

class _Event(Node):
  _required_attributes = {"date"}
  _optional_attributes = {'contact_name', 'readable_date'}

class MessageBox(object):
  RECEIVED = 1
  SENT = 2
  DRAFT = 3

class _Message(_Event):
  _required_attributes = _Event._required_attributes | {'address', 'read', 'locked'}
  _optional_attributes = _Event._optional_attributes | {'date_sent'}

class AddressType(object):
  BCC = 129
  CC = 130
  FROM = 137
  TO = 151

class Sms(_Message):
  _required_attributes = _Message._required_attributes | {'protocol', 'type', 'body', 'toa', 'sc_toa', 'service_center', 'status'}

  _children = None

  def calculated_attributes(self):
    ret = super(_Message, self).calculated_attributes()
    ret.update({'subject': 'null'})
    return ret

class Mms(_Message):
  #TODO: some are probably calculated fields or optional fields
  _required_attributes = _Message._required_attributes | {'text_only', 'ct_t', 'msg_box', 'sub', 'sequence_time', 'seen', 'rr', 'ct_cls', 'retr_txt_cs', 'ct_l', 'phone_id', 'm_size', 'exp', 'sub_cs', 'st', 'creator', 'tr_id', 'sub_id', 'resp_st', 'm_id', 'pri', 'd_rpt', 'd_tm', 'read_status', 'retr_txt', 'resp_txt', 'rpt_a', 'star_status', 'm_cls', 'retr_st'}

  def __init__(self):
    super(_Message, self).__init__()
    self._children.append(Parts())
    self._children.append(Addrs())

  @staticmethod
  def _message_type(message_box):
    if message_box == MessageBox.DRAFT:
      return "null"
    elif message_box == MessageBox.RECEIVED:
      return "132"
    elif message_box == MessageBox.SENT:
      return "128"
    else:
      raise RuntimeError("Unknown direction {}".format(direction))

  def calculated_attributes(self):
    ret = super(_Message, self).calculated_attributes()
    ret.update({'v': 16, 'm_type': self._message_type(self['msg_box'])})
    return ret

  def add_part(self, part):
    self._children[0]._children.append(part)

  def add_addr(self, type, address):
    a = Addr()
    a["type"] = type
    a["address"] = address
    self._children[-1]._children.append(a)

class Parts(Node):
  pass

class Part(Node):
  _required_attributes = {'seq', 'ct', 'name', 'chset', 'cd', 'fn', 'cid', 'cl', 'ctt_s', 'ctt_t', 'text'}
  _optional_attributes = {'data'}

class Addrs(Node):
  pass

class Addr(Node):
  _required_attributes = {'address', 'type'}

  def calculated_attributes(self):
    # all examples seem to use the same charset?
    return {'charset': '106'}

class Smses(_Collection):
  @staticmethod
  def filename_prefix():
    return "sms-"

class CallType(object):
  INCOMING = 1
  OUTGOING = 2
  MISSED = 3
  VOICEMAIL = 4
  REJECTED = 5
  REFUSED_LIST = 6

class NumberPresentation(object):
  ALLOWED = 1
  RESTRICTED = 2
  UNKNOWN = 3
  PAYPHONE = 4

class Call(_Event):
  _required_attributes = _Event._required_attributes | {'number', 'duration', 'type', 'presentation'}
  children = None


class Calls(_Collection):
  @staticmethod
  def filename_prefix():
    return "calls-"
