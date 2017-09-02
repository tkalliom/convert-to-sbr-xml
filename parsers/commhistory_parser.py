import sqlite3
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from os import unlink
from base64 import b64encode
import re
from xml.etree.ElementTree import XMLParser, ParseError
import warnings

import magic

from sbr.elements import Sms, Mms, MessageBox, Part, AddressType, Call, CallType, NumberPresentation

class SmilHandler:

  parts = []

  def __init__(self, directory):
    self.directory = directory

  def start(self, tag, attrib):
    if "src" in attrib and tag in ["text", "img", "animation", "audio", "video", "ref"]:
      if tag in ["animation", "audio", "video", "ref"]:
        warnings.warn("The SMIL element " + tag + " is untested. Results may be wrong.")
        
      with open(self.directory + "/_" + attrib["src"] + "_", 'rb') as partfile:
        part_data = partfile.read()
      
      part = Part()
      parsed = dict(
        seq = "0",
        ct = magic.from_buffer(part_data, mime=True),
        name = attrib["src"],
        chset = "106" if tag == "text" else "null",
        cd = "null", fn = "null",
        cid = "<" + attrib["src"] + ">",
        cl = attrib["src"],
        ctt_s = "null", ctt_t = "null",
        text = part_data.decode("UTF-8") if tag == "text" else "null",
      )
      if tag != "text":
        encoded = b64encode(part_data)
        if type(encoded) is bytes:
          encoded = encoded.decode("ASCII")
        parsed["data"] = encoded

      for key in parsed:
        part[key] = parsed[key]

      self.parts.append(part)

  def end(self, tag):
    pass

  def data(self, data):
    pass

  def close(self):
    return self.parts

def _message_box(direction, is_draft):
  if is_draft:
    return MessageBox.DRAFT
  elif direction == 1:
    return MessageBox.RECEIVED
  elif direction == 2:
    return MessageBox.SENT
  else:
    raise RuntimeError("Unknown commhistory direction {}".format(direction))

def _handle_smses(cursor):
  ret = []
  for row in cursor.execute("SELECT id, type, startTime, endTime, direction, isDraft, isRead, remoteUid, freeText, mmsId, hasMessageParts, headers FROM Events WHERE type IN (2, 6)"):
    if row['type'] == 2:
      msg = Sms()

      parsed = dict(
        date = str(row['endTime']) + '000',
        address = row['remoteUid'], read = row['isRead'], locked = '0',
        protocol = '0', type = _message_box(row['direction'], row['isDraft']), body = row['freeText'], toa = "null", sc_toa = "null", service_center = "null", status = "-1"
      )
      if parsed["address"] == "" or parsed["address"] == None:
        if parsed["isDraft"]:
          parsed["address"] = "null"
        else:
          raise RuntimeError("Unexpected missing remoteUid in non-draft message")
    else:
      if not row['hasMessageParts']:
        warnings.warn("MMS without locally stored parts not supported")
        continue

      msg = Mms()

      parsed = dict(
        date = str(row['endTime']) + '000',
        address = row['remoteUid'],
        read = row['isRead'],
        locked = '0', text_only = '0', ct_t = "application/vnd.wap.multipart.related",
        msg_box = _message_box(row['direction'], row['isDraft']),
        sub = "null",
        sequence_time = str(row['startTime']) + '000',
        seen="0", rr="null", ct_cls="null", retr_txt_cs="null", ct_l="null", phone_id="-1", m_size="null", exp="null", sub_cs="null", st="null", creator="org.freedesktop.Telepathy.Client.CommHistory", tr_id="null", sub_id="1",
        resp_st="null",
        m_id=row["mmsId"],
        date_sent="0", pri="129",
        d_rpt="129", d_tm="null", read_status="null", retr_txt="null", resp_txt="null", rpt_a="null", star_status="0", m_cls="personal", retr_st="null"
      )

      with open('data/' + str(row['id']) + '/_Smil.smil_', 'rb') as smilfile:
        smil_data = smilfile.read().decode(encoding="ascii")
      smilpart = Part()
      smil_parsed = dict(
        seq = "-1", ct = "application/smil", name="Smil.smil", chset="106", cd="null", fn="null", cid="<Smil.smil>", cl="null", ctt_s="null", ctt_t="null", text=smil_data
      )
      for key in smil_parsed:
        smilpart[key] = smil_parsed[key]
      msg.add_part(smilpart)

      smilhandler = SmilHandler('data/' + str(row['id']))
      parser = XMLParser(target=smilhandler)
      parser.feed(smil_data)
      try:
        attachment_parts = parser.close()
      except ParseError:
        warnings.warn("Could not parse SMIL file for msg {}".format(str(row['id'])))
        continue
      for a_p in attachment_parts:
        msg.add_part(a_p)

      msg.add_addr(AddressType.FROM, row['remoteUid'])
      for to in re.findall(r"x-mms-to.(\+[0-9]+)", row['headers']):
        msg.add_addr(AddressType.TO, to)
      for cc in re.findall(r"x-mms-cc.(\+[0-9]+)", row['headers']):
        msg.add_addr(AddressType.CC, cc)
      for bcc in re.findall(r"x-mms-bcc.(\+[0-9]+)", row['headers']):
        msg.add_addr(AddressType.BCC, bcc)
    for key in parsed:
      msg[key] = parsed[key]
    ret.append(msg)
  return ret

def _call_type(direction, is_missed, start_time, end_time):
  if direction != 1 and direction != 2:
    raise RuntimeError("Unknown commhistory direction {}".format(direction))
  if is_missed:
    return CallType.MISSED
  elif direction == 2:
    return CallType.OUTGOING
  elif start_time == end_time:
    return CallType.REJECTED
  else:
    return CallType.INCOMING

def _handle_calls(cursor):
  ret = []
  for row in cursor.execute("SELECT id, type, startTime, endTime, direction, isMissedCall, remoteUid FROM Events WHERE type = 3"):
    call = Call()

    parsed = dict(
      date = str(row['startTime']) + '000',
      duration = row['endTime'] - row['startTime'],
      type = _call_type(row['direction'], row['isMissedCall'], row['startTime'], row['endTime']),
      number = row['remoteUid'] or "",
      presentation = NumberPresentation.RESTRICTED if ((not row['remoteUid']) or (not any(char.isdigit() for char in row['remoteUid'])) ) else NumberPresentation.ALLOWED
    )

    for key in parsed:
      call[key] = parsed[key]
    ret.append(call)

  return ret

class CommhistoryParser():
  @staticmethod
  def parse(srcfile, sms_list = None, call_list =  None):
    if (sms_list == None and call_list == None):
      raise ValueError("Must specify at least one collection")

    tempfilename = None
    conn = None
    cur = None
    try:
      with NamedTemporaryFile(delete=False) as tempfile:
        tempfilename = tempfile.name
        copyfileobj(srcfile, tempfile)

      conn = sqlite3.connect(tempfilename)
      conn.row_factory = sqlite3.Row
      cur = conn.cursor()
      if sms_list:
        sms_list.extend(_handle_smses(cur))
      if call_list:
        call_list.extend(_handle_calls(cur))
    finally:
      if cur:
        cur.close()
      if conn:
        conn.close()
      if tempfilename:
        unlink(tempfilename)
