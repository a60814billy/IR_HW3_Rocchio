__author__ = 'raccoon'

from .record import Record
from html.parser import HTMLParser
import os


class SGMParser(HTMLParser):
    """
    :type tmp_record: sgm_parser.record.Record
    """
    records = []
    tmp_record = None
    # used to identify which data is in tag scope,
    # beacuse use last tag, can make some mistake
    in_reuters_section = False
    in_title_section = False
    in_topics_section = False
    in_body_section = False
    new_id = 0

    def __init__(self):
        HTMLParser.__init__(self)
        # let HTMLParser convert HTML Entity name to normal character,
        # see HTMLParser source code in https://hg.python.org/cpython/file/3.4/Lib/html/parser.py
        # about convert_charrefs
        self.convert_charrefs = True
        self.records = []

    def handle_starttag(self, tag, attrs):
        if tag == 'reuters':
            self.tmp_record = Record()
            self.in_reuters_section = True
            for name, value in attrs:
                if name == 'lewissplit':
                    if value == 'TRAIN':
                        self.tmp_record.is_training = True
                    elif value == 'TEST':
                        self.tmp_record.is_testing = True
                elif name == 'oldid':
                    self.tmp_record.oldid = int(value)

        elif tag == 'title':
            self.in_title_section = True
        elif tag == 'topics':
            self.in_topics_section = True
        elif tag == 'text':
            self.in_body_section = True

    def handle_endtag(self, tag):
        if tag == 'reuters':
            self.records.append(self.tmp_record)
            self.tmp_record = None
            self.in_reuters_section = False
        elif tag == 'title':
            self.in_title_section = False
        elif tag == 'topics':
            self.in_topics_section = False
        elif tag == 'text':
            self.in_body_section = False

    def handle_data(self, data):
        if self.in_title_section:
            self.tmp_record.title = data
        elif self.in_body_section:
            self.tmp_record.contents += " " + data
        elif self.in_topics_section:
            self.tmp_record.topics.append(data)


def parse_file(file):
    import os
    if os.path.isfile(file):
        flines = open(file, encoding='iso-8859-1').readlines()
        contents = "".join(flines)
        sgm = SGMParser()
        sgm.feed(contents)
        return sgm.records
    else:
        return []


def unitest():
    file_path = os.path.dirname(os.path.abspath(__file__))
    test_data_path = os.path.abspath(file_path + "/../reuters21578/reut2-000.sgm")
    flines = open(test_data_path).readlines()
    contents = "".join(flines)
    sgm_parser = SGMParser()
    sgm_parser.feed(contents)

    records = sgm_parser.records

    for record in records:
        if record.is_training:
            print(record.oldid, record.is_training, record.topics)


if __name__ == "__main__":
    unitest()
