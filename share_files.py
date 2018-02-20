import c_builder
import yaml


class thread:
    '''

    the thread class classifies threads based on whether they can interrupt each other.

    '''
    def __init__(self, name, exempt, priority=0, can_interrupt_same_priority=True):
        """
        :str name: name of the thread or process
        :bool exempt: true if this thread is exempt from critical sections / mutexes
        :int priority: numerical priority, lower numbers can interrupt higher numbers.
        :bool can_interrupt_same_priority: true if everything in the same priority list can interrupt each other

        :rtype: thread object
        """
        self.name = name
        self.exempt = exempt
        self.priority = priority
        self.can_interrupt_same_priority = can_interrupt_same_priority

    def can_interrupt(self, other):
        '''
        :thread other:
        :return: True if this thread can run when the other thread is running either by taking context or by running concurrently
        '''
        if self.exempt:
            return True
        if other.exempt:
            return False
        if self.priority < other.priority:
            return True
        if self.priority == other.priority and self.can_interrupt_same_priority:
            return True
        return False
    def can_be_interrupted_by(self, other):
        return other.can_interrupt(self)

    def __str__(self):
        return "n:" + self.name
        #+ " e:" + str(self.exempt) + " p:" + str(self.priority) + " can interrupt =:" + str(self.can_interrupt_same_priority)

def generate_file(file_parameters):
    pass

def main(name):
    #get the user paramaters
    with open(name) as f:
        json_struct = yaml.load(f)


    print json_struct
    threads = []
    for item in json_struct["threads"]["cannot_be_disabled"]:
        threads.append(thread(item, True))
    for priority in json_struct["threads"]["other"]:
        for item in priority["threads"]:
            threads.append(thread(item, False, priority["priority"], priority["can_interrupt_each_other"]))


    fs = json_struct["share_files"]
    structs = fs["structs"]
    for s in structs:
        s["reader_objs"] = [t for t in threads if t.name in s["readers"]]
        print s["reader_objs"]
        print s["readers"]


        assert len(s["reader_objs"]) == len(s["readers"]), \
            "at least one item in readers is not defined in the threads section"

        s["writer_objs"] = [t for t in threads if t.name in s["writers"]]
        assert len(s["writer_objs"]) == 1, \
            "the writer is not properly defined in the structs or threads section"

        s["read_copies"] = [t.name for t in s["reader_objs"] if s["writer_objs"][0].can_interrupt(t)]


        if (any([t for t in s["reader_objs"] if s["writer_objs"][0].can_be_interrupted_by(t)])) or \
                s.get("scratchpad",False):
            s["read_copies"].append("newest")

        s["all_copies"] = s["read_copies"] + ["write"]
        s["writer_names"] = [t.name for t in s["writer_objs"]]
        s["index_names"] = list(set(s["writer_names"]+ s["all_copies"] + ["newest"]))
        print s["all_copies"]
        print s["read_copies"]
        print s["index_names"]

        generate_file(fs)






if __name__ == '__main__':
    main("test.yaml")
