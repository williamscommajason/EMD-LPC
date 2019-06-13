import struct
import math
import numpy as np
from io import BytesIO
import rice_encode
import scipy.io as io
from rice_encode import signed_to_unsigned

class Node(object):
    pass

class InternalNode(Node):

    def __init__(self,value):
        self.value = value
        self.left = None
        self.right = None

class Leaf(Node):

    def __init__(self,code):
        self.code = str(code)

class HyTree:

    def __init__(self, root):

        
        self.root = InternalNode(root)
        self.value = self.root.value 
        self.right = self.root.right
        self.left = self.root.left

def padding(bit):

    return '0' + bit

def rice_code(x,k):

    q = x / (1 << k)
    q = int(q)
    code = ''
    for i in range(q):
        code += '1'
    code += '0'

    for i in range(k-1, -1, -1):
        code += str((x >> i) & 1)

    return code

def make_hybrid_tree(level,k):

    dictionary = dict()
    
    j = 0
    
    while j <= 2**(k+1) - 1:
        code = rice_code(j,k)
        dictionary[code] = j
        j += 1
    
    left_count = ''
    tree = HyTree(left_count)
    
    start = tree
    integer = j
    max_reached = False
    i = 1
    while i <= level:
        start = move(start,'1')
        start,integer,dictionary = make_leaf(start, 0, integer,dictionary)
        
        i += 1

    print(dictionary)
    return tree , dictionary
    
    
def move(node,bit,leaf = False):

    if bit == '0' and leaf == False:
        node.right = InternalNode(node.value + '0')        
        return node.right

    elif bit == '1' and leaf == False:
        node.left = InternalNode(node.value + '1')
        return node.left

    elif bit == '0' and leaf == True:
        node.right = Leaf(node.value + '0')
        return node.right

    else:
        node.left = Leaf(node.value + '1')
        return node.left


def make_leaf(start, k, integer,dictionary):
            
    left_count = len(start.value)
    

    i = left_count
    original = start
    start = move(start,'0')
    even = 2*left_count + k
    odd = 2*left_count + k + 1
    
    even_range = list(range(0,(2**k)*((2**i) -1) - 1))
    odd_range = list(range((2**(k+1))*((2**(i-1))-1),2**(i+k)+1))
    
    
    even_bits = [bin(x)[2:] for x in even_range]
    odd_bits = [bin(x)[2:] for x in odd_range]
    padded_even_bits = []
    padded_odd_bits = []
    
    for even_bit in even_bits:
        if left_count + 1 + len(even_bit) > even:
            even_bits.remove(even_bit)
            continue
        even_pad = even - 1 - left_count

        while len(even_bit) < even_pad:
            even_bit = padding(even_bit)

        padded_even_bits.append(even_bit)


    for odd_bit in odd_bits:
        if left_count + 1 + len(odd_bit) > odd:
            odd_bits.remove(odd_bit)
            continue
        odd_pad = odd - 2 - left_count

        while len(odd_bit) < odd_pad:
            odd_bit = padding(odd_bit)
           
        
        padded_odd_bits.append(odd_bit)
    
    if left_count > 1:

        padded_odd_bits, padded_even_bits = delete_prefixes(padded_odd_bits,padded_even_bits)

    
    for even_bit in padded_even_bits:
        
        start = original.right
        for bit in even_bit[:-1]:
            start = move(start,bit)
        
        start = move(start,even_bit[-1], leaf = True)
        dictionary[str(integer)] = start.code
        integer += 1
        

    for odd_bit in padded_odd_bits:
        
        start = original.right
        for bit in odd_bit[:-1]:
             start = move(start,bit)
        
        start = move(start,odd_bit[-1],leaf = True)
        dictionary[str(integer)] = start.code
        integer += 1
        
        
    return original, integer, dictionary
    
    

def delete_prefixes(padded_odd_bits,padded_even_bits):
    
    for even_bit in padded_even_bits:
        for odd_bit in padded_odd_bits:
            if even_bit == odd_bit[:-1]:
                
                padded_even_bits.remove(even_bit)
                break
    return padded_odd_bits, padded_even_bits

def put_bit(f,b):
    
    global buff, filled
     
    buff = buff | (b << (7-filled))

    if filled == 7:

        f.write(buff.to_bytes(1,byteorder='little'))
        buff = 0
        filled = 0

    else:
        filled += 1


def hybrid_encode(f, x, dictionary):

    
    code = dictionary[str(x)] 

    for bit in code:
        print(bit , code)
        put_bit(f, int(bit))

def pre_compress(L, level, k):
    L = signed_to_unsigned(L)

    fd = BytesIO()
    tree, dictionary = make_hybrid_tree(level,k)

    global buff,filled 
    buff = 0
    filled = 0
 
    for x in L:
        hybrid_encode(fd, x, dictionary)
    
    for i in range(8-filled):
        put_bit(fd,1)

    return fd.tell()

def compress(f,L, level, k):

    L = signed_to_unsigned(L)
    size = pre_compress(L, level, k)
    tree,dictionary = make_hybrid_tree(level,k)

    #f.write(struct.pack('@i',k))
    #f.write(struct.pack('@Q',size))

    buff = 0
    filled = 0

    for x in L:

        hybrid_encode(f, x, dictionary)

    for i in range(8-filled):
        put_bit(f, 1)

    return f

        
        

if __name__ == '__main__':
    from EMDLPC import EMD
    x = np.load('timestream1000.npy')[:100]
    emd = EMD.EMD()
    emd.save(x)
    L = [2,3,4,5,5,6]
    tree = make_hybrid_tree(4,0)
    fp = BytesIO()
    #fp = compress(fp,L,4,0)
    print(fp.tell())
    error = io.loadmat('error.mat')['error'][0]
    error = [int(x) for x in error]
    fp = compress(fp,emd.error,13,0)
    print(fp.tell())
