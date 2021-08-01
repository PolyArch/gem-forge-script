
dot_prod_offsets = [
    'offset_0B',
    'offset_4kB',
    'offset_8kB',
    'offset_12kB',
    'offset_16kB',
    'offset_20kB',
    'offset_24kB',
    'offset_28kB',
    'offset_32kB',
    'offset_36kB',
    'offset_40kB',
    'offset_44kB',
    'offset_48kB',
    'offset_52kB',
    'offset_56kB',
    'offset_60kB',
    'offset_64kB',
    'random0B',
]

stream_cmp_data_placement_simulations = [
    'stream.ruby.single.o8.tlb.8x8c-l256-s64B.f2048-c-gb-cmp',
    'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.fltsc-cmp',
    'stream.ruby.single.o8.tlb.8x8c-l256-s1kB.f2048-c-gb.fltsc-cmp-sync',
]

ssp_so_cmp_transform = {
    'transform': 'stream.ex.static.so.store.cmp',
    'simulations': stream_cmp_data_placement_simulations,
}

def get_configurations():
    configurations = list()
    for b in dot_prod_offsets:
        configurations.append({
            'suite': 'gfm',
            'benchmark': f'omp_dot_prod_avx_{b}',
            'tdg_folder': 'fake.0.tdg.thread64',
            'transforms': [
                ssp_so_cmp_transform,
            ],
        })
    return configurations
