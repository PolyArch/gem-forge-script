
import os
import subprocess


def call_helper(cmd, stdout=None, stderr=None):
    """
    Helper function to call a command and print the actual command when failed.
    """
    print(' \\\n'.join(cmd))
    print('Executing \n{cmd}'.format(cmd=' '.join(cmd)))
    try:
        subprocess.check_call(cmd, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError as e:
        print('Error when executing {cmd}'.format(cmd=' '.join(cmd)))
        raise e


def mkdir_p(path):
    if os.path.isdir(path):
        return
    call_helper(['mkdir', '-p', path])


def mkdir_f(path):
    if os.path.isdir(path):
        call_helper(['rm', '-r', path])
    mkdir_p(path)


def mkdir_chain(path):
    if os.path.isdir(path) or not path:
        return
    parent, child = os.path.split(path)
    mkdir_chain(parent)
    mkdir_p(path)


def create_symbolic_link(src, dest):
    if os.path.exists(dest):
        return
    if os.path.realpath(dest) != src:
        call_helper(['rm', '-f', dest])
    call_helper([
        'ln',
        '-s',
        src,
        dest,
    ])

"""
Filter out obj with insignificant weight.
@assume obj.weight
"""
def filter_tail(objs, threshold):
    sum_weight = sum([obj.weight for obj in objs])
    for obj in objs:
        obj.weight = obj.weight / sum_weight
    objs.sort(key=lambda t: t.weight, reverse=True)
    selected_objs = list()
    selected_weight = 0.0
    for obj in objs:
        selected_objs.append(obj)
        selected_weight += obj.weight
        if selected_weight > threshold:
            break
    # Normalize again.
    for obj in objs:
        obj.weight = obj.weight / selected_weight
    return (selected_objs, selected_weight)