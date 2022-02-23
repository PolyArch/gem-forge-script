from ComputeCacheModel import IndVar
from ComputeCacheModel import LoopStruct
from ComputeCacheModel import Stream
from ComputeCacheModel import LoopBody

def get_loop_body():
    """
    Simple 2D stencil:
    for i = 0 -> N
      for j = 0 -> N
        C[i][j] = A[i][j] * Rz + \
            ((B[i][j] << 1) - B[i][j+1] - B[i][j-1]) * Rx + \
            ((B[i][j] << 1) - B[i+1][j] - B[i-1][j]) * Ry 
    """
    N = 2048
    hotspot_operations = ['*', '-', '-', '-', '-', '*', '*', '+', '+']
    hotspot_tile_streams = [
        Stream('A', N * N, 4, [('i', N), ('j', 1)]),
        Stream('B', N * N, 4, [('i', N), ('j', 1)]),
        Stream('C', N * N, 4, [('i', N), ('j', 1)]),
    ]
    hotspot_tile_streams2 = [
        Stream('A', N * N, 4, [('i', N), ('j', 1)]),
        Stream('B', N * N, 4, [('i', N), ('j', 1)]),
        Stream('B', N * N, 4, [('i', N), ('j', 1)], -N),
        Stream('B', N * N, 4, [('i', N), ('j', 1)], N),
        Stream('B', N * N, 4, [('i', N), ('j', 1)], 1),
        Stream('B', N * N, 4, [('i', N), ('j', 1)], -1),
        Stream('C', N * N, 4, [('i', N), ('j', 1)]),
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