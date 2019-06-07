import struct
import math
import numpy as np
from io import BytesIO
import rice_encode

class Node:

    def __init__(self,value):
        self.value = value
        self.left = None
        self.right = None

class HyTree:

    def __init__(self, root):

        
        self.root = Node(root)
        self.value = self.root.value 


def padding(bit):

    return '0' + bit

def make_hybrid_tree(L,k):

    f = BytesIO()
    '''    
    for j in L:
        if j <= 2**k  - 1:
            f = rice_encode.rice_code(f,j,k)
        if j <= 2**(k+1) - 1 and j >= 2**k:

            f = rice_encode.rice_code(f,j,k)
    '''
    left_count = '1'
    tree = HyTree(left_count)
    start = tree
   
    i = 1
    while i <= 4:
        start.left = Node(start.value + '1')
        start = make_leaf(start.left, 0)
        i += 1

def make_leaf(start, k):
            
    left_count = len(start.value)
    i = left_count
    start.right = Node('0')
    original = start
    start = start.right
    integer = 2**k
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
        count = 0
        while count < even_pad:
            even_bit = padding(even_bit)
            count += 1

        padded_even_bits.append(even_bit)


    for odd_bit in odd_bits:
        if left_count + 1 + len(odd_bit) > odd:
            odd_bits.remove(odd_bit)
            continue

        odd_pad = odd - 1 - left_count
        count = 1
        while count < odd_pad:
            odd_bit = padding(odd_bit)
            count += 1
        
        padded_odd_bits.append(odd_bit)
    
    for even_bit in padded_even_bits:
        for bit in even_bit:
            if bit == '0':
                start.right = Node('0')
            else:
                start.left = Node('1')
        
    for odd_bit in padded_odd_bits:
        for bit in odd_bit:
            if bit == '0':
                start.right = Node('0')
            else:
                start.left = Node('1')
    
    return original


if __name__ == '__main__':

    L = [1,2,3,4,5,5,6]

    make_hybrid_tree(L,0)
    
