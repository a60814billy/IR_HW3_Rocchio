__author__ = 'raccoon'

import sgm_parser.parser
from indexing.index import Index
from buildindex import BuildIndex
import os


class TopicIndex:
    """
    :type topic: dict
    """
    training_topics = {}
    testing_topics = {}

    def add_training_doc(self, topic, doc_id):
        if topic not in self.training_topics:
            self.training_topics[topic] = []
            self.training_topics[topic].append(doc_id)
        else:
            self.training_topics[topic].append(doc_id)

    def add_testing_doc(self, topic, doc_id):
        if topic not in self.testing_topics:
            self.testing_topics[topic] = []
            self.testing_topics[topic].append(doc_id)
        else:
            self.testing_topics[topic].append(doc_id)

    def dump(self, filename: str):
        f = open(filename + ".topics.train.idx", "w")
        for i in self.training_topics:
            content = i + " "
            for doc_id in self.training_topics[i]:
                content += str(doc_id) + ", "
            content = content[:-2] + "\n"
            f.write(content)
        f.close()

        f = open(filename + ".topics.test.idx", "w")
        for i in self.testing_topics:
            content = i + " "
            for doc_id in self.testing_topics[i]:
                content += str(doc_id) + ", "
            content = content[:-2] + "\n"
            f.write(content)
        f.close()


def main():
    """
    :type records: list[sgm_parser.record.Record]
    :return:
    """

    # setup build parameter
    BuildIndex.case_folding = True
    BuildIndex.stemming = True
    BuildIndex.stopword_remove = True
    BuildIndex.saving_partial_index = True
    BuildIndex.partial_index_path = os.path.abspath("./reuters_pi/") + "/"

    reuters_index = Index()
    topic_index = TopicIndex()

    if not (os.path.isfile('reuters21578.idx') and os.path.isfile('reuters21578.dict') and os.path.isfile(
            'reuters21578topics.train.idx')):
        # read all reuters sgm file
        file = "./reuters21578/reut2-"
        records = []
        # read 22 seg file, and extra article to records array
        for i in range(0, 22):
            file_name = file + "{0:0=3d}".format(i) + ".sgm"
            print("Parse {0} sgm file".format(i))
            partial_records = sgm_parser.parser.parse_file(file_name)
            print("{0} sgm file contain {1} documents".format(i, len(partial_records)))
            records += partial_records
        print("count of documents is {0}".format(len(records)))

        for record in records:
            # do record level indexing
            print("indexing OLD:{0} document".format(record.oldid))
            idx = BuildIndex()
            idx.process_content(record.contents)
            # dump partial index to file
            idx.dump(record.oldid)
            # add partial index to all document collection index
            reuters_index.read_partial_index(record.oldid, idx.index)
            # according to the topic to split training data and testing data
            for topic in record.topics:
                if record.is_training:
                    topic_index.add_training_doc(topic, record.oldid)
                elif record.is_testing:
                    topic_index.add_testing_doc(topic, record.oldid)
        # dump document collection index
        reuters_index.dump("reuters21578")
        # dump training and testing topics index to file
        topic_index.dump("reuters21578")
    else:
        print("reading index file.")
        reuters_index.read("reuters21578.idx")

    print(len(reuters_index.index))


if __name__ == '__main__':
    main()
