from sbr.elements import MessageBox

def get_parser(filename):
  if filename.endswith(".db"):
    from parsers.commhistory_parser import CommhistoryParser
    return CommhistoryParser()
  else:
    raise ValueError('File type not recognized for parsing')
