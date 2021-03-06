import struct
import scipy.io 
import math
import numpy as np
from io import BytesIO
import os

def put_bit(f, b):

    global buff, filled
    buff = buff | (b << (7-filled))

    if (filled == 7):
        #f.write(struct.pack('B',buff))
        f.write(buff.to_bytes(1,byteorder='little'))
        buff = 0
        filled = 0

    else:
        filled += 1

def rice_code(f, x, k):

    q = x / (1 << k)
    q = int(q)
 
    for i in range(q): 
        put_bit(f, 1)
    put_bit(f, 0)
    
    for i in range(k-1, -1, -1):
        put_bit(f, (x >> i) & 1)

def signed_to_unsigned(L):
    
    L = [int(round(x)) for x in L]
    
    unsigned = []
    for x in L:
        if x > 0:
            unsigned.append(2*x)
        elif x < 0:
            unsigned.append(2*abs(x) - 1)
        else:
            unsigned.append(x)

    return unsigned
#

def pre_compress(L):
    fp = BytesIO() 
    L = signed_to_unsigned(L)   
    k = get_k(L)
    
    global buff, filled

    buff = 0
    filled = 0
    
    for x in L:                # encode all numbers
        rice_code(fp, x, k)
        
    
    for i in range(8-filled):  # write the last byte (if necessary pad with 1111...)  
        put_bit(fp, 1)
    
    return fp.tell()

def compress(L,fd):
    
    
    size = pre_compress(L)
    L = signed_to_unsigned(L)
    k = get_k(L)
    
    fd.write(struct.pack('@i',k))
    fd.write(struct.pack('@Q',size))
    
    buff = 0
    filled = 0
    
    for x in L:
        rice_code(fd, x, k)

    for i in range(8-filled):
        put_bit(fd, 1)
   
    

    return fd

def compress_partition(L,fd,partition):

     for i in range(partition):
         pL = L[i*964:(i+1)*964]
         print(pL)
         fd = compress(np.diff(pL),fd)

     return fd

def get_k(error):

    rice_base = [2**i for i in range(64)]

    std = math.sqrt(np.var(error))
    k = rice_base.index(min(rice_base, key = lambda x:abs(x-std)))
    
    return k

if __name__ == '__main__':
    import bitstring
    from bitstring import BitArray
    from bitstring import BitStream
    from rice_decode import decompress
    print(struct.pack('BBB', 0b00010010, 0b00111001, 0b01111111))      #see http://fr.wikipedia.org/wiki/Codage_de_Rice#Exemples
    import numpy as np
    x = np.load('timestream6161.npy')
    dx = np.diff(x)
    import scipy.io as io
    fd = open('rice.bin', 'w+b')
    
    #fd = BytesIO() 
    #print(pre_compress([-1,-2,-3,0]))
    diffs = io.loadmat('diffs.mat')['diffs'][0]
    points = io.loadmat('points.mat')['points'][0]
    mins = io.loadmat('mins.mat')['mins'][0]
    maxs = io.loadmat('maxs.mat')['maxs'][0]
    sub = io.loadmat('sub.mat')['sub'][0]
    error = io.loadmat('error.mat')['error'][0]
    est_x = io.loadmat('estx.mat')['est_x'][0]
    pdf = io.loadmat('pdf.mat')['pdf'][0]
    diffs = diffs[~np.isnan(diffs)]
    diffs = [int(round(x)) for x in diffs]
    print(dx)
    fd = compress([1,2,3,4,5,6,7,8,9,10],fd)
    lists,bString = decompress(fd)
    count = 0
    for i in bString:
        if i == '1':
            count += 1
    print(count)
    print(len(bString) - count)
    print(count/len(bString))
    a = BitStream().join([BitArray(se=i) for i in pdf])
    print(len(a)/8)  
    #fd = compress(np.diff(points),fd)
    #fd = compress(np.diff(mins),fd)
    #fd = compress(np.diff(maxs),fd)
    
   
    #a = BitStream().join([BitArray(se=i) for i in diffs])
    #print(len(a)/8)
    ''' 
    x = np.load('timestream1019.npy')
    dx = np.diff(x)
    x = [int(round(i)) for i in x]
    dx = [int(round(i)) for i in x]
    #compress(dx,'dtimestream1019.bin.emd')
    #compress(x,'timestream1004.bin.emd')
    
    imf0 = scipy.io.loadmat('imf0.mat')['imf0'][0]
    ddct = scipy.io.loadmat('ddct.mat')['ddct'][0]
    nee = scipy.io.loadmat('nee.mat')['nee'][0]
    
    compress(ddct,'ddct.bin.emd')
    compress(nee,'nee.bin')
    ddct = [int(round(x/2)) for x in ddct]
    a = BitStream().join([BitArray(se=i) for i in ddct])
    '''
    '''
    subtracted = io.loadmat('subtracted.mat')['subtracted'][0]
    subtracted = subtracted[~np.isnan(subtracted)]
    subtracted = [int(round(x)) for x in subtracted]
    print(len(subtracted))
    diffs = io.loadmat('diffs.mat')['diffs'][0]
    #diffs = diffs[~np.isnan(diffs)]
    diffs = [int(round(x)) for x in diffs]
    print(diffs)
    compress(diffs,'diffs.bin')
    times = io.loadmat('times.mat')['ts'][0]
    compress(times,'times.bin')
    '''
    '''
    data = io.loadmat('summed.mat')
    residual = data['summed'][0]
    print(residual.tolist())
    nerror = [int(round(x)) for x in residual] 
    #nerror = (np.diff(nerror)).tolist()
    print(len(nerror))
    '''
    #signal = data['signal'][0]
    #signal = signal[:1400]
    #error = signal-residual
    
    #f_error = []
    #for i in range(len(error)):
    #    f_error.append(int(round(error[i])))
    #print(f_error)
    #array = np.fromfile('timestream.bin',dtype=np.int32)
    #array = np.diff(array)
    #array = [int(x) for x in array]
    '''
    error = io.loadmat('truncated_error.mat')['terror'][0]
    filt = io.loadmat('filterr.mat')['a'][0]
    print(len(error))
    compress(error,'rice.bin') 
    compress(filt,'trunc.bin')
    '''
