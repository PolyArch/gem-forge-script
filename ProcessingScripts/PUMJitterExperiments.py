"""
Simple script to feed tdfg to pum-jitter and collect jit runtime.
"""

import os
import sys
import subprocess

import argparse

__print_us__ = True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get PUM Jit time.')
    parser.add_argument('--folder', action='store', default='.',
                        help='where to find tdfgs.')
    parser.add_argument('--debug-tdfg', action='store', type=int, default=None,
                        help='which tdfg to debug.')

    args = parser.parse_args()

def invokePUMJitter(pum_jitter, tdfg, is_debug=False):
    command = [
        pum_jitter,
        tdfg,
    ]
    try:
        output = subprocess.check_output(command, encoding='UTF-8')
        total_runtime = 0.0
        if is_debug:
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            print(output)
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        for line in output.splitlines():
            if not line.startswith('>> '):
                continue
            """
            Format:
            >> CompileTime shiftRhs2D 12.239313 us
            """
            if __print_us__:
                print(line)
            fields = line.split()
            t = float(fields[3])
            total_runtime += t
        return total_runtime
    except subprocess.CalledProcessError as e:
        print(f'Failed to invoke PUMJitter on {tdfg}')
        print(f'  ReturnCode {e.returncode} Output ')
        print(e.output)
        assert(False)

def getPUMJitTimeMicroSecond(sim_out_folder, debug_tdfg=None):

    gem_forge_top = os.getenv('GEM_FORGE_TOP')
    assert(gem_forge_top is not None)

    pum_jitter = os.path.join(
        gem_forge_top,
        'gem5/build/X86/cpu/gem_forge/accelerator/stream/cache/pum/pum-jitter.fast',
    )

    tdfg_folder = os.path.join(
        sim_out_folder,
        'stream_pum_tdfg',
    )

    if not os.path.isdir(tdfg_folder):
        # There is no tdfg folder.
        return 0.0

    # Iterate all json file.
    total_runtime = 0.0
    tdfg_idx = 0
    found_before_lowering = False
    for fn in os.listdir(tdfg_folder):
        if fn.endswith('.json') and fn.startswith('tdfg-before-lowering'):
            found_before_lowering = True
            break
    for fn in os.listdir(tdfg_folder):
        if not fn.endswith('.json'):
            continue
        if found_before_lowering and not fn.startswith('tdfg-before-lowering'):
            continue
        tdfg = os.path.join(tdfg_folder, fn)
        is_debug = False
        if debug_tdfg == tdfg_idx:
            is_debug = True
        total_runtime += invokePUMJitter(pum_jitter, tdfg, is_debug=is_debug)
        tdfg_idx += 1
    
    return total_runtime
        

if __name__ == '__main__':
    sim_out_folder = args.folder
    total_runtime = getPUMJitTimeMicroSecond(sim_out_folder, args.debug_tdfg)
    print(f'Total runtime {total_runtime}us')