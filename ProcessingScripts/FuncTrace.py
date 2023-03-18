
import os
import sys

if len(sys.argv) > 1:
    folder = sys.argv[1]
else:
    folder = '.'

def get_cpu_id(fn):
    prefix = 'ftrace.system.future_cpus'
    return int(fn[len(prefix):])

class Event:
    def __init__(self, cur_cycle, acc_cycle, func_name, cpu_id):
        self.cur_cycle = cur_cycle
        self.acc_cycle = acc_cycle
        self.func_name = func_name
        self.cpu_id = cpu_id

def parse_line(line, cpu_id):
    lhs, rhs = line.split(': ')
    cur_cycle, acc_cycle = [int(x) for x in lhs.split('-')]
    func_name = rhs[:-1]
    return Event(cur_cycle, acc_cycle, func_name, cpu_id)

def process_trace(fn, cpu_id):
    events = list()
    with open(fn) as f:
        for line in f:
            try:
                events.append(parse_line(line, cpu_id))
            except:
                print(line)
    return events


for fn in os.listdir(folder):
    if not fn.startswith('ftrace.system.future_cpus'):
        continue
    print(fn)
    cpu_id = get_cpu_id(fn)
    events = process_trace(os.path.join(folder, fn), cpu_id)
    for event in events:
        if event.func_name == '.omp_outlined..26' and event.acc_cycle >= 100:
            print(f'>> {event.func_name} {cpu_id} {event.cur_cycle} {event.acc_cycle}')