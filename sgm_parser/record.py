__author__ = 'raccoon'


class Record():
    is_training = False
    is_testing = False
    oldid = 0
    title = ""
    contents = ""
    topics = None

    def __init__(self):
        self.is_training = False
        self.is_testing = False
        self.oldid = 0
        self.title = ""
        self.contents = ""
        self.topics = []
