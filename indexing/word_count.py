__author__ = 'raccoon'


class WordCount:
    word_dist = {}

    def push(self, word, value=1):
        if word in self.word_dist:
            self.word_dist[word] += value
        else:
            self.word_dist[word] = value

    def get_dict(self):
        exp = ((k, self.word_dist[k]) for k in sorted(self.word_dist, key=self.word_dist.get, reverse=True))
        dc = {}
        for k, v in exp:
            dc[k] = v
        return dc