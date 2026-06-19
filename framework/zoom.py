import zlib, struct, sys
def read_png(p):
    d = open(p, 'rb').read(); i = 8; w = h = 0; idat = b''
    while i < len(d):
        ln = struct.unpack('>I', d[i:i+4])[0]; tag = d[i+4:i+8]; data = d[i+8:i+8+ln]; i += 12+ln
        if tag == b'IHDR': w, h = struct.unpack('>II', data[:8])
        elif tag == b'IDAT': idat += data
    raw = zlib.decompress(idat); bpp = 4; off = 0
    prev = bytearray(w*bpp); out = bytearray()
    for y in range(h):
        ft = raw[off]; off += 1
        line = bytearray(raw[off:off+w*bpp]); off += w*bpp
        if ft == 1:
            for x in range(bpp, len(line)): line[x] = (line[x]+line[x-bpp]) & 255
        elif ft == 2:
            for x in range(len(line)): line[x] = (line[x]+prev[x]) & 255
        elif ft == 3:
            for x in range(len(line)):
                a = line[x-bpp] if x >= bpp else 0
                line[x] = (line[x]+((a+prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(len(line)):
                a = line[x-bpp] if x >= bpp else 0; b = prev[x]; c = prev[x-bpp] if x >= bpp else 0
                pp = a+b-c; pa = abs(pp-a); pb = abs(pp-b); pc = abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x]+pr) & 255
        out += line; prev = line
    return w, h, out
def write_png(p, w, h, buf):
    raw = bytearray()
    for y in range(h):
        raw.append(0); raw += buf[y*w*4:(y+1)*w*4]
    def ch(t, da): return struct.pack('>I', len(da))+t+da+struct.pack('>I', zlib.crc32(t+da) & 0xffffffff)
    open(p, 'wb').write(b'\x89PNG\r\n\x1a\n'+ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))+ch(b'IDAT', zlib.compress(bytes(raw), 9))+ch(b'IEND', b''))
src, dst, Z = sys.argv[1], sys.argv[2], int(sys.argv[3])
w, h, buf = read_png(src); W, H = w*Z, h*Z; ob = bytearray(W*H*4)
for y in range(h):
    for x in range(w):
        c = buf[(y*w+x)*4:(y*w+x)*4+4]
        for sy in range(Z):
            for sx in range(Z):
                o = ((y*Z+sy)*W+(x*Z+sx))*4; ob[o:o+4] = c
write_png(dst, W, H, ob); print('zoom', src, '->', dst, W, H)
