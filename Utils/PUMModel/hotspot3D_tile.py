from ComputeCacheModel import IndVar
from ComputeCacheModel import LoopStruct
from ComputeCacheModel import Stream
from ComputeCacheModel import LoopBody

def get_loop_body():

    """
    Hotspot3D:
    for i = 0 -> M
      for j = 0 -> N
        for k = 0 -> N
        C[i][j][k] = A[i][j][k] * Rf + \
            ((B[i][j][k] << 1) - B[i][j+1][k] - B[i][j-1][k]) * Ry + \
            ((B[i][j][k] << 1) - B[i+1][j][k] - B[i-1][j][k]) * Rz + \
            ((B[i][j][k] << 1) - B[i][j][k+1] - B[i][j][k-1]) * Rx 
    """
    M = 16
    N = 512
    hotspot3D_operations = ['*', '-', '-', '-', '-', '-', '-', '*', '*', '*', '+', '+', '+']
    hotspot3D_streams = [
        Stream('A', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)]),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)]),
        Stream('C', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)]),
    ]
    hotspot3D_streams2 = [
        Stream('A', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)]),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)]),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)], N * N),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)], -N * N),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)], -N),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)], N),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)], 1),
        Stream('B', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)], -1),
        Stream('C', M * N * N, 4, [('i', N * N), ('j', N), ('k', 1)]),
    ]
    hotspot3D_loop_struct = LoopStruct(bitline_dim=0, ind_vars=[
        IndVar('k', 0, 8),
        IndVar('j', 0, 8),
        IndVar('i', 0, 8),
        IndVar('k', 1, N // 8),
        IndVar('j', 1, N // 8),
        IndVar('i', 1, M // 8),
    ])
    hotspot3D_loop_body = LoopBody(
        hotspot3D_loop_struct, hotspot3D_streams, hotspot3D_operations)
    hotspot3D_loop_body2 = LoopBody(
        hotspot3D_loop_struct, hotspot3D_streams2, hotspot3D_operations)
    return (hotspot3D_loop_body, hotspot3D_loop_body2)

def get_nsc_interleave_anchor():
    interleave = 256
    anchor = 'C'
    return (interleave, anchor)