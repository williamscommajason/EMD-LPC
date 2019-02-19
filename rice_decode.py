import struct


def BitString(BitString):

    for bit in BitString:
        yield bit


def decompress(k):

    bString = ''
    with open("rice.bin", "rb") as f:

        byte = f.read(1)

        while byte != b"":

            hexbyte = struct.unpack("@B",byte)[0]
            binary = "{0:b}".format(hexbyte)

            if len(binary) < 8:
                for i in range(8 - len(binary)):
                    binary = '0' + binary

            bString = bString + binary
            byte = f.read(1)

    f.close()

    codes = decode_bitString(bString,k)
    rice_dictionary = rice_dict(k,4)
    unsigned = []

    for i in codes:
        if i in rice_dictionary.keys():
            unsigned.append(rice_dictionary[i])
        else:
            unsigned.append(decode_rice_byte(i,k))

    signed = back_to_signed(unsigned)
    return signed
            

def decode_bitString(bString, k):
 
    zero_flag = False
    one_flag = False
    codes = []
    
    bString = BitString(bString)

    while True:

        bit = next(bString)
        
        try:
            quotient = '' 
            if bit == '0' and one_flag == False:
                
                quotient = '0' 
                zero_flag = True

            if zero_flag == True and one_flag == False:
                remainder = ''
                for i in range(k-1,-1,-1):
                    bit = next(bString)
                    remainder = remainder + bit    

                codes.append(quotient + remainder)
                zero_flag = False

            quotient = ''           
            while bit == '1':
                one_flag = True
                quotient = quotient + '1'
                bit = next(bString)
                if bit == '0':
                    
                    zero_flag = True
                    quotient = quotient + bit
                    break
        
               
            if zero_flag == True and one_flag == True:
                remainder = ''              
                for i in range(k-1,-1,-1):
                    bit = next(bString)
                    remainder = remainder + bit    
                codes.append(quotient + remainder)
                zero_flag = False
                one_flag = False

        except StopIteration:
            #print("Last element was: ", bit)
            break
        
    return codes
            
def decode_rice_byte(rb,k):
    
    rb = BitString(rb) 
    zero_flag = False
    one_flag = False
    
    while True:
    
        try:
            bit = next(rb)
            quotient = ''
            if bit == '0' and one_flag == False:
                for i in range(k-1,-1,-1):
                    bit = next(rb)
                    quotient = quotient + bit

                x = int(quotient,2)
                
                return x

            ones = 0   
            while bit == '1':
                one_flag = True
                ones += 1  
                bit = next(rb)
                if bit == '0':
                    zero_flag = True
                    quotient = quotient + bit
                    break
 
            if zero_flag == True and one_flag == True:
                remainder = ''
                for i in range(k-1,-1,-1):
                    bit = next(rb)
                    remainder = remainder + bit
            #print(ones)        

            x = ones*(2**k) + int(remainder,2)
           
            return x

        except StopIteration:
            break  
    
    
def rice_dict(k,end):

    rice_dictionary = dict()
    ints = tuple(range(end+1))

    for x in ints:
        q = x / (1 << k)
        q = int(q)
        bString = ''
        for i in range(q):
            bString = bString + '1'
        bString = bString + '0'
        for i in range(k-1, -1, -1):
            bString = bString + str((x >> i) & 1)
            
        rice_dictionary[bString] = x

    return rice_dictionary
                     
def back_to_signed(L):

    signed = []
    for x in L:
        if x%2 == 0:
            signed.append(int(x/2))
        if x%2 == 1:
            signed.append(-(int((x/2) + 1)))

    return signed
        

if __name__ == "__main__":

    signed = decompress(3)
    print(signed)
    
    
