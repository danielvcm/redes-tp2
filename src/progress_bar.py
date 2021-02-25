import sys
import math

class ProgressBar:
    def __init__(self, total_tasks, bar_size=40) -> None:
        self.total_tasks = total_tasks
        self.bar_size = bar_size
        self.tasks_done = 0
        self.tags_printed = 0
        self.tag_size = total_tasks / bar_size
    
    def init_print(self):
        # setup toolbar
        sys.stdout.write("[%s]" % (" " * self.bar_size))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self.bar_size+1)) # return to start of line, after '['

    def end_print(self):
        if self.tags_printed < self.bar_size:
            tags_to_print = self.bar_size - self.tags_printed
            self.print_tags(tags_to_print)
        sys.stdout.write("]\n")

    def print_tags(self, tags_to_print):
        sys.stdout.write("#"*tags_to_print)
        sys.stdout.flush()
    
    def increase(self, number_of_tasks = 1):
        self.tasks_done+=number_of_tasks
        new_number_tags = math.floor(self.tasks_done/self.tag_size)
        if new_number_tags > self.tags_printed:
            tags_to_print = new_number_tags-self.tags_printed
            self.print_tags(tags_to_print)
            self.tags_printed+=tags_to_print
        