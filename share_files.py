import c_builder
import yaml


class thread:
    def __init__(self,name, exempt, priority=0, can_interrupt_same_priority=True):
        self.name = name
        self.exempt = exempt
        self.priority = priority
        self.can_interrupt_same_priority = can_interrupt_same_priority

    def can_interrupt(self, other):
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



def main(name):

    with open("test.yaml") as f:
        json_struct = yaml.load(f)

    print json_struct
    threads = []
    for item in json_struct["threads"]["cannot_be_disabled"]:
        threads.append(thread(item, True))
    for priority in json_struct["threads"]["other"]:
        for item in priority["threads"]:
            threads.append(thread(item, False, priority["priority"], priority["can_interrupt_each_other"]))







if __name__ == '__main__':
    main("test.json")