from ComputeCacheModel import IndVar
from ComputeCacheModel import LoopStruct
from ComputeCacheModel import Stream
from ComputeCacheModel import LoopBody

def get_loop_body():
    """
    Only the kernel processing the inner region.
    for n = 0 -> N - 1
      for i = n + 1 -> N
        m = A[i][n] / A[n][n]
        for j = n -> N
          A[i][j] -= A[n][j] * m
    """
    N = 2048
    hotspot_operations = ['*', '-']
    hotspot_tile_streams = [
        Stream('A', N * N, 4, [('i', N), ('j', 1)]),
    ]
    hotspot_tile_streams2 = [
        Stream('A', N * N, 4, [('i', N), ('j', 1)]),
        Stream('A', N * N, 4, [('j', 1)]),
    ]
    hotspot_tile_loop_struct = LoopStruct(bitline_dim=0, ind_vars=[
        IndVar('j', 0, N),
        IndVar('i', 0, N),
    ])
    hotspot_tile_loop_body = LoopBody(
        hotspot_tile_loop_struct, hotspot_tile_streams, hotspot_operations)
    hotspot_tile_loop_body2 = LoopBody(
        hotspot_tile_loop_struct, hotspot_tile_streams2, hotspot_operations)
    return (hotspot_tile_loop_body, hotspot_tile_loop_body2)

def get_nsc_interleave_anchor():
    interleave = 1024
    anchor = 'C'
    return (interleave, anchor)