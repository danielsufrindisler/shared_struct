import c_builder
import yaml
import generate_struct
import sys



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
        if self == other:
            return False
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


class struct:
    def __init__(self, name, header, parsing, read_copies, read_threads, all_copies, all_ptrs):
        """
        :str name: name of the thread or process
        :bool exempt: true if this thread is exempt from critical sections / mutexes
        :int priority: numerical priority, lower numbers can interrupt higher numbers.
        :bool can_interrupt_same_priority: true if everything in the same priority list can interrupt each other

        :rtype: thread object
        """
        self.name = name
        self.header_which_defines_struct = header
        self.parsing = parsing
        self.read_copies = read_copies
        self.read_threads = read_threads
        self.all_copies = all_copies
        self.all_ptrs = all_ptrs



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

    sf = json_struct["share_files"]
    structs = sf["structs"]
    s_objs = []  #list of class struct
    for s in structs:

        s["reader_objs"] = [t for t in threads if t.name in s["readers"]]

        assert len(s["reader_objs"]) == len(s["readers"]), \
            "at least one item in readers is not defined in the threads section"

        s["writer_objs"] = [t for t in threads if t.name in s["writers"]]
        assert len(s["writer_objs"]) == 1, \
            "the writer is not properly defined in the structs or threads section"

        s["read_copies"] = [t.name for t in s["reader_objs"] if s["writer_objs"][0].can_interrupt(t)]
        s["read_threads"] = [t.name for t in s["reader_objs"]]

        if (any([t for t in s["reader_objs"] if s["writer_objs"][0].can_be_interrupted_by(t)])) or \
                s.get("scratchpad",False):
            s["read_copies"].append("newest")

        s["all_copies"] = s["read_copies"] + ["write"]
        s["writer_names"] = [t.name for t in s["writer_objs"]]
        s["index_names"] = list(set(s["writer_names"]+ s["all_copies"] + ["newest"]))


        s_objs.append( struct(s["name"], s["header"], False, s["read_copies"], s["read_threads"],
                              s["all_copies"], s["index_names"]))

    generate_struct.create_files(sf["output_path"], sf["prefix"], sf["c_extension"], sf["h_extension"], \
                                 sf["preamble"], sf["critical_enter"], sf["critical_exit"], sf["includes"], \
                                 json_struct["threads"]["get_thread_function"],threads, s_objs)
    print "files created successfully"
    return 0


if __name__ == '__main__':
    main(sys.argv[1])
