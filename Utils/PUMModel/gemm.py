from ComputeCacheModel import IndVar
from ComputeCacheModel import LoopStruct
from ComputeCacheModel import Stream
from ComputeCacheModel import LoopBody

def get_loop_body():
    """
    Let's do a MM example:
    for i = 0 -> N
      for j = 0 -> N
        for k = 0 -> N
          C[i][j] = A[i][k] * B[k][j]

    The first loop body establish the default mapping.
    for i = 0 -> N
      for j = 0 -> N
        A[i][j], B[i][j], C[i][j]

    The second loop body will do the computation.
    """
    N = 64
    I = N
    J = N
    K = N
    mm_streams = [
        Stream('A', I * K, 4, [('i', K), ('k', 1)]),
        Stream('B', K * J, 4, [('k', J), ('j', 1)]),
        Stream('C', I * J, 4, [('i', J), ('j', 1)]),
    ]
    mm_operations = ['*']
    mm_loop_struct = LoopStruct(bitline_dim=0, ind_vars=[
        IndVar('k', 0, K),
        IndVar('j', 0, J),
        IndVar('i', 0, I),
    ])
    mm_loop_body = LoopBody(mm_loop_struct, mm_streams, mm_operations)
    print(mm_loop_body)
    print("Gemm has reduction.")
    assert(False)