

from abc import abstractmethod
from array import array

import sys


class LLCConfig:
    """
    This represents a mesh topology LLC configuration (from bottom up):
    Each SRAM array is organized as A (wordline) x B (bitline).
    Each way contains L SRAM arrays are connected with a tree of degree D and leaf bandwidth S.
    Each LLC bank contains W ways.
    Each chip contains M x M LLC banks.

    Way:
     ----------------------------------------------------------------------------------------
    |                                                                                        |   
    |   <------------------------------------    L    -------------------------------->      |    
    |       B           B            B           B                                 B         |              
    |     -----       -----        -----       -----                             -----       |                      
    |   A|     |    A|     |     A|     |    A|     |        ...               A|     |      |                                
    |    |     |     |     |      |     |     |     |                           |     |      |                            
    |     -----       -----        -----       -----                             -----       |                                   
    |     S |    D    S |          S |    D    S |                          D    S |         |   
    |        -----------              -----------                        ----------          |        
    |             |                        |                                 |               |    
    |                         ...                             ...                            |        
    |                                                                                        |               
     ----------------------------------------------------------------------------------------
    
    """

    def __init__(self, array_rows, array_cols, array_per_way, tree_degree, tree_leaf_bandwdith_bytes, way_per_bank, mesh_layers, mesh_rows, mesh_cols):
        self.array_rows = array_rows
        self.array_cols = array_cols
        self.array_per_way = array_per_way
        self.tree_degree = tree_degree
        self.tree_leaf_bandwidth_bytes = tree_leaf_bandwdith_bytes
        self.way_per_bank = way_per_bank
        self.mesh_layers = mesh_layers
        self.mesh_rows = mesh_rows
        self.mesh_cols = mesh_cols

    def get_total_arrays(self):
        return self.mesh_rows * self.mesh_cols * self.mesh_layers * self.way_per_bank * self.array_per_way

    def get_total_banks(self):
        return self.mesh_layers * self.mesh_rows * self.mesh_cols

    def get_array_per_bank(self):
        return self.way_per_bank * self.array_per_way
    
    def get_bitlines_per_bank(self):
        return self.get_array_per_bank() * self.array_cols

    def get_array_idx_from_bitline_idx(self, bitline_idx):
        return bitline_idx // self.array_cols

    def get_way_leaf_idx_from_array_idx(self, array_idx):
        return array_idx % self.array_per_way

    def get_way_idx_from_array_idx(self, array_idx):
        return array_idx // self.array_per_way

    def get_bank_idx_from_way_idx(self, way_idx):
        return way_idx // self.way_per_bank

    def get_bank_idx_from_array_idx(self, array_idx):
        return self.get_bank_idx_from_way_idx(self.get_way_idx_from_array_idx(array_idx))

    def get_hops_between_bank(self, bank_idx1, bank_idx2):
        layer1, row1, col1 = self.get_mesh_layer_row_col_from_bank_idx(bank_idx1)
        layer2, row2, col2 = self.get_mesh_layer_row_col_from_bank_idx(bank_idx2)
        return abs(layer1 - layer2) + abs(row1 - row2) + abs(col1 - col2)

    def get_mesh_layer_row_col_from_bank_idx(self, bank_idx):
        layer = bank_idx // (self.mesh_rows * self.mesh_cols)
        bank_idx = bank_idx % (self.mesh_rows * self.mesh_cols)
        return (layer, bank_idx // self.mesh_cols, bank_idx % self.mesh_cols)

    def get_bank_idx_from_mesh_layer_row_col(self, mesh_layer, mesh_row, mesh_col):
        return mesh_layer * self.mesh_rows * self.mesh_cols + mesh_row * self.mesh_cols + mesh_col

class LLCLocation:
    """
    Represents a location in the LLC data array. Tuple of
    (mesh_row, mesh_col, way, array, array_row, array_col)
    """
    def __init__(self, array_row, array_col, array, way, mesh_layer, mesh_row, mesh_col):
        self.array_row = array_row
        self.array_col = array_col
        self.array = array
        self.way = way
        self.mesh_layer = mesh_layer
        self.mesh_row = mesh_row
        self.mesh_col = mesh_col

    def get_flat_mesh_idx(self, llc_config):
        return llc_config.get_bank_idx_from_mesh_layer_row_col(self.mesh_layer, self.mesh_row, self.mesh_col)

    def get_flat_array_idx(self, llc_config):
        return self.array + self.way * llc_config.array_per_way \
            + self.get_flat_mesh_idx(llc_config) * llc_config.get_array_per_bank()

    def get_flat_bitline_idx(self, llc_config):
        return self.get_flat_array_idx(llc_config) * llc_config.array_cols + self.array_col

    def __str__(self):
        return f'[{self.mesh_layer}x{self.mesh_row}x{self.mesh_col}x{self.way}x{self.array}x{self.array_row}x{self.array_col}]'


class IndVar:
    """
    This represents one induction variable. With the orignal name and suffix if tiled.
    For example, the induction variable i <- [0, 100) after tiled will be i1 <- [0, 5)
    and i2 <- [0, 20).
    """
    def __init__(self, name, tile_level, n):
        self.name = name
        self.tile_level = tile_level
        self.n = n

    def __str__(self):
        return f'{self.name}_{self.tile_level}:{self.n}'

    def tile(self, tile_size):
        """
        Split this induction variable into two, with the inner one has the original tile
        level and range tile_size.
        """
        if self.n % tile_size != 0:
            print(f'{self} non-divisor tile size {tile_size}')
            assert(False)
        inner_iv = IndVar(self.name, self.tile_level, tile_size)
        outer_iv = IndVar(self.name, self.tile_level + 1, self.n / tile_size)
        return (inner_iv, outer_iv)

class LoopStruct:
    """
    This represents a loop structure with a list of induction variables, starting from
    the inner most one.
    bitline_dim represents the number of inner dimensions that are unrolled in bitline.
    """
    def __init__(self, bitline_dim, ind_vars):
        self.bitline_dim = bitline_dim
        self.ind_vars = ind_vars

    def __str__(self):
        ret = ''
        for i in range(len(self.ind_vars)):
            indent = '  ' * i
            iv = self.ind_vars[len(self.ind_vars) - 1 - i]
            ret += f'{indent}for {iv}\n'
        return ret

    def get_num_loop_levels(self):
        return len(self.ind_vars)

    def get_num_iters(self):
        iters = 1
        for iv in self.ind_vars:
            iters *= iv.n
        return iters

    def get_iv_at_iter(self, iter_num):
        assert(iter_num < self.get_num_iters())
        ivs = list()
        for iv in self.ind_vars:
            ivs.append(iter_num % iv.n)
            iter_num = iter_num // iv.n
        assert(iter_num == 0)
        return ivs

class Stream:
    """
    This represents a stream pattern that remembers how to compute the address from
    the induction variables.
    It will be a list of (ind_var, stride), so purely affine:
    iv1 * mult1 + iv2 * mult2 + ... + constant
    Notice that here induction variables are all before tiled.
    """
    def __init__(self, name, num_elem, data_type_size, iv_mults, constant = 0):
        self.name = name
        self.num_elem = num_elem
        self.data_type_size = data_type_size
        self.iv_mults = iv_mults
        self.constant = constant

    def __str__(self):
        return f'{self.name}[' + ' + '.join([f'{x[0]}x{x[1]}' for x in self.iv_mults]) + \
            f' {"+" if self.constant > 0 else "-"} {abs(self.constant)}]'

    def reconstruct_iv_value(self, iv_name, ind_vars, ivs):
        match_ivs = [x for x in zip(ind_vars, ivs) if x[0].name == iv_name]
        match_ivs.sort(key=lambda x: x[0].tile_level)
        tile_size = 1
        ret = 0
        for iv, iv_val in match_ivs:
            ret += iv_val * tile_size
            tile_size *= iv.n
        return ret

    def get_elem_idx_from_iv(self, ind_vars, ivs):
        elem_idx = self.constant
        for iv_name, mult in self.iv_mults:
            iv_val = self.reconstruct_iv_value(iv_name, ind_vars, ivs)
            elem_idx += iv_val * mult
        return elem_idx

class LoopBody:
    """
    This represents a loop body, contains a loop structure and a list of streams.
    """
    def __init__(self, loop_struct, streams, operations):
        self.loop_struct = loop_struct
        self.streams = streams
        self.operations = operations

    def __str__(self):
        ret = f'{self.loop_struct}'
        indent = '  ' * self.loop_struct.get_num_loop_levels()
        for s in self.streams:
            ret += f'{indent}{s}\n'
        return ret

class TrafficModel:

    def __init__(self, llc_config, loop_body, nsc_interleave=-1, nsc_anchor='whatever', multicast=False):
        self.llc_config = llc_config
        self.loop_body = loop_body
        self.nsc_interleave = nsc_interleave
        self.nsc_anchor = nsc_anchor
        self.multicast = multicast
        self.bitline_dim = loop_body.loop_struct.bitline_dim 
        if self.nsc_interleave != -1:
            assert(self.bitline_dim == 0)

    def build_bitline_data_map(self):
        self.bitline_data = list()
        loop_struct = self.loop_body.loop_struct
        streams = self.loop_body.streams
        ind_vars = loop_struct.ind_vars
        bitline_iters = 1
        for ind_var in ind_vars[0:self.bitline_dim]:
            bitline_iters *= ind_var.n
        stream_data = list()
        for iter_idx in range(loop_struct.get_num_iters()):
            ivs = loop_struct.get_iv_at_iter(iter_idx)
            for s in streams:
                elem_idx = s.get_elem_idx_from_iv(ind_vars, ivs)
                if elem_idx < 0 or elem_idx >= s.num_elem:
                    continue
                stream_data.append((s.name, elem_idx))
            if (iter_idx + 1) % bitline_iters == 0:
                # Time to move to the next bitline.
                # Remember the current stream data and dedup.
                stream_data = list(dict.fromkeys(stream_data))
                stream_data.sort()
                self.bitline_data.append(stream_data)
                stream_data = list()

    def build_nsc_elem_data_map(self):
        self.array_loc_map = dict()
        for s in self.loop_body.streams:
            if s.name not in self.array_loc_map:
                self.array_loc_map[s.name] = list()
        loop_struct = self.loop_body.loop_struct
        streams = self.loop_body.streams
        anchor_stream = None
        for s in streams:
            if s.name == self.nsc_anchor:
                anchor_stream = s
        assert(anchor_stream)
        ind_vars = loop_struct.ind_vars
        for iter_idx in range(loop_struct.get_num_iters()):
            ivs = loop_struct.get_iv_at_iter(iter_idx)
            elem_idx = anchor_stream.get_elem_idx_from_iv(ind_vars, ivs)
            if elem_idx < 0 or elem_idx >= anchor_stream.num_elem:
                continue
            elem_addr = elem_idx * s.data_type_size
            bank_idx = (elem_addr // self.nsc_interleave) % self.llc_config.get_total_banks()
            # For now just put it at the first bitline of that bank.
            bitline_idx = bank_idx * self.llc_config.get_bitlines_per_bank()

            for s in streams:
                elem_idx = s.get_elem_idx_from_iv(ind_vars, ivs)
                if elem_idx < 0 or elem_idx >= s.num_elem:
                    continue
                # Always put the element where the anchor stream is located.
                loc_map = self.array_loc_map[s.name]
                while len(loc_map) <= elem_idx:
                    loc_map.append(list())
                loc_map[elem_idx].append(bitline_idx)

    def build_elem_data_map(self):
        self.array_loc_map = dict()
        for s in self.loop_body.streams:
            if s.name not in self.array_loc_map:
                self.array_loc_map[s.name] = list()
        for bitline_idx in range(len(self.bitline_data)):
            data = self.bitline_data[bitline_idx]
            for array_name, elem_idx in data:
                loc_map = self.array_loc_map[array_name]
                while len(loc_map) <= elem_idx:
                    loc_map.append(list())
                loc_map[elem_idx].append(bitline_idx)

    def estimate_traffic(self, target_array_loc_map):
        array_intra_bank_traffic_map = dict()
        array_inter_bank_traffic_map = dict()
        self.target_array_loc_map = target_array_loc_map
        for s in self.loop_body.streams:
            array_name = s.name
            if array_name in array_intra_bank_traffic_map:
                continue
            my_array_loc = self.array_loc_map[array_name]
            target_array_loc = target_array_loc_map[array_name]
            intra_bank_traffic_pair = dict()
            inter_bank_traffic_pair = dict()
            for elem_idx in range(len(target_array_loc)):
                target_locs = target_array_loc[elem_idx]
                my_locs = my_array_loc[elem_idx]

                intra_bank_array_idxes = list()
                inter_bank_bank_idxes = list()

                # Collect all target array idx, deduplicated.
                for target_loc in target_locs:
                    if target_loc in my_locs:
                        # No need to move.
                        continue
                    # For now just pick the first one.
                    if not my_locs:
                        print(my_array_loc)
                        print(f'{array_name}[{elem_idx}]')
                    assert(my_locs)
                    my_loc = my_locs[0]
                    target_array_idx = self.llc_config.get_array_idx_from_bitline_idx(target_loc)
                    my_array_idx = self.llc_config.get_array_idx_from_bitline_idx(my_loc)
                    if target_array_idx == my_array_idx:
                        continue
                    target_bank_idx = self.llc_config.get_bank_idx_from_array_idx(target_array_idx)
                    my_bank_idx = self.llc_config.get_bank_idx_from_array_idx(my_array_idx)
                    if target_bank_idx == my_bank_idx:
                        intra_bank_array_idxes.append((my_array_idx, target_array_idx))
                    else:
                        inter_bank_bank_idxes.append((my_bank_idx, target_bank_idx))

                for pair in intra_bank_array_idxes:
                    if pair not in intra_bank_traffic_pair:
                        intra_bank_traffic_pair[pair] = 0
                    intra_bank_traffic_pair[pair] += s.data_type_size
                

                if self.multicast:
                    inter_bank_bank_idxes = self.apply_multicast_on_inter_bank_traffic_pair(inter_bank_bank_idxes)
                
                for pair in inter_bank_bank_idxes:
                    if pair not in inter_bank_traffic_pair:
                        inter_bank_traffic_pair[pair] = 0
                    inter_bank_traffic_pair[pair] += s.data_type_size

            array_intra_bank_traffic_map[array_name] = intra_bank_traffic_pair
            array_inter_bank_traffic_map[array_name] = inter_bank_traffic_pair

        self.array_intra_bank_traffic_map = array_intra_bank_traffic_map
        self.array_inter_bank_traffic_map = array_inter_bank_traffic_map

    def apply_multicast_on_inter_bank_traffic_pair(self, pairs):
        # Generate routing path for all target banks.
        route_paths = [self.get_route_path_between_banks(src, dst) for src, dst in pairs]
        unique_edge_pairs = set()
        for path in route_paths:
            for edge_pair in path:
                if edge_pair not in unique_edge_pairs:
                    unique_edge_pairs.add(edge_pair)
        return unique_edge_pairs

    def analyze_traffic(self):
        def sum_traffic_across_array(array_traffic_map):
            total_traffic_map = dict()
            for array_name in array_traffic_map:
                traffic = array_traffic_map[array_name]
                for pair in traffic:
                    if pair not in total_traffic_map:
                        total_traffic_map[pair] = 0
                    total_traffic_map[pair] += traffic[pair]
            return total_traffic_map
        intra_bank_traffic_map = sum_traffic_across_array(self.array_intra_bank_traffic_map)
        inter_bank_traffic_map = sum_traffic_across_array(self.array_inter_bank_traffic_map)

        intra_way_traffic = list()
        intra_bank_traffic = dict()
        mesh_traffic = dict()
        llc_config = self.llc_config
        for pair in intra_bank_traffic_map:
            data_bytes = intra_bank_traffic_map[pair]
            src_array_idx, dst_array_idx = pair
            src_way_idx = llc_config.get_way_idx_from_array_idx(src_array_idx)
            dst_way_idx = llc_config.get_way_idx_from_array_idx(dst_array_idx)
            if src_way_idx == dst_way_idx:
                src_tree_leaf_idx = llc_config.get_way_leaf_idx_from_array_idx(src_array_idx)
                dst_tree_leaf_idx = llc_config.get_way_leaf_idx_from_array_idx(dst_array_idx)
                xor_tree_leaf_idx = src_tree_leaf_idx ^ dst_tree_leaf_idx
                tree_traffic_idx = 0
                while xor_tree_leaf_idx != 0:
                    xor_tree_leaf_idx = xor_tree_leaf_idx >> 1
                    tree_traffic_idx += 1
                while len(intra_way_traffic) <= tree_traffic_idx:
                    intra_way_traffic.append(dict())
                # Use mask to get the subtree idx.
                mask = (1 << tree_traffic_idx) - 1
                subtree_idx = src_array_idx & (~mask)
                assert((dst_array_idx & (~mask)) == subtree_idx)
                subtree_traffic_map = intra_way_traffic[tree_traffic_idx]
                if subtree_idx not in subtree_traffic_map:
                    subtree_traffic_map[subtree_idx] = 0
                subtree_traffic_map[subtree_idx] += data_bytes
                continue
            src_bank_idx = llc_config.get_bank_idx_from_way_idx(src_way_idx)
            dst_bank_idx = llc_config.get_bank_idx_from_way_idx(dst_way_idx)
            if src_bank_idx == dst_bank_idx:
                if src_bank_idx not in intra_bank_traffic:
                    intra_bank_traffic[src_bank_idx] = 0
                intra_bank_traffic[src_bank_idx] += data_bytes
                continue
        for bank_pair in inter_bank_traffic_map:
            data_bytes = inter_bank_traffic_map[bank_pair]
            if bank_pair not in mesh_traffic:
                mesh_traffic[bank_pair] = 0
            mesh_traffic[bank_pair] += data_bytes

        self.total_traffic_map = intra_bank_traffic_map
        # Convert everything from dict to sorted list.
        self.intra_way_traffic = list()
        for subtree_traffic_map in intra_way_traffic:
            subtree_traffic_list = list(zip(subtree_traffic_map.keys(), subtree_traffic_map.values()))
            subtree_traffic_list.sort()
            self.intra_way_traffic.append(subtree_traffic_list)

        self.intra_bank_traffic = list(zip(intra_bank_traffic.keys(), intra_bank_traffic.values()))
        self.intra_bank_traffic.sort()
        self.mesh_traffic = list(zip(mesh_traffic.keys(), mesh_traffic.values()))
        self.mesh_traffic.sort()

    def get_route_path_between_banks(self, src_bank_idx, dst_bank_idx):
        llc_config = self.llc_config
        src_layer, src_row, src_col = llc_config.get_mesh_layer_row_col_from_bank_idx(src_bank_idx)
        dst_layer, dst_row, dst_col = llc_config.get_mesh_layer_row_col_from_bank_idx(dst_bank_idx)
        layer_step = 1 if dst_layer > src_layer else -1
        row_step = 1 if dst_row > src_row else -1
        col_step = 1 if dst_col > src_col else -1
        route_path = list()
        # Routing Z.
        for i in range(src_layer, dst_layer, layer_step):
            from_bank_idx = llc_config.get_bank_idx_from_mesh_layer_row_col(i, src_row, src_col)
            to_bank_idx = llc_config.get_bank_idx_from_mesh_layer_row_col(i + layer_step, src_row, src_col)
            edge_pair = (from_bank_idx, to_bank_idx)
            route_path.append(edge_pair)
        # Routing Y.
        for i in range(src_row, dst_row, row_step):
            from_bank_idx = llc_config.get_bank_idx_from_mesh_layer_row_col(dst_layer, i, src_col)
            to_bank_idx = llc_config.get_bank_idx_from_mesh_layer_row_col(dst_layer, i + row_step, src_col)
            edge_pair = (from_bank_idx, to_bank_idx)
            route_path.append(edge_pair)
        # Routing X.
        for i in range(src_col, dst_col, col_step):
            from_bank_idx = llc_config.get_bank_idx_from_mesh_layer_row_col(dst_layer, dst_row, i)
            to_bank_idx = llc_config.get_bank_idx_from_mesh_layer_row_col(dst_layer, dst_row, i + col_step)
            edge_pair = (from_bank_idx, to_bank_idx)
            route_path.append(edge_pair)
        return route_path

    def estimate_mesh_traffic_latency(self, traffic_list, bandwidth):
        # Assume bidirectional link and ZYX routing.
        edge_traffic_map = dict()
        for (src_bank_idx, dst_bank_idx), data_bytes in traffic_list:
            route_path = self.get_route_path_between_banks(src_bank_idx, dst_bank_idx)
            for edge_pair in route_path:
                if edge_pair not in edge_traffic_map:
                    edge_traffic_map[edge_pair] = 0
                edge_traffic_map[edge_pair] += data_bytes
        # Just get the maximum edge traffic.
        max_traffic_for_one_edge = max(edge_traffic_map.values()) if edge_traffic_map else 0
        return max_traffic_for_one_edge // bandwidth

    def estimate_move_latency(self):
        intra_way_cycles = list()
        total_move_cycles = 0
        llc_config = self.llc_config
        def estimate_parallel_traffic_latency(traffic_list, bandwidth):
            max_cycles = 0
            for _, data_bytes in traffic_list:
                cycles = data_bytes // bandwidth
                max_cycles = max(max_cycles, cycles)
            return max_cycles
        for subtree_traffic in self.intra_way_traffic:
            cycles = estimate_parallel_traffic_latency(subtree_traffic, llc_config.tree_leaf_bandwidth_bytes)
            intra_way_cycles.append(cycles)
            total_move_cycles += cycles
        intra_bank_cycles = estimate_parallel_traffic_latency(self.intra_bank_traffic, 64)
        total_move_cycles += intra_bank_cycles

        mesh_cycles = self.estimate_mesh_traffic_latency(self.mesh_traffic, 32)

        def estimate_nsc_access_cycles(array_loc_map, data_type_bytes, bitlines_per_bank):
            src_bank_bytes = dict()
            for array_name in array_loc_map:
                loc_map = array_loc_map[array_name]
                for bitline_idxes in loc_map:
                    for bitline_idx in bitline_idxes:
                        bank_idx = bitline_idx // bitlines_per_bank
                        if bank_idx not in src_bank_bytes:
                            src_bank_bytes[bank_idx] = 0
                        src_bank_bytes[bank_idx] += data_type_bytes
            # Assume 4 cycles per cache line.
            max_access_cycles = max(src_bank_bytes.values()) // 64 * 4
            return max_access_cycles
        if self.nsc_interleave != -1:
            access_cycles = estimate_nsc_access_cycles(
                self.target_array_loc_map,
                self.loop_body.streams[0].data_type_size,
                llc_config.get_bitlines_per_bank())
            if access_cycles > mesh_cycles:
                mesh_cycles = access_cycles
        total_move_cycles += mesh_cycles

        self.intra_way_cycles = intra_way_cycles
        self.intra_bank_cycles = intra_bank_cycles
        self.mesh_cycles = mesh_cycles
        self.total_move_cycles = total_move_cycles

    def estimate_compute_latency(self):
        loop_body = self.loop_body
        compute_cycles = 0
        data_type_bits = loop_body.streams[0].data_type_size * 8
        # Assume we can skip 0 for multiplication.
        multi_op_latency = data_type_bits * data_type_bits + 5 * data_type_bits - 2
        multi_op_latency /= 4
        for op in loop_body.operations:
            if op == '+' or op == '-':
                compute_cycles += data_type_bits
            elif op == '*':
                compute_cycles += multi_op_latency
        # This is just one iteration. Account the dimension in bitline.
        bitline_iters = 1
        for ind_var in loop_body.loop_struct.ind_vars[0:self.bitline_dim]:
            bitline_iters *= ind_var.n
        compute_cycles *= bitline_iters
        self.compute_cycles = compute_cycles


def main(workload, nsc, multicast):
    import importlib
    wk = importlib.import_module(workload)
    loop_body1, loop_body2 = wk.get_loop_body()
    nsc_interleave = -1
    nsc_anchor = 'whatever'
    if nsc:
        nsc_interleave, nsc_anchor = wk.get_nsc_interleave_anchor()
    print(loop_body1)
    print(loop_body2)
    analyze_two_loop_struct(loop_body1, loop_body2, nsc_interleave, nsc_anchor, multicast)

def analyze_two_loop_struct(loop_body, loop_body2, nsc_interleave, nsc_anchor, multicast):

    llc_config = LLCConfig(
        array_rows=512,
        array_cols=512,
        array_per_way=8,
        tree_degree=2,
        tree_leaf_bandwdith_bytes=8,
        way_per_bank=16,
        mesh_layers=1,
        mesh_rows=8,
        mesh_cols=8,
    )
    
    traffic_model = TrafficModel(
        llc_config=llc_config,
        loop_body=loop_body,
        nsc_interleave=nsc_interleave,
        nsc_anchor=nsc_anchor,
        multicast=multicast,
    )
    traffic_model2 = TrafficModel(
        llc_config=llc_config,
        loop_body=loop_body2,
        nsc_interleave=nsc_interleave,
        nsc_anchor=nsc_anchor,
        multicast=multicast,
    )
    if nsc_interleave == -1:
        traffic_model.build_bitline_data_map()
        traffic_model.build_elem_data_map()
        traffic_model2.build_bitline_data_map()
        traffic_model2.build_elem_data_map()
    else:
        traffic_model.build_nsc_elem_data_map()
        traffic_model2.build_nsc_elem_data_map()
    print(f'Start estimating traffic.')
    traffic_model.estimate_traffic(traffic_model2.array_loc_map)
    print(f'Start analyzing traffic.')
    traffic_model.analyze_traffic()
    print(f'Start estimating move latency.')
    traffic_model.estimate_move_latency()
    print(f'Start estimating compute latency.')
    traffic_model.estimate_compute_latency()
    # print(traffic_model.total_traffic_map)
    # print(f'Intra Way  Traffic {traffic_model.intra_way_traffic}')
    # print(f'Intra Bank Traffic {traffic_model.intra_bank_traffic}')
    print(f'Mesh       Traffic {traffic_model.mesh_traffic}')
    print(f'Intra Way  Cycles  {traffic_model.intra_way_cycles}')
    print(f'Intra Bank Cycles  {traffic_model.intra_bank_cycles}')
    print(f'Mesh       Cycles  {traffic_model.mesh_cycles}')
    print(f'Move       Cycles  {traffic_model.total_move_cycles}')
    print(f'Compute    Cycles  {traffic_model.compute_cycles}')
    print(f'Total      Cycles  {traffic_model.compute_cycles + traffic_model.total_move_cycles}')

if __name__ == '__main__':
    workload = 'hotspot'
    if len(sys.argv) > 1:
        workload = sys.argv[1]
    nsc = False
    if 'nsc' in sys.argv[2:]:
        nsc = True
    multicast = False
    if 'multicast' in sys.argv[2:]:
        multicast = True
    print(f'Working on workload {workload} nsc={nsc} multicast={multicast}')
    main(workload, nsc, multicast)
