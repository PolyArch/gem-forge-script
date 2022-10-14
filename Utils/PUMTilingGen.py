
def generate3DTileSize(x, y, z, bitlines):
    ret = list()
    xx = 1
    while xx <= bitlines:
        yy = 1
        while yy <= bitlines // xx:
            zz = bitlines // xx // yy

            if xx <= x and yy <= y and zz <= z:
                ret.append((xx, yy, zz))

            yy *= 2
        xx *= 2

    return ret

def gen(benchmark):
    if benchmark == 'conv3d':
        return generate3DTileSize(256, 256, 64, 512)
    elif benchmark == 'stencil3d':
        return generate3DTileSize(512, 512, 16, 512)

if __name__ == '__main__':
    print('conv3d')
    ret = generate3DTileSize(256, 256, 64, 512)
    print(','.join([f'"{xx}x{yy}"' for xx, yy, zz in ret]))
    print('stencil3d')
    ret = generate3DTileSize(512, 512, 16, 512)
    print(','.join([f'"{xx}x{yy}"' for xx, yy, zz in ret]))

