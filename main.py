__author__ = 'raccoon'

import os
import math
import time

import sgm_parser.parser
from indexing.index import Index
from buildindex import BuildIndex
from indexing.partial_index import PartialIndex

CURSOR_UP_ONE = "\x1b[1A"
CURSOR_DOWN_ONE = "\x1b[1B"
ERASE_LINE = "\x1b[K"
CLEAR_SCREEN = "\x1b[1J"
SPLIT_LINE_LENGTH = 60


def cli_control(code):
    print(code, end='')


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

    @staticmethod
    def read(filename):
        topic_index = TopicIndex()
        lines = open(filename + ".topics.train.idx", 'r').readlines()
        for line in lines:
            r = line.split(" ", maxsplit=1)
            topic = r[0]
            l = r[1].split(", ")
            for doc in l:
                topic_index.add_training_doc(topic.strip(), int(doc))
        lines = open(filename + ".topics.test.idx", 'r').readlines()
        for line in lines:
            r = line.split(" ", maxsplit=1)
            topic = r[0]
            l = r[1].split(", ")
            for doc in l:
                topic_index.add_testing_doc(topic.strip(), int(doc))
        return topic_index


class Rocchio:
    """
    :type dc_index: indexing.index.Index
    """
    dc_index = None
    reuters_pi_path = "./"

    topic_class_centroid = {}
    topic_class_centroid_magnitude = {}
    topic_class_info = {}

    def __init__(self, dci):
        self.dc_index = dci
        pass

    def training(self, topic, doc_ids):
        if topic not in self.topic_class_centroid:
            self.topic_class_centroid[topic] = {}
            self.topic_class_centroid_magnitude[topic] = 0
            self.topic_class_info[topic] = {}
            self.topic_class_info[topic]["train"] = len(doc_ids)
            self.topic_class_info[topic]["test"] = 0
            self.topic_class_info[topic]["TP"] = 0
            self.topic_class_info[topic]["FP"] = 0
            self.topic_class_info[topic]["TN"] = 0
            self.topic_class_info[topic]["FN"] = 0

        for doc_id in doc_ids:
            # print("Read doc:{0} partial index".format(doc_id))
            file_path = self.reuters_pi_path + str(doc_id) + ".idx"
            if os.path.isfile(file_path):
                doc_pi = PartialIndex.read(file_path)
                for term in doc_pi.index:
                    if term not in self.topic_class_centroid[topic]:
                        self.topic_class_centroid[topic][term] = (1 + math.log(len(doc_pi.index[term]))) * math.log(
                            21578 / len(self.dc_index.index[term]))
                    else:
                        self.topic_class_centroid[topic][term] += (1 + math.log(len(doc_pi.index[term]))) * math.log(
                            21578 / len(self.dc_index.index[term]))
            else:
                Exception("can't read partial idx file in {0} doc".format(doc_id))
                # print("Centroid vector: ", self.topic_class_centroid[topic])
        sqare_sum = 0
        for term in self.topic_class_centroid[topic]:
            sqare_sum += self.topic_class_centroid[topic][term]
        for term in self.topic_class_centroid[topic]:
            self.topic_class_centroid[topic][term] = self.topic_class_centroid[topic][term] / sqare_sum

    def apply_test(self, doc_id, real_class):
        if real_class not in self.topic_class_info:
            self.topic_class_info[real_class] = {}
            self.topic_class_info[real_class]["train"] = 0
            self.topic_class_info[real_class]["test"] = 0
            self.topic_class_info[real_class]["TP"] = 0
            self.topic_class_info[real_class]["FP"] = 0
            self.topic_class_info[real_class]["TN"] = 0
            self.topic_class_info[real_class]["FN"] = 0
        file_path = self.reuters_pi_path + str(doc_id) + ".idx"
        result_vector = {}
        result = 0
        square_sum = 0
        magnitude = 0
        if os.path.isfile(file_path):
            doc_pi = PartialIndex.read(file_path)
            doc_vec = {}
            for term in doc_pi.index:
                doc_vec[term] = (1 + math.log(len(doc_pi.index[term]))) * math.log(21578 / len(self.dc_index.index[term]))
                # doc_vec[term] = len(doc_pi.index[term])
                square_sum += doc_vec[term] * doc_vec[term]
            for term in doc_vec:
                doc_vec[term] = doc_vec[term] / square_sum

            for topic in self.topic_class_centroid:
                result = 0
                for term in doc_vec:
                    if term in self.topic_class_centroid[topic]:
                        result += doc_vec[term] * self.topic_class_centroid[topic][term]
                result_vector[topic] = result

            for first_class in sorted(result_vector, key=result_vector.get, reverse=True):
                # print("doc_id apply result = ", first_class, " real_result is ", real_class, "score = ",
                #       str(result_vector[first_class]))
                if first_class == real_class:
                    self.topic_class_info[first_class]["test"] += 1
                    self.topic_class_info[first_class]["TP"] += 1
                else:
                    self.topic_class_info[first_class]["test"] += 1
                    self.topic_class_info[first_class]["FP"] += 1
                    self.topic_class_info[real_class]["FN"] += 1
                break


def main():
    """
    :type records: list[sgm_parser.record.Record]
    :return:
    """

    # setup build parameter
    BuildIndex.case_folding = True
    BuildIndex.stemming = False
    BuildIndex.stopword_remove = True
    BuildIndex.saving_partial_index = True
    BuildIndex.partial_index_path = os.path.abspath("./reuters_pi/") + "/"

    program_start = time.time()

    reuters_index = Index()
    topic_index = TopicIndex()

    if not (os.path.isfile('reuters21578.idx') and os.path.isfile('reuters21578.dict') and os.path.isfile(
            'reuters21578.topics.train.idx')):
        # read all reuters sgm file
        file = "./reuters21578/reut2-"
        records = []
        # read 22 seg file, and extra article to records array
        start_read_time = time.time()
        print("-" * SPLIT_LINE_LENGTH)
        print("Starting read all reuters records......")
        for i in range(0, 22):
            file_name = file + "{0:0=3d}".format(i) + ".sgm"
            print("Parse {0} sgm file".format(i))
            partial_records = sgm_parser.parser.parse_file(file_name)
            print("{0} sgm file contain {1} documents".format(i, len(partial_records)))
            records += partial_records
            cli_control(CURSOR_UP_ONE)
            cli_control(CURSOR_UP_ONE)
        cli_control(CURSOR_DOWN_ONE)
        cli_control(ERASE_LINE)
        print("total # of documents is {0}".format(len(records)))
        print("spend {}s".format(time.time() - start_read_time))
        print("-" * SPLIT_LINE_LENGTH)
        print("Starting index all article......")
        start_index_article_time = time.time()
        cli_control(CURSOR_DOWN_ONE)
        for record in records:
            # do record level indexing
            cli_control(CURSOR_UP_ONE)
            cli_control(ERASE_LINE)
            print("indexing OLD: {0} document".format(record.oldid))
            idx = BuildIndex()
            idx.process_content(record.title + " " + record.contents)
            # dump partial index to file
            idx.dump(record.oldid)
            # add partial index to all document collection index
            reuters_index.read_partial_index(record.oldid, idx.index)
            # according to the topic to split training data and testing data
            # in there, take the first one topic as document topic
            for topic in record.topics:
                if record.is_training:
                    topic_index.add_training_doc(topic, record.oldid)
                elif record.is_testing:
                    topic_index.add_testing_doc(topic, record.oldid)
                # break
        cli_control(CURSOR_DOWN_ONE)
        print("Saving index to file......")
        # dump document collection index
        reuters_index.dump("reuters21578")
        # dump training and testing topics index to file
        topic_index.dump("reuters21578")
        print("spend {}s".format(time.time() - start_index_article_time))
        print("-" * SPLIT_LINE_LENGTH)
    else:
        print("-" * SPLIT_LINE_LENGTH)
        print("Read reuters index file......")
        start_read_index_time = time.time()
        reuters_index.read("reuters21578.idx")
        topic_index = TopicIndex.read("reuters21578")
        print("spend {}s".format(time.time() - start_read_index_time))
        print("-" * SPLIT_LINE_LENGTH)

    classfi = Rocchio(reuters_index)
    classfi.reuters_pi_path = os.path.abspath("./reuters_pi/") + "/"

    print("Starting processing training data......")
    start_processing_training_data = time.time()
    for train_topic in topic_index.training_topics:
        cli_control(ERASE_LINE)
        print("training topic:{}".format(train_topic))
        cli_control(CURSOR_UP_ONE)
        classfi.training(train_topic, topic_index.training_topics[train_topic])
    cli_control(CURSOR_DOWN_ONE)
    print("spend {}s".format(time.time() - start_processing_training_data))
    print("-" * SPLIT_LINE_LENGTH)

    print("Starting processing testing data......")
    start_processing_testing_data = time.time()
    for test_topic in topic_index.testing_topics:
        for doc in topic_index.testing_topics[test_topic]:
            print("Apply Test doc#{} in topic {}".format(doc, test_topic))
            classfi.apply_test(doc, test_topic)
            cli_control(CURSOR_UP_ONE)
            cli_control(ERASE_LINE)
    cli_control(CURSOR_DOWN_ONE)
    print("spend {}s".format(time.time() - start_processing_testing_data))
    print("-" * SPLIT_LINE_LENGTH)


    # caculator FN TN

    print(
        "{:<15} {:>5} {:>5} {:>5} {:>5} {:>5} {:>9} {:>9}".format("class name", "train", "test", "TP", "FP", "FN",
                                                                  "Precision",
                                                                  "Recall"))

    top10_P = 0
    top10_R = 0
    avg_P = 0
    avg_R = 0

    i = 0
    for topic in sorted(classfi.topic_class_info, key=lambda x: classfi.topic_class_info[x]['train'], reverse=True):
        if classfi.topic_class_info[topic]["TP"] == 0 and classfi.topic_class_info[topic]["FP"] == 0:
            p = 1
        else:
            p = classfi.topic_class_info[topic]["TP"] / (
                classfi.topic_class_info[topic]["TP"] + classfi.topic_class_info[topic]["FP"])

        if classfi.topic_class_info[topic]["TP"] == 0 and classfi.topic_class_info[topic]["FN"] == 0:
            r = 1
        else:
            r = classfi.topic_class_info[topic]["TP"] / (
                classfi.topic_class_info[topic]["TP"] + classfi.topic_class_info[topic]["FN"])

        if i < 10:
            top10_R += r
            top10_P += p
        avg_R += r
        avg_P += p
        i += 1

        print("{:<15} {:>5} {:>5} {:>5} {:>5} {:>5} {:>8.1%} {:>8.1%}".format(topic,
                                                                              classfi.topic_class_info[topic]["train"],
                                                                              classfi.topic_class_info[topic]["test"],
                                                                              classfi.topic_class_info[topic]["TP"],
                                                                              classfi.topic_class_info[topic]["FP"],
                                                                              classfi.topic_class_info[topic]["FN"], p,
                                                                              r))

    print("Precision (top 10 class) average: {:>8.1%}".format(top10_P / 10))
    print("Recall (top 10 class) average: {:>8.1%}".format(top10_R / 10))

    print("Precision average: {:>8.1%}".format(avg_P / i))
    print("Recall average: {:>8.1%}".format(avg_R / i))

    print("-" * SPLIT_LINE_LENGTH)
    print("program finish, total execute time: {:3.2n}s".format(time.time() - program_start))


if __name__ == '__main__':
    main()
