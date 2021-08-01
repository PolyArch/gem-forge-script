import Utils.StreamMessage_pb2 as StreamMesssage_pb2
import sys
import os

from google.protobuf.internal.decoder import _DecodeVarint32


class StreamFloatTraceReader(object):
    def __init__(self, fn):
        with open(fn, 'rb') as f:
            self.buf = f.read()
        self.pos = 0
        self.length = len(self.buf)

        # Skip the magic number.
        self.pos += 4

    def parseNext(self):
        if self.pos >= self.length:
            return None
        size, self.pos = _DecodeVarint32(self.buf, self.pos)
        msg = StreamMesssage_pb2.StreamFloatEvent()
        msg.ParseFromString(self.buf[self.pos:self.pos + size])

        self.pos += size

        return msg


def collectTrace(fn):
    parser = StreamFloatTraceReader(fn)

    count = 0
    events = list()
    while True:
        msg = parser.parseNext()
        if msg is None:
            break

        count += 1
        events.append(msg)
    return events

def collectAllTraces(folder, keyword=None):
    all_events = list()
    for f in os.listdir(folder):
        if keyword and keyword not in f:
            continue
        full_fn = os.path.join(folder, f)
        if os.path.isfile(full_fn):
            print(f'Reading {f}')
            all_events += collectTrace(full_fn)
    return all_events

def collectStreamChangesForBank(all_events, bank):
    bank_events = [e for e in all_events if e.llc_bank == bank]
    current_streams = 0
    stream_changes = list()
    for e in bank_events:
        new_streams = current_streams
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.MIGRATE_IN:
            new_streams += 1
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.CONFIG:
            new_streams += 1
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.MIGRATE_OUT:
            new_streams -= 1
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.END:
            new_streams -= 1
        if new_streams != current_streams:
            stream_changes.append((e.cycle, new_streams))
            current_streams = new_streams
    return stream_changes


def dumpAliveStreams(folder, keyword=None):
    all_events = collectAllTraces(folder, keyword)
    all_events.sort(key=lambda x: x.cycle)
    base_folder = os.path.basename(os.path.basename(os.path.basename(folder)))
    with open(f'{base_folder}-llc-{keyword if keyword else "all"}-streams-timeline.csv', 'w') as f:
        max_streams = list()
        for bank in range(0, 64, 1):
            f.write(f'bank{bank}\n')
            stream_changes = collectStreamChangesForBank(all_events, bank)
            max_streams.append(max(x[1] for x in stream_changes))
            for c in stream_changes:
                f.write(f'{c[0]},')
            f.write('\n')
            for c in stream_changes:
                f.write(f'{c[1]},')
            f.write('\n')
        for bank in range(len(max_streams)):
            f.write(f'{bank},')
        f.write('\n')
        for bank in range(len(max_streams)):
            f.write(f'{max_streams[bank]},')
        f.write('\n')


def main(argv):
    folder = argv[1]
    keyword = None
    if len(argv) > 2:
        keyword = argv[2]
    dumpAliveStreams(folder, keyword)


if __name__ == '__main__':
    main(sys.argv)

