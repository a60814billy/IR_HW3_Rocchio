__author__ = 'raccoon'

import gzip
from .partial_index import PartialIndex


class Index:
    index = {}

    def read_partial_index(self, doc_id: int, pi: PartialIndex):
        for i in pi.index:
            if i not in self.index:
                self.index[i] = {}
            self.index[i][doc_id] = pi.index[i]

    def dump(self, filename: str):
        f = open(filename + ".idx", "w")
        fdic = open(filename + ".dict", "w")
        for k, v in ((k, self.index[k]) for k in sorted(self.index)):
            fdic.write(k + ", " + str(f.tell()) + "\n")
            f.write(k + ", " + str(len(v)) + ":<")
            for doc in v:
                f.write(str(doc) + ", " + str(len(v[doc])) + ":<")
                fr = True
                for pos in v[doc]:
                    if fr:
                        f.write(str(pos))
                        fr = False
                    else:
                        f.write(", " + str(pos))
                f.write(">;")
            f.write(">;\n")
        f.close()
        fdic.close()

    def dump_gzip(self, filename: str):
        f = gzip.open(filename + ".idx.gz", "w")
        fdic = gzip.open(filename + ".dict.gz", "w")
        for k, v in ((k, self.index[k]) for k in sorted(self.index)):
            fdic.write(bytes(k + "\n", "utf8"))
            f.write(bytes(k + ", " + str(len(v)) + ":<", "utf8"))
            for doc in v:
                f.write(bytes(str(doc) + ", " + str(len(v[doc])) + ":<", "utf8"))
                fr = True
                for pos in v[doc]:
                    if fr:
                        f.write(bytes(str(pos), "utf8"))
                        fr = False
                    else:
                        f.write(bytes(", " + str(pos), "utf8"))
                f.write(bytes(">;", "utf8"))
            f.write(bytes(">;\n", "utf8"))
        f.close()
        fdic.close()

    @staticmethod
    def read(filename):
        """
        read plain text index file to partial index
        :param filename:
        :return:
        """
        f = open(filename, "r")
        lines = f.readlines()
        index = Index()
        for line in lines:
            (key, posting_list) = line.split(",", maxsplit=1)
            docs = posting_list[posting_list.find(":") + 2:-4].split(";")
            for doc in docs:
                pi = PartialIndex()
                (docId, position) = doc.split(",", maxsplit=1)
                positions = position[position.find(":") + 2:-1].split(",")
                for pos in positions:
                    pi.push(key, int(pos))
                index.read_partial_index(docId, pi)
        return index

    @staticmethod
    def parse_posting_entry(entry):
        index = Index()
        (key, posting_list) = entry.split(",", maxsplit=1)
        docs = posting_list[posting_list.find(":") + 2:-4].split(";")
        for doc in docs:
            pi = PartialIndex()
            (docId, position) = doc.split(",", maxsplit=1)
            positions = position[position.find(":") + 2:-1].split(",")
            for pos in positions:
                pi.push(key, int(pos))
            index.read_partial_index(docId, pi)
        return index

    @staticmethod
    def read_index_by_offset(filename, offset):
        f = open(filename, "r")
        f.seek(offset)
        line = f.readline()
        return Index.parse_posting_entry(line)

