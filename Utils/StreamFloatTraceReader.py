import Utils.StreamMessage_pb2 as StreamMesssage_pb2
import sys
import os
import argparse

from google.protobuf.internal.decoder import _DecodeVarint32

enable_print = True
def PRINT(f):
    if enable_print:
        print(f)

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


def collectTrace(args, fn):
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

def match_file_with_keyword(fn, keyword):
    if keyword is None:
        return True
    ks = keyword.split(',')
    for k in ks:
        if k in fn:
            return True
    return False

def collectAllTraces(args, folder, keyword=None):
    all_events = list()
    min_cycle = 1000000000000000
    PRINT(f'Reading folder {folder}')
    for f in os.listdir(folder):
        if not match_file_with_keyword(f, keyword):
            continue
        full_fn = os.path.join(folder, f)
        if os.path.isfile(full_fn):
            PRINT(f'Reading {f}')
            events = collectTrace(args, full_fn)
            if events:
                PRINT(f'NumEvents {len(events)} {events[0].cycle}-{events[-1].cycle}')
                min_cycle = min(min_cycle, events[0].cycle)
            all_events += events
    PRINT(f'Subtracting Min Cycle {min_cycle}')
    for e in all_events:
        e.cycle -= min_cycle
    return all_events

def alignCycleToInterval(args, cycle):
    return cycle - cycle % args.interval

def addEventToStreamChanges(args, e, prev_streams, stream_changes):
    new_streams = prev_streams
    # Stream events.
    if args.event_type == 'llc-stream':
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.MIGRATE_IN:
            new_streams += 1
        elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.CONFIG:
            new_streams += 1
        elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.MIGRATE_OUT:
            new_streams -= 1
        elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.END:
            new_streams -= 1
    # Stream engine events.
    elif args.event_type == 'llc-cmp':
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.CMP_START:
            new_streams += 1
        elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.CMP_DONE:
            new_streams -= 1
    elif args.event_type == 'llc-req':
        if e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.LOCAL_REQ_START:
            new_streams += 1
        elif e.type == StreamMesssage_pb2.StreamFloatEvent.StreamFloatEventType.LOCAL_REQ_DONE:
            new_streams -= 1
    if new_streams == prev_streams:
        # No change. Skip
        return new_streams
    
    """
    Be careful how to merge stream change within the same interval.
    Since we are modeling the average within this interval.
    NOTE: The previous stream change has prev_cycle, not prev_interval as we need it
    to construct the average.
    """
    assert(stream_changes)
    curr_cycle = e.cycle
    curr_interval = alignCycleToInterval(args, curr_cycle)
    prev_cycle, acc = stream_changes[-1]
    prev_interval = alignCycleToInterval(args, prev_cycle)

    mid_interval = prev_interval + args.interval

    if curr_interval == prev_interval:
        # We are still within the same interval.
        diff = curr_cycle - prev_cycle
        acc += prev_streams * diff
        stream_changes[-1] = (curr_cycle, acc)
    elif curr_interval == mid_interval:
        # We are moving to the next interval.
        # Close the previous interval.
        acc += prev_streams * (args.interval - (prev_cycle - prev_interval))
        stream_changes[-1] = (prev_interval, acc / args.interval)
        # Open the new interval.
        new_acc = prev_streams * (curr_cycle - curr_interval)
        stream_changes.append((curr_cycle, new_acc))
    else:
        assert(curr_interval > mid_interval)
        # Close the previous interval
        acc += prev_streams * (args.interval - (prev_cycle - prev_interval))
        stream_changes[-1] = (prev_interval, acc / args.interval)
        # Create the intermediate interval.
        stream_changes.append((mid_interval, prev_streams))
        # Create possible second intermediate interval.
        if curr_interval > mid_interval + args.interval:
            stream_changes.append((curr_interval - args.interval, prev_streams))
        # Open the new interval.
        new_acc = prev_streams * (e.cycle - curr_interval)
        stream_changes.append((e.cycle, new_acc))

    # merged = False
    # if stream_changes:
    #     prev_interval = stream_changes[-1][0]
    #     if align_interval == prev_interval:
    #         merged = True
    #         stream_changes[-1] = (align_interval, max(new_streams, prev_streams))
    #     elif align_interval > prev_interval + args.interval:
    #         stream_changes.append((align_interval - args.interval, prev_streams))
    # if not merged:
    #     stream_changes.append((align_interval, new_streams))
    #     if len(stream_changes) >= 4:
    #         a = stream_changes[-4][1]
    #         b = stream_changes[-3][1]
    #         c = stream_changes[-2][1]
    #         if a == b and b == c:
    #             stream_changes.pop(-3)

    return new_streams

all_bank = ('x', 'all')
avg_bank = ('x', 'avg')
one_quarter_bank = ('x', '25%')
three_quarter_bank = ('x', '75%')
max_bank = ('x', 'max')
min_bank = ('x', 'min')

def collectStreamChanges(args, all_events, banks):
    bank_current_streams = dict()
    bank_stream_changes = dict() 
    for bank in banks:
        bank_stream_changes[bank] = [(0, 0)] 
        bank_current_streams[bank] = 0
    for e in all_events:
        bank = (e.se, e.llc_bank)
        bank_current_streams[bank] = addEventToStreamChanges(args, e,
            stream_changes=bank_stream_changes[bank],
            prev_streams=bank_current_streams[bank]
        )
        bank_current_streams[all_bank] = addEventToStreamChanges(args, e,
            stream_changes=bank_stream_changes[all_bank],
            prev_streams=bank_current_streams[all_bank]
        )
    # Close the last interval.
    for bank in banks:
        stream_changes = bank_stream_changes[bank]
        prev_streams = bank_current_streams[bank]
        prev_cycle, acc = stream_changes[-1]
        prev_interval = alignCycleToInterval(args, prev_cycle)
        acc += prev_streams * (args.interval - (prev_cycle - prev_interval))
        stream_changes[-1] = (prev_interval, acc / args.interval)
        # Add the final zero interval
        stream_changes.append((prev_interval + args.interval, 0))

    return bank_stream_changes

def collectBanks(args, all_events):
    all_banks = list()
    for e in all_events:
        bank = (e.se, e.llc_bank)
        if bank not in all_banks:
            all_banks.append(bank)
    all_banks.sort()
    all_banks.append(all_bank)
    return all_banks

def alignStreamChanges(args, bank_stream_changes):
    PRINT('Start to align changes')
    aligned = dict()
    total_changes = 0
    max_cycle = 0
    for bank in bank_stream_changes:
        aligned[bank] = list()
        changes = bank_stream_changes[bank]
        total_changes += len(changes)
        if changes:
            max_cycle = max(max_cycle, changes[-1][0])

    processed_changes = 0
    while processed_changes < total_changes:
        # Select the next cycle.
        next_cycle = max_cycle
        for bank in bank_stream_changes:
            changes = bank_stream_changes[bank]
            if not changes:
                continue
            next_cycle = min(next_cycle, changes[0][0])
        
        # Pop changes at the next_cycle
        for bank in bank_stream_changes:
            changes = bank_stream_changes[bank]
            aligned_changes = aligned[bank]
            if not changes or changes[0][0] > next_cycle:
                # Either duplicate or put a 0 here.
                if not aligned_changes:
                    aligned_changes.append((next_cycle, 0))
                else:
                    prev_change = aligned_changes[-1][1]
                    aligned_changes.append((next_cycle, prev_change))
            else:
                # We can move the change.
                aligned_changes.append(changes[0])
                changes.pop(0)
                processed_changes += 1
    PRINT('Aligned changes')

    return aligned

def addStatsToAligned(args, aligned, new_banks):
    # Add average and other stats.
    total_intervals = 0
    banks = list()
    for bank in aligned:
        if bank == all_bank:
            continue
        total_intervals = len(aligned[bank])
        banks.append(bank)

    num_banks = len(banks)
    samples = list(range(num_banks))

    avgs = list()
    three_quarters = list()
    one_quarters = list()
    maxes = list()
    mines = list()

    for i in range(total_intervals):
        cycle = aligned[banks[0]][i][0]
        for j in range(len(banks)):
            bank = banks[j]
            samples[j] = aligned[bank][i][1]
        # Compute the average.
        samples.sort()
        total = sum(samples)
        avg = total / num_banks
        maximal = max(samples)
        minimal = min(samples)
        three_quarter = samples[int(3 * num_banks / 4)]
        one_quarter = samples[int(1 * num_banks / 4)]

        avgs.append((cycle, avg))
        three_quarters.append((cycle, three_quarter))
        one_quarters.append((cycle, one_quarter))
        mines.append((cycle, minimal))
        maxes.append((cycle, maximal))

    aligned[avg_bank] = avgs
    aligned[one_quarter_bank] = one_quarters
    aligned[three_quarter_bank] = three_quarters
    aligned[min_bank] = mines
    aligned[max_bank] = maxes

    new_banks.insert(0, max_bank)
    new_banks.insert(0, three_quarter_bank)
    new_banks.insert(0, avg_bank)
    new_banks.insert(0, one_quarter_bank)
    new_banks.insert(0, min_bank)

    return aligned

def dumpStreamChange(args, f, banks, bank_stream_changes):
    for bank in banks:
        PRINT(f'Writing {bank}')
        stream_changes = bank_stream_changes[bank]
        f.write(f'bank-{bank[0]}-{bank[1]}\n')
        for c in stream_changes:
            f.write(f'{c[0]},')
        f.write('\n')
        for c in stream_changes:
            f.write(f'{c[1]},')
        f.write('\n')

def dumpAlignedStreamChange(args, f, banks, bank_stream_changes):
    # Dump the cycles.
    for cycle, _ in bank_stream_changes[banks[0]]:
        f.write(f',{cycle}')
    f.write('\n')

    # Dump the bank.
    for bank in banks:
        PRINT(f'Writing {bank}')
        stream_changes = bank_stream_changes[bank]
        f.write(f'bank-{bank[0]}-{bank[1]}')
        for _, streams in stream_changes:
            f.write(f',{streams}')
        f.write('\n')

def determinInterval(args, all_events):
    if args.n_intervals == 0:
        return
    min_cycle = all_events[0].cycle
    max_cycle = all_events[-1].cycle
    diff = max_cycle - min_cycle
    ratio = diff // args.n_intervals
    high_digit = 1
    while high_digit <= ratio:
        high_digit *= 10
    high_digit //= 10
    args.interval = (ratio // high_digit) * high_digit
    PRINT(f'Min {min_cycle} Max {max_cycle} Diff {diff} NInterval {args.n_intervals} Ratio {ratio} Interval {args.interval}')


def dumpAliveStreams(args):
    folder = args.folder
    keyword = args.keyword
    all_events = collectAllTraces(args, folder, keyword)
    all_events.sort(key=lambda x: x.cycle)
    determinInterval(args, all_events)
    base_folder = os.path.basename(os.path.basename(os.path.basename(folder)))
    banks = collectBanks(args, all_events)
    bank_stream_changes = collectStreamChanges(args, all_events, banks)
    PRINT(f'All Banks {banks}')

    if args.align:
        bank_stream_changes = alignStreamChanges(args, bank_stream_changes)
        addStatsToAligned(args, bank_stream_changes, banks)

    out_csv_fn = f'{args.out_fn}.{args.event_type}.csv'
    PRINT(f'Write CSV {out_csv_fn}')

    with open(out_csv_fn, 'w') as f:
        if args.align:
            dumpAlignedStreamChange(args, f, banks, bank_stream_changes)
        else:
            dumpStreamChange(args, f, banks, bank_stream_changes)
        max_streams = list()
        max_cycles = list()
        min_cycles = list()
        for bank in banks:
            stream_changes = bank_stream_changes[bank]
            max_streams.append(max(x[1] for x in stream_changes))
            min_cycles.append(stream_changes[0][0])
            max_cycles.append(stream_changes[-1][0])

        f.write('\n')
        if not args.no_summary:
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

    parser = argparse.ArgumentParser(
        prog = 'Read StreamFloatTrace')

    parser.add_argument('folder')           # positional argument
    parser.add_argument('--interval', '-i',
        type=int, default=10,
        help='Interval in cycles to merge event')      # option that takes a value
    parser.add_argument('--n-intervals',
        type=int, default=0,
        help='Break into specific intervals')      # option that takes a value
    parser.add_argument('--keyword', '-k',
        type=str, default=None,
        help='Keyword to filter out traces')      # option that takes a value
    parser.add_argument('--align', '-a',
        action='store_true', default=False,
        help='Align changes')     
    parser.add_argument('--out-fn', '-o',
        type=str, default="float-trace.csv",
        help='Output filename')    
    parser.add_argument('--no-summary',
        action='store_true', default=False,
        help='Dump summary at the end')    
    parser.add_argument('--event-type',
        choices=['llc-stream', 'llc-cmp', 'llc-req'], default='llc-stream',
        help='What event to process')

    args = parser.parse_args(argv)

    dumpAliveStreams(args)


if __name__ == '__main__':
    main(sys.argv[1:])

