
from ComputeCacheModel import LLCConfig

import itertools
import functools
import operator
import json

class AffinePattern:
    """
    This represents an affine pattern:
    start : stride1 : trip1 : ... : stride_n : trip_n

    The formula:
        start + (i % trip1) * stride1 + ((i / (trip1)) % trip2) * stride2 + ... + ((i / (trip1 x ... x trip_{n-1})) % trip_n) * stride_n
    """
    def __init__(self, start, params):
        self.start = start
        self.params = params

    def __call__(self, i):
        result = self.start
        acc_trip = 1
        for stride, trip in self.params:
            result += stride * ((i // acc_trip) % trip)
            acc_trip *= trip
        return result

    """
    This represents a canonical tiling pattern:
    1. No reuse (hence one-to-one mapping)
    2. Must be tiling form:
        First tiling for [T1 x T2 x ... x Tn], then span to the entire N dimention array of size (S1 x S2 x ... x Sn).
        Examples:
            1D: 0 : 1 : T1 : T1 : S1/T1
            2D: 0 : 1 : T1 : S1 : T2    : T1    : S1/T1 : T2xS1 : S2/T2
            3D: 0 : 1 : T1 : S1 : T2    : S1xS2 : T3    : T1    : S1/T1 : T2xS1 : S2/T2 : T3xS1xS2 : S3/T3
        
        The formal definition:
            0 : 1 : T1 : S1 : T2 : ... : S1x...S_{n-1} : Tn : T1 : S1/T1 : ... : S1x...xS_{n-1}xTn : Sn/Tn

        Notice that some special cases can be rewritten into canonical form by inserting Tx=1 dimension.
        For example: Column major access of 2D array:
            Column-major:   0 : S1 : S2 : 1  : S1
            Canonical:      0 : 1  : 1  : S1 : S2 : 1 : S1 : S1xS2 : 1  (T1 = 1, T2 = S2)
        
    Given a canonical tiling pattern, we can construct the reverse pattern via:
    1st dimension keep the same                  0 : 1 : T1
    2nd dimension move to the tile size            : T1xT2x...xTn : S1/T1
    3rd dimension move to the 2nd tile dimension   : T1 : T2
    4th dimension move to the S2/T2 tile           : S1xT2x...xTn : S2/T2
    5th dimension move to the 3rd tile dimension   : T1xT2 : T3
    6th dimension move to the S3/T3 tile           : S1xS2x...xTn : S3/T3

    TODO: How to support nested tiling?
    """
    def is_canonical_tile(self):
        if self.start != 0:
            return False
        if len(self.params) % 2 != 0:
            return False
        if len(self.params) == 0:
            return False
        dimension = len(self.params) // 2
        tile_sizes, array_sizes = self.get_canonical_tile_and_array_size()
        for i in range(dimension):
            stride, _ = self.params[i]
            correct_stride = functools.reduce(operator.mul, array_sizes[:i], 1)
            if stride != correct_stride:
                return False
        for i in range(dimension):
            stride, _ = self.params[i + dimension]
            correct_stride = functools.reduce(operator.mul, array_sizes[:i], tile_sizes[i])
            if stride != correct_stride:
                return False
        return True

    def get_canonical_tile_and_array_size(self):
        dimension = len(self.params) // 2
        tile_sizes = [trip for _, trip in self.params[:dimension]]
        tile_counts = [trip for _, trip in self.params[dimension:]]
        array_sizes = [t * s for t, s in zip(tile_sizes, tile_counts)]
        return (tile_sizes, array_sizes)

    @staticmethod
    def construct_canonical_tile(tile_sizes, array_sizes):
        assert(len(tile_sizes) == len(array_sizes))
        for tile_size, array_size in zip(tile_sizes, array_sizes):
            assert(array_size % tile_size == 0)
            assert(array_size >= tile_size)
        start = 0
        params = list()
        dimension = len(tile_sizes)
        for i in range(dimension):
            stride = functools.reduce(operator.mul, array_sizes[:i], 1)
            params.append((stride, tile_sizes[i]))
        for i in range(dimension):
            stride = functools.reduce(operator.mul, array_sizes[:i], tile_sizes[i])
            trip = array_sizes[i] // tile_sizes[i]
            params.append((stride, trip))
        return AffinePattern(start, params)

    def revert_canonical_tile(self):
        assert(self.is_canonical_tile())
        dimension = len(self.params) // 2
        tile_sizes, array_sizes = self.get_canonical_tile_and_array_size()

        start = 0
        params = list()

        for i in range(dimension):
            stride1 = 1
            for j in range(i):
                stride1 *= tile_sizes[j]
            params.append((stride1, tile_sizes[i]))

            stride2 = 1
            for j in range(dimension):
                stride2 *= array_sizes[j] if j < i else tile_sizes[j]
            trip2 = array_sizes[i] // tile_sizes[i]
            params.append((stride2, trip2))
        
        return AffinePattern(start, params)

    def get_strides(self):
        return [s for s, _ in self.params]

    def get_trips(self):
        return [t for _, t in self.params]

    def get_total_trip(self):
        total_trip = 1
        for _, trip in self.params:
            total_trip *= trip
        return total_trip

    def check_is_reverse(self, reverse):
        for i in range(self.get_total_trip()):
            f = self(i)
            reverse_i = reverse(f)
            if reverse_i != i:
                return False
        return True

    def __str__(self):
        x = ':'.join([f'{s}:{t}' for s, t in self.params])
        return f'{self.start}:{x}'

    @staticmethod
    def parse(s):
        xs = [int(x) for x in s.split(':')]
        assert(len(xs) % 2 == 1)
        start = xs[0]
        params = list()
        for i in range(1, len(xs), 2):
            params.append((xs[i], xs[i + 1]))
        return AffinePattern(start, params)

    @staticmethod
    def get_array_position(array_sizes, linear_pos):
        """
        Given a linear position, return the position according to the array dimension.
        """
        dimension = len(array_sizes)
        # This is S1x...xSi
        inner_array_sizes = [functools.reduce(operator.mul, array_sizes[:i], 1) for i in range(dimension)]
        pos = list()
        cur_pos = linear_pos
        for i in range(dimension - 1, -1, -1):
            p = cur_pos // inner_array_sizes[i]
            pos.insert(0, p)
            cur_pos = cur_pos % inner_array_sizes[i]
        return pos

    def get_sub_region_start_to_array_size(self, array_sizes):
        return AffinePattern.get_array_position(array_sizes, self.start)

    def is_canonical_sub_region_to_array_size(self, array_sizes, allow_reuse=False):
        dimension = len(array_sizes)
        if len(self.params) != dimension:
            return False
        # This is S1x...xSi
        inner_array_sizes = [functools.reduce(operator.mul, array_sizes[:i], 1) for i in range(dimension)]
        strides = self.get_strides()
        trips = self.get_trips()
        for s, t in zip(strides, inner_array_sizes):
            if s == t:
                continue
            # Check if this is 0 stride and we allow reuse.
            if allow_reuse and s == 0:
                continue
            return False
        starts = self.get_sub_region_start_to_array_size(array_sizes)
        for p, q, s in zip(starts, trips, array_sizes):
            if p + q > s:
                return False
        return True

    @staticmethod
    def construct_canonical_sub_region(array_sizes, starts, trips):
        dimension = len(array_sizes)
        assert(len(starts) == len(trips))
        assert(len(starts) == dimension)
        # This is S1x...xSi
        inner_array_sizes = [functools.reduce(operator.mul, array_sizes[:i], 1) for i in range(dimension)]
        start = 0
        params = list()
        for i in range(dimension):
            start += starts[i] * inner_array_sizes[i]
            stride = inner_array_sizes[i]
            trip = trips[i]
            params.append((stride, trip))
        return AffinePattern(start, params)

    @staticmethod
    def break_continuous_range_into_canonical_sub_regions(array_sizes, start, trip):
        ps = AffinePattern.get_array_position(array_sizes, start)
        qs = AffinePattern.get_array_position(array_sizes, start + trip)
        return AffinePattern.recursive_break_continuous_range_into_canonical_sub_regions(array_sizes, ps, qs, dim=0)

    @staticmethod
    def recursive_break_continuous_range_into_canonical_sub_regions(array_sizes, ps, qs, dim):
        """
        This method breaks a continuous range [start, start + trip) into a list of
        sub regions. Specifically, it aligns the start and and to each dimension
        by creating new sub regions if the mod is not zero.

        |--------|-------|-------|-------|-------|-------|-------|--------|
                 A   P   B       C   Q   D
        
        Create a sub region for [P, B), [C, Q) and keep [B, C) continuous.
        """
        sub_regions = list()
        dimension = len(array_sizes)

        p = ps[dim]
        q = qs[dim]
        t = array_sizes[dim]

        print(f'dim={dim} array={array_sizes} ps={ps} qs={qs}')

        high_dim_match = True
        for i in range(dim + 1, dimension):
            if ps[i] != qs[i]:
                high_dim_match = False
                break

        if p != 0 and q != 0 and high_dim_match:
            # One sub region [P, Q)
            starts = ps.copy()
            trips = [array_sizes[i] if i < dim else 1 for i in range(dimension)]
            trips[dim] = q - p
            sub_regions.append(AffinePattern.construct_canonical_sub_region(array_sizes, starts, trips))
        else:
            if p != 0:
                # One sub region [P, B)
                starts = ps.copy()
                trips = [array_sizes[i] if i < dim else 1 for i in range(dimension)]
                trips[dim] = t - p
                sub_regions.append(AffinePattern.construct_canonical_sub_region(array_sizes, starts, trips))

            if q != 0:
                starts = qs.copy()
                starts[dim] = 0
                trips = [array_sizes[i] if i < dim else 1 for i in range(dimension)]
                trips[dim] = q
                sub_regions.append(AffinePattern.construct_canonical_sub_region(array_sizes, starts, trips))

            if not high_dim_match:
                # There is more to match.
                assert(dim + 1 < dimension)
                bs = ps.copy()
                if p != 0:
                    bs[dim] = 0
                    bs[dim + 1] += 1
                    # Adjust starting point if we need to carry.
                    for i in range(dim + 1, dimension - 1):
                        if bs[i] == array_sizes[i]:
                            bs[i] = 0
                            bs[i + 1] += 1
                cs = qs.copy()
                if q != 0:
                    cs[dim] = 0
                bs_eq_cs = True
                for b, c in zip(bs, cs):
                    if b != c:
                        bs_eq_cs = False
                        break
                if not bs_eq_cs:
                    sub_regions += AffinePattern.recursive_break_continuous_range_into_canonical_sub_regions(array_sizes, bs, cs, dim + 1)

        return sub_regions


    @staticmethod
    def intersect_sub_regions(array_sizes, region1, region2):
        assert(region1.is_canonical_sub_region_to_array_size(array_sizes))
        assert(region2.is_canonical_sub_region_to_array_size(array_sizes))
        starts1 = region1.get_sub_region_start_to_array_size(array_sizes)
        trips1 = region1.get_trips()
        starts2 = region2.get_sub_region_start_to_array_size(array_sizes)
        trips2 = region2.get_trips()
        intersect_starts = list()
        intersect_trips = list()
        for i in range(len(array_sizes)):
            s1 = starts1[i]
            t1 = trips1[i]
            s2 = starts2[i]
            t2 = trips2[i]
            if s1 >= s2 + t2 or s2 >= s1 + t1:
                # None means empty intersection.
                return None
            ss = max(s1, s2)
            tt = min(s1 + t1, s2 + t2) - ss
            intersect_starts.append(ss)
            intersect_trips.append(tt)
        return AffinePattern.construct_canonical_sub_region(array_sizes, intersect_starts, intersect_trips)

    def generate_all_values(self):
        values = list()
        for i in range(self.get_total_trip()):
            values.append(self(i))
        return values

class DataMoveCompiler:
    """
    Take in a canonical tiling pattern and the LLC SRAM configuration,
    generate the data move instructions for certain aligning requirement.
    Key assumptions:
    1. Each tile is placed across one SRAM array's bitlines.
    2. Align requiremnts are specified through a combination of movement in each dimension.

    Given one source stream and one destination stream, we analyze the reuse
    and align requirements between them.

    Define CanonicalSubRegionPattern to be a pattern that iterates through
    a rectangular sub-region of the N-dimension array. It must be of pattern:
    
    P1 + P2xS1 + P3xS2xS1 + ... PnxS_{n-1}x...xS1
        : 1              : Q1
        : S1             : Q2
        : S1xS2          : Q3
        : ...
        : S1x...xS_{n-1} : Qn
    Pi >= 0, Qi > 0, Pi + Qi <= Si for i in [1, n]
    
    This defines a non-tiling region [P1, P1+Q1)x...x[Pn, Pn+Qn), and we immediately
    see that there is no reuse within this pattern.
    
    So far we assume the destination stream must be a CanonicalSubRegionPattern,
    while the source stream may reuse some dimension (0 stride):

    P1 + P2xS1 + P3xS2xS1 + ... PnxS_{n-1}x...xS1
        : 1              : Q1
        : 0              : Q2  // Reuse at this dimension.
        : 0              : Q3  // Another reuse.
        : ...
        : S1x...xS_{n-1} : Qn

    Also, the source and destination stream may have different start point, but
    the trip parameters across all dimension must match.

    For source stream with reuse, we replace the reused dimension with
    (stride=1, trip=1), which turns it back to a CanonicalSubRegionPattern.

    Then we analyze the difference between their start point to get the base align
    requirement, which is then multicasted according to the reuse dimension.

    Finally:
        The align requirement with multicast is used to generate the general
        commands applies to all SRAM arrays.
        The source CanonicalSubRegionPattern is used to mask the general commands.
        The LLC configuration is used to split the general commands according to
        the hardware topology and network.

    TODO: So far we assume no mixed dimension.
    """
    def __init__(self, llc_config, tile_pattern):
        self.llc_config = llc_config
        self.tile_pattern = tile_pattern
        assert(self.tile_pattern.is_canonical_tile())
        self.dimension = len(self.tile_pattern.params) // 2
        self.tile_sizes, self.array_sizes = self.tile_pattern.get_canonical_tile_and_array_size()

    def compile(self, src_stream, dst_stream):
        return self.analyze_stream_pair(src_stream, dst_stream)

    def get_sub_region_start(self, pattern):
        # This is S1x...xSi
        return pattern.get_sub_region_start_to_array_size(self.array_sizes)

    def is_canonical_sub_region(self, pattern, allow_reuse=False):
        return pattern.is_canonical_sub_region_to_array_size(self.array_sizes, allow_reuse)

    def fix_reuse_in_canonical_sub_region(self, pattern):
        assert(self.is_canonical_sub_region(pattern, allow_reuse=True))
        fixed_params = list()
        for s, t in pattern.params:
            stride = 1 if s == 0 else s
            trip = 1 if s == 0 else t
            fixed_params.append((stride, trip))
        return AffinePattern(pattern.start, fixed_params)

    def can_handle_stream_pair(self, src_stream, dst_stream):
        assert(self.is_canonical_sub_region(dst_stream))
        assert(self.is_canonical_sub_region(src_stream, allow_reuse=True))
        assert(len(src_stream.params) == len(dst_stream.params))
        src_trips = src_stream.get_trips()
        dst_trips = dst_stream.get_trips()
        for s, t  in zip(src_trips, dst_trips):
            assert(s == t)

    def analyze_stream_pair(self, src_stream, dst_stream):
        self.can_handle_stream_pair(src_stream, dst_stream)

        src_starts = self.get_sub_region_start(src_stream)
        dst_starts = self.get_sub_region_start(dst_stream)
        assert(len(src_starts) == len(dst_starts))
        base_aligns = list()
        for i in range(len(src_starts)):
            if src_starts[i] != dst_starts[i]:
                base_aligns.append((i, dst_starts[i] - src_starts[i]))
        assert(len(base_aligns) <= 1)

        reuses = list()
        for i in range(len(src_stream.params)):
            stride, trip = src_stream.params[i]
            if stride == 0:
                # This is reuse dimension.
                reuses.append((i, trip))
        assert(len(reuses) <= 1)
        if reuses and base_aligns:
            assert(len(reuses) == len(base_aligns))
            for r, a in zip(reuses, base_algins):
                # Assert that reuse and base align are along the same dimension
                assert(r[0] == a[0])

        # First compile for the align and reuse.
        commands = self.compile_align_and_reuse(base_aligns, reuses)

        # Then we limit the command by source CanonicalSubRegion.
        no_reuse_src_sub_region = self.fix_reuse_in_canonical_sub_region(src_stream)

        commands = self.mask_commands_by_sub_region(commands, no_reuse_src_sub_region)

        print('--------------------- Before Mapped to LLC ----------------------')
        print(json.dumps(commands, indent=2, sort_keys=True))

        commands = self.map_commands_to_llc(commands)

        print('--------------------- After Mapped to LLC ----------------------')
        print(json.dumps(commands, indent=2, sort_keys=True))

        # Map commands to LLC configuration.
        return commands

    def compile_align_and_reuse(self, base_aligns, reuses):
        assert(len(reuses) == 0)
        assert(len(base_aligns) == 1)
        dim, distance = base_aligns[0]
        return self.compile_one_align(dim, distance)

    def compile_one_align(self, dim, distance):
        """
        Generate hierarchical data move commands:
        1. Within each tile (SRAM array).
        2. Boundary case:
            For dimensions between [0, dim), data is continous layout.
            For dimensions between (dim, D), data is incontinuous.
        Thus, we need one command to move [0, dim) to the correct location.
        Finally, we need to split traffic across tiles with different level
        of LLC configuration.
        """
        dimension = self.dimension
        tile_sizes = self.tile_sizes
        array_sizes = self.array_sizes

        assert(dim < dimension)
        abs_dist = abs(distance)
        if abs_dist < tile_sizes[dim]:
            return self.handle_align_smaller_than_tile_size(dim, distance)
        else:
            assert(abs_dist % tile_sizes[dim] == 0)
            assert(False)

    def handle_align_smaller_than_tile_size(self, dim, distance):
        dimension = self.dimension
        tile_sizes = self.tile_sizes
        array_sizes = self.array_sizes

        commands = list()

        abs_dist = abs(distance)
        assert(abs_dist) < tile_sizes[dim]
        # Traffic within this tile.
        bitlines = distance
        for i in range(dim):
            bitlines *= tile_sizes[i]
        commands.append({
            'type': 'intra-array',
            'dist': bitlines,
            'mask': 'all',
        })

        # Boundary case.
        # move_size = functools.reduce(operator.mul, tile_sizes[:dim], abs_dist)
        # inner_tile_size = functools.reduce(operator.mul, tile_sizes[:dim+1], 1)
        # remain_tile_size = inner_tile_size - move_size

        move_tile_dist = 1
        for i in range(dim):
            move_tile_dist *= array_sizes[i] // tile_sizes[i]

        # # Generate the cross product of outer dimension.
        # outer_tile_size = functools.reduce(operator.mul, tile_sizes[dim+1:], 1)

        # front_pattern = AffinePattern(
        #     start=0,
        #     params=[
        #         (1, move_size),
        #         (inner_tile_size, outer_tile_size),
        #     ]
        # ).__str__()

        # back_pattern = AffinePattern(
        #     start=remain_tile_size,
        #     params=[
        #         (1, move_size),
        #         (inner_tile_size, outer_tile_size),
        #     ]
        # ).__str__()

        # Construct the sub-region of front and back.
        front_starts = list()
        front_trips = list()
        for i in range(dim):
            front_starts.append(0)
            front_trips.append(tile_sizes[i])
        front_starts.append(0)
        front_trips.append(abs_dist)
        for i in range(dim + 1, dimension):
            front_starts.append(0)
            front_trips.append(tile_sizes[i])
        
        back_starts = list()
        back_trips = list()
        for i in range(dim):
            back_starts.append(0)
            back_trips.append(tile_sizes[i])
        back_starts.append(tile_sizes[dim] - abs_dist)
        back_trips.append(abs_dist)
        for i in range(dim + 1, dimension):
            back_starts.append(0)
            back_trips.append(tile_sizes[i])
        
        front_pattern = AffinePattern.construct_canonical_sub_region(tile_sizes, front_starts, front_trips)
        back_pattern = AffinePattern.construct_canonical_sub_region(tile_sizes, back_starts, back_trips)


        if distance > 0:
            # Move forward.
            src_pattern = back_pattern
            dst_pattern = front_pattern
        else:
            # Move backward.
            dst_pattern = back_pattern
            src_pattern = front_pattern


        commands.append({
            'type': 'inter-array',
            'tile_dist': move_tile_dist,
            'src_bitline_mask': src_pattern.__str__(),
            'dst_bitline_mask': dst_pattern.__str__(),
        })

        return commands

    def mask_commands_by_sub_region(self, commands, sub_region):
        """
        Recursively mask commands by sub_region dimensions.
        Starting from the outer-most dimension, let the current dimension be i.

        The sub region requires [Pi, Pi+Qi).
        Let the tile size be Ti, array size Si.

        Define:
        Ai = Pi // Ti
        Bi = (Pi + Ti - 1) // Ti
        Ci = (Pi + Qi) // Ti
        Di = (Pi + Qi + Ti - 1) // Ti

        In terms of an axis:

        |-------|-------|-------|-------|-------|-------|-------|
                A   P   B               C  P+Q  D

        If B < C:
            Mask [P,    BxTi)
            Mask [CxTi, P+Q)
            No Mask [BxTi, CxTi)
        If B = C:
            Mask [P,    BxTi)
            Mask [CxTi, P+Q)
        If B < C:
            Mask [P, P+Q)

        And then go to the next dimension.
        """
        return self.recursive_mask_commands_at_dim(
            commands, sub_region, self.dimension - 1, list(), list())

    def merge_masks(self, masks, inner_sizes):
        start = 0
        params = list()
        for i in range(self.dimension):
            dim_start, dim_stride, dim_trip = masks[i]
            start += dim_start * inner_sizes[i]
            stride = dim_stride * inner_sizes[i]
            trip = dim_trip
            params.append((stride, trip))
        return AffinePattern(start, params)

    def merge_bitline_masks(self, bitline_masks):
        assert(len(bitline_masks) == self.dimension)
        inner_tile_sizes = [functools.reduce(operator.mul, self.tile_sizes[:i], 1) for i in range(self.dimension)]
        return self.merge_masks(bitline_masks, inner_tile_sizes)

    def merge_tile_masks(self, tile_masks):
        assert(len(tile_masks) == self.dimension)
        tile_nums = [(a + t - 1) // t for a, t in zip(self.array_sizes, self.tile_sizes)]
        inner_tile_nums = [functools.reduce(operator.mul, tile_nums[:i], 1) for i in range(self.dimension)]
        return self.merge_masks(tile_masks, inner_tile_nums)

    def intersect_bitline_masks(self, bitline_mask1, bitline_mask2):
        return AffinePattern.intersect_sub_regions(self.tile_sizes, bitline_mask1, bitline_mask2)

    def recursive_mask_commands_at_dim(self, commands, sub_region, dim, bitline_masks, tile_masks):
        """
        This implements the above mask algorithm, and accumulate mask pattern along each dimension.
        At the end, we construct the overall mask pattern by merging bitline_masks and tile_masks.

        An key optimization is to check the merged bitline mask against inter-array commands'
        source bitline mask. If they have no intersection, we can ignore the command.

        This is done by leveraging the fact that both bitline masks are canonical sub-region
        within that tile, and take their interection.

        """
        if dim == -1:
            merged_bitline_masks = self.merge_bitline_masks(bitline_masks)
            merged_tile_masks = self.merge_tile_masks(tile_masks)
            masked_commands = list()
            for command in commands:
                c = command.copy()
                c['bitline_mask'] = merged_bitline_masks.__str__()
                c['tile_mask'] = merged_tile_masks.__str__()
                if c['type'] == 'inter-array':
                    src_bitline_mask = AffinePattern.parse(c['src_bitline_mask'])
                    intersect = self.intersect_bitline_masks(src_bitline_mask, merged_bitline_masks)
                    if intersect is None:
                        continue
                    c['bitline_mask'] = intersect.__str__()
                masked_commands.append(c)
            return masked_commands

        ps = self.get_sub_region_start(sub_region)
        qs = sub_region.get_trips()
        p = ps[dim]
        q = qs[dim]
        t = self.tile_sizes[dim]
        a = p // t
        b = (p + t - 1) // t
        c = (p + q) // t
        d = (p + q + t - 1) // t

        tile_p = p - a * t
        tile_pq = p + q - c * t

        masked_commands = list()
        if b <= c:
            # [P, BxTi)
            if a < b:
                bitline_mask = (tile_p, 1, t - tile_p)
                tile_mask = (a, 1, 1)
                masked_commands += self.recursive_mask_commands_at_dim(
                    commands, sub_region, dim - 1,
                    [bitline_mask] + bitline_masks,
                    [tile_mask] + tile_masks
                )
            # [CxTi, P+Q)
            if c < d:
                bitline_mask = (0, 1, tile_pq)
                tile_mask = (c, 1, 1)
                masked_commands += self.recursive_mask_commands_at_dim(
                    commands, sub_region, dim - 1,
                    [bitline_mask] + bitline_masks,
                    [tile_mask] + tile_masks
                )
            if b < c:
                # [BxTi, CxTi)
                bitline_mask = (0, 1, t) # Essentially no mask.
                tile_mask = (b, 1, c - b)
                masked_commands += self.recursive_mask_commands_at_dim(
                    commands, sub_region, dim - 1,
                    [bitline_mask] + bitline_masks,
                    [tile_mask] + tile_masks
                )
        else:
            # [P, P+Q)
            bitline_mask = (tile_p, 1, tile_pq)
            tile_mask = (a, 1, 1)
            masked_commands += self.recursive_mask_commands_at_dim(
                commands, sub_region, dim - 1,
                [bitline_mask] + bitline_masks,
                [tile_mask] + tile_masks
            )
        return masked_commands

    def map_commands_to_llc(self, commands):
        """
        Here we map commands to LLC.

        Since the number of tiles in each dimension may not be a divisor of
        the LLC SRAM arrays configuration, it is very challenging to derive
        an analytical close form to commands in all LLC slice. Therefore,
        here we explicitly generate the mask for each LLC slice.

        We do this in the following steps.
        1. Each LLC slice will have a number of SRAM arrays, and tiles are
        mapped continuously to these slices, with one tile per SRAM array.
        2. We first split the SRAM arrays into canonical sub-regions in the
        tile coordinate, then for each sub-regions we take the intersection
        with the command's tile mask to generate the specific tile mask
        within that LLC slice.
        3. With in each slice, we then split commands according to the tree
        structure.

        """

        tile_per_llc_bank = self.llc_config.get_array_per_bank()
        total_llc_banks = self.llc_config.get_total_banks()

        tile_nums = [s // t for s, t in zip(self.array_sizes, self.tile_sizes)]

        # Construct the sub-region for each LLC bank.
        llc_bank_sub_regions = list()
        for i in range(total_llc_banks):
            sub_regions_in_llc_bank = \
                AffinePattern.break_continuous_range_into_canonical_sub_regions(
                    tile_nums, i * tile_per_llc_bank, tile_per_llc_bank
                )
            llc_bank_sub_regions.append(sub_regions_in_llc_bank)

        # Process all commands.
        for command in commands:
            self.map_command_to_llc(command, llc_bank_sub_regions)
        return commands

    def map_command_to_llc(self, command, llc_bank_sub_regions):
        tile_per_llc_bank = self.llc_config.get_array_per_bank()
        total_llc_banks = self.llc_config.get_total_banks()

        tile_nums = [s // t for s, t in zip(self.array_sizes, self.tile_sizes)]
        command_tile_mask = AffinePattern.parse(command['tile_mask'])

        llc_command = dict()

        for i in range(total_llc_banks):
            llc_tiles = list()
            for llc_sub_region in llc_bank_sub_regions[i]:
                intersect = AffinePattern.intersect_sub_regions(tile_nums, command_tile_mask, llc_sub_region)
                if intersect is None:
                    continue
                llc_tiles.append(intersect.__str__())
            llc_command[i] = llc_tiles
        
        command['llc_command'] = llc_command
        if command['type'] == 'inter-array':
            self.split_inter_array_command_to_llc(command)

    def split_inter_array_command_to_llc(self, command):
        """
        First start to scan each level of the tree in the way.
        Then handle inter-ways.
        Finally across LLC banks.

        At each level, we model it as this:

        [  S  ] [  S  ] [  S  ] ... [  S  ] [  S  ] [  S  ]
           |       |       |           |       |       |
            -------------------------------------------
                                DxS

        Each sub-tree has S arrays, with D sub-trees.

        If tile_dist >= DxS: Nothing to move within this level.

        Otherwise, define
            M = tile_dist // S
            N = tile_dist % S.

        If tile_dist >= S
            The first part:
                0 : 1 : S-N : S : D-M
            The second part:
                S-N : 1 : N : S : D-M-1
        If tile_dist < S:
            Only part:
                S-N : 1 : N : S : D-1

        This can be mreged into:
        The first part only comes when tile_dist >= S:
                0 : 1 : S-N : S : D-M
        The second part is always the same:
                S-N : 1 : N : S : D-M-1

        """
        tile_dist = command['tile_dist']
        llc_config = self.llc_config
        inter_array_splits = dict()

        def split(s, d, tile_dist):
            splits = list()
            if tile_dist < s * d:
                m = tile_dist // s
                n = tile_dist % s
                # First part.
                if tile_dist >= s:
                    pattern1 = AffinePattern(
                        start=0,
                        params=[(1, s-n), (s, d-m)]
                    )
                    splits.append(pattern1.__str__())
                # Second part.
                pattern2 = AffinePattern(
                    start=s-n,
                    params=[(1, n), (s, d-m-1)],
                )
                splits.append(pattern2.__str__())
            return splits

        cur_level = 0
        prev_level_tiles = 1
        cur_level_tiles = llc_config.tree_degree
        while cur_level_tiles <= llc_config.array_per_way:
            s = prev_level_tiles
            d = llc_config.tree_degree
            splits = split(s, d, tile_dist)
            inter_array_splits[cur_level] = splits

            cur_level += 1
            prev_level_tiles = cur_level_tiles
            cur_level_tiles *= llc_config.tree_degree

        # Inter LLC ways.
        splits = split(llc_config.array_per_way, llc_config.way_per_bank, tile_dist)
        inter_array_splits[cur_level] = splits
        cur_level += 1

        # Inter LLC banks.
        splits = split(
            llc_config.get_array_per_bank(),
            llc_config.get_total_banks(),
            tile_dist
        )
        inter_array_splits[cur_level] = splits
        cur_level += 1

        command['inter_array_splits'] = inter_array_splits

def main():
    S1 = 512
    S2 = 512
    S3 = 16
    tile_pattern = AffinePattern.construct_canonical_tile(
        tile_sizes=[8, 8, 8],
        array_sizes=[S1, S2, S3],
    )
    print(tile_pattern)
    mapping = tile_pattern.revert_canonical_tile()
    # assert(tile_pattern.check_is_reverse(mapping))

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
    mover = DataMoveCompiler(llc_config, tile_pattern)
    src_stream = AffinePattern(
        start=0,
        params=[
            (1, S1),
            (S1, S2 - 1),
            (S1 * S2, S3),
        ],
    )
    dst_stream = AffinePattern(
        start=S1,
        params=[
            (1, S1),
            (S1, S2 - 1),
            (S1 * S2, S3),
        ],
    )
    commands = mover.compile(src_stream, dst_stream)
    print(json.dumps(commands, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
