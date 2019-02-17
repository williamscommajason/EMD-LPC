import struct
#import StringIO
import scipy.io

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

def compress(L, k):

    unsigned = []
    for x in L:
        if x > 0:
            unsigned.append(2*x)
        elif x < 0:
            unsigned.append(2*abs(x) - 1)
        else:
            unsigned.append(x)
    L = unsigned
    
    #f = StringIO.StringIO()
    f = open('rice.bin','w+b')
    global buff, filled
    buff = 0
    filled = 0
    
    for x in L:                # encode all numbers
        rice_code(f, x, k)

    for i in range(8-filled):  # write the last byte (if necessary pad with 1111...)  
        put_bit(f, 1)

    return f

if __name__ == '__main__':
    print(struct.pack('BBB', 0b00010010, 0b00111001, 0b01111111))      #see http://fr.wikipedia.org/wiki/Codage_de_Rice#Exemples
    compress([1,2,3,4,5,1,2,4,3,0],k = 2)
      
    
   
