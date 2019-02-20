import struct
#import StringIO
import scipy.io
import math
import numpy as np

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

    unsigned = []
    for x in L:
        if x > 0:
            unsigned.append(2*x)
        elif x < 0:
            unsigned.append(2*abs(x) - 1)
        else:
            unsigned.append(x)

    return unsigned

def compress(L):
    
    L = signed_to_unsigned(L)    
    #f = StringIO.StringIO()
    #f = open('rice.bin','w+b')
    f,k = get_k(L)
    global buff, filled
    buff = 0
    filled = 0
    
    for x in L:                # encode all numbers
        rice_code(f, x, k)

    for i in range(8-filled):  # write the last byte (if necessary pad with 1111...)  
        put_bit(f, 1)

    return f

def get_k(error):

    rice_base = [2**i for i in range(16)]

    std = math.sqrt(np.var(error))
    k = rice_base.index(min(rice_base, key = lambda x:abs(x-std)))

    f = open('rice.bin', 'w+b')
    f.write(struct.pack('@i', k))

    return f,k

if __name__ == '__main__':
    print(struct.pack('BBB', 0b00010010, 0b00111001, 0b01111111))      #see http://fr.wikipedia.org/wiki/Codage_de_Rice#Exemples
    compress([1,2,3,4,5,1,2,4,3,0])
    import scipy.io as io
    data = io.loadmat('r99.mat')
    residual = data['residual'][0]
    residual = residual[:1400]
    signal = data['signal'][0]
    signal = signal[:1400]
    error = signal-residual
    
    f_error = []
    for i in range(len(error)):
        f_error.append(int(round(error[i])))
    #print(f_error)
    compress(f_error) 
   
