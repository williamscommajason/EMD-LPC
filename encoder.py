from LPC import LPC
from EMD import EMD
import rice_encode
import rice_decode
import argparse
import numpy as np
import math

def encoder():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    x = np.load(args.filename)[:1400]
    
    emd = run_EMD(x)
    run_LPC(emd.residual)
    run_rice_encode(emd.error)

def run_EMD(x):

    emd = EMD()
    emd.emd(x,None)
    emd.get_error()
    print(emd.get_error())

    return emd

def run_LPC(residual):

    lpc = LPC(2,350)
    lpc.lpc_fit(residual)
    lpc.get_fits(lpc.err)
    lpc.get_amp(lpc.err,lpc.h)
    lpc.pack_residual()

def run_rice_encode(error):

    mylist = [1,2,4,8,16,32,64,128,256,512]
    std = math.sqrt(np.var(error))
    rounded = mylist.index(min(mylist, key = lambda x:abs(x-std)))    
    rice_encode.compress(error,rounded)

    
        
if __name__ == "__main__":
    encoder()
       
