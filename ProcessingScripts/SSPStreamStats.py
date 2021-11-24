"""
Simple process script to process stream.
"""

import os

class SingleStreamStat(object):
    def __init__(self, name):
        self.name = name
        self.stats = dict()

    def add_line(self, line):
        fields = [x for x in line.split(' ') if len(x) > 0]
        if len(fields) == 2:
            field, value = fields
            if field not in self.stats:
                self.stats[field] = list()
            self.stats[field].append(float(value))

    def get_avg(self, field):
        if field not in self.stats:
            print(f'{field} not in stream {self.name}')
            assert(False)
        values = self.stats[field]
        print(values)
        print(f'min {min(values)} avg {sum(values) / len(values)}')
        return sum(values) / len(values)

class AllStreamStat(object):
    def __init__(self):
        self.stream_stats = dict()

    def add_file(self, fn):
        with open(fn) as f:
            current_stat = None
            for line in f:
                line = line[:-1]
                if line.startswith(' '):
                    assert(current_stat is not None)
                    current_stat.add_line(line)
                else:
                    stream_name = line
                    if stream_name not in self.stream_stats:
                        self.stream_stats[stream_name] = SingleStreamStat(stream_name)
                    current_stat = self.stream_stats[stream_name]

    def print_stream_avg(self, stream_name, field):
        if stream_name not in self.stream_stats:
            print(f'{stream_name} not found')
            assert(False)
        stream_stat = self.stream_stats[stream_name]
        avg_value = stream_stat.get_avg(field)
        print(f'{stream_name} avg {field} {avg_value}')

def main():
    core_id = 0
    all_stat = AllStreamStat()
    while True:
        stream_stats_fn = f'stream.stats.{core_id}.txt'
        core_id += 1
        if not os.path.isfile(stream_stats_fn):
            break
        all_stat.add_file(stream_stats_fn)

    all_stat.print_stream_avg('gap.pr_push.atomic.out_v.ld', 'avgNumDynStreams')
        

if __name__ == '__main__':
    main()