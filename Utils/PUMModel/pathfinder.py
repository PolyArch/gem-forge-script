from ComputeCacheModel import IndVar
from ComputeCacheModel import LoopStruct
from ComputeCacheModel import Stream
from ComputeCacheModel import LoopBody

def get_loop_body():
    """
    Simple 1D pointwise computation.
    for i = 0 -> N
        C[i] = A[i] + min(B[i-1], B[i], B[i+1])
    """
    N = 4 * 1024 * 1024
    operations = ['-', '-', '+']
    streams = [
        Stream('A', N, 4, [('i', 1)]),
        Stream('B', N, 4, [('i', 1)]),
        Stream('C', N, 4, [('i', 1)]),
    ]
    streams2 = [
        Stream('A', N, 4, [('i', 1)]),
        Stream('B', N, 4, [('i', 1)]),
        Stream('B', N, 4, [('i', 1)], 1),
        Stream('B', N, 4, [('i', 1)], -1),
        Stream('C', N, 4, [('i', 1)]),
    ]
    loop_struct = LoopStruct(bitline_dim=0, ind_vars=[
        IndVar('i', 0, N),
    ])
    loop_body = LoopBody(loop_struct, streams, operations)
    loop_body2 = LoopBody(loop_struct, streams2, operations)
    return (loop_body, loop_body2)

def get_nsc_interleave_anchor():
    interleave = 1024
    anchor = 'C'
    return (interleave, anchor)