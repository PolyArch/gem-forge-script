import Utils.StreamMessage_pb2 as StreamMesssage_pb2
import sys
import os
import argparse

from google.protobuf.internal.decoder import _DecodeVarint32

parser = argparse.ArgumentParser(
    prog = 'Read StreamFloatTrace')

parser.add_argument('folder')           # positional argument
parser.add_argument('--interval', '-i',
    type=int, default=10,
    help='Interval in cycles to merge event')      # option that takes a value
parser.add_argument('--keyword', '-k',
    type=str, default=None,
    help='Keyword to filter out traces')      # option that takes a value

args = parser.parse_args()

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
        if size + self.pos > self.length:
            # we have truncated message.
            return None
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
    min_cycle = 1000000000000000
    for f in os.listdir(folder):
        if keyword and keyword not in f:
            continue
        full_fn = os.path.join(folder, f)
        if os.path.isfile(full_fn):
            print(f'Reading {f}')
            events = collectTrace(full_fn)
            if events:
                min_cycle = min(min_cycle, events[0].cycle)
            all_events += events
    for e in all_events:
        e.cycle -= min_cycle
    return all_events

def alignCycleToInterval(cycle):
    return cycle - cycle % args.interval

def addEventToStreamChanges(e, current_streams, stream_changes):
    align_interval = alignCycleToInterval(e.cycle)
    new_streams = current_streams
    if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.MIGRATE_IN:
        new_streams += 1
    elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.CONFIG:
        new_streams += 1
    elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.MIGRATE_OUT:
        new_streams -= 1
    elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.END:
        new_streams -= 1
    if new_streams != current_streams:
        merged = False
        if stream_changes:
            prev_interval = stream_changes[-1][0]
            # Skip change if cycle is within 10 cycle.
            if align_interval == prev_interval:
                merged = True
                stream_changes[-1] = (align_interval, max(new_streams, current_streams))
            elif align_interval > prev_interval + args.interval:
                stream_changes.append((align_interval - args.interval, current_streams))
        if not merged:
            stream_changes.append((align_interval, new_streams))
            if len(stream_changes) >= 4:
                a = stream_changes[-4][1]
                b = stream_changes[-3][1]
                c = stream_changes[-2][1]
                if a == b and b == c:
                    stream_changes.pop(-3)
    return new_streams

all_bank = ('x', 'all')

def collectStreamChanges(all_events, banks):
    bank_current_streams = dict()
    bank_stream_changes = dict() 
    for bank in banks:
        bank_stream_changes[bank] = list()
        bank_current_streams[bank] = 0
    for e in all_events:
        bank = (e.se, e.llc_bank)
        bank_current_streams[bank] = addEventToStreamChanges(e,
            stream_changes=bank_stream_changes[bank],
            current_streams=bank_current_streams[bank]
        )
        bank_current_streams[all_bank] = addEventToStreamChanges(e,
            stream_changes=bank_stream_changes[all_bank],
            current_streams=bank_current_streams[all_bank]
        )
    return bank_stream_changes

def collectBanks(all_events):
    all_banks = list()
    for e in all_events:
        bank = (e.se, e.llc_bank)
        if bank not in all_banks:
            all_banks.append(bank)
    all_banks.sort()
    all_banks.append(all_bank)
    return all_banks

def dumpAliveStreams(folder, keyword=None):
    all_events = collectAllTraces(folder, keyword)
    all_events.sort(key=lambda x: x.cycle)
    base_folder = os.path.basename(os.path.basename(os.path.basename(folder)))
    banks = collectBanks(all_events)
    bank_stream_changes = collectStreamChanges(all_events, banks)
    print(f'All Banks {banks}')
    with open(f'{base_folder}-llc-{keyword if keyword else "all"}-streams-timeline.csv', 'w') as f:
        max_streams = list()
        max_cycles = list()
        min_cycles = list()
        for bank in banks:
            print(f'Writing {bank}')
            f.write(f'bank-{bank[0]}-{bank[1]}\n')
            stream_changes = bank_stream_changes[bank]
            max_streams.append(max(x[1] for x in stream_changes))
            min_cycles.append(stream_changes[0][0])
            max_cycles.append(stream_changes[-1][0])
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
        for bank in range(len(min_cycles)):
            f.write(f'{min_cycles[bank]},')
        f.write('\n')
        for bank in range(len(max_cycles)):
            f.write(f'{max_cycles[bank]},')
        f.write('\n')
        for bank in range(len(max_cycles)):
            f.write(f'{max_cycles[bank] - min_cycles[bank]},')
        f.write('\n')


def main(argv):
    dumpAliveStreams(args.folder, args.keyword)


if __name__ == '__main__':
    main(sys.argv)

