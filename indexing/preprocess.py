__author__ = 'raccoon'

import re


def split_word(content):
    return re.split('<|>|,|-|/|=|"|\'|;|#|\(|\)|\.|:|\d|\||\{|\}|%|_|!|@|	|&|\n|\r|\s*}', content.replace('\n' , ''))
