from LPC import LPC
from EMD import EMD
import rice_encode
import rice_decode
import argparse
import numpy as np
import math
np.set_printoptions(threshold=np.nan)

def encoder():

    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    x = np.load(args.filename)[:1400]
    emd = run_EMD_encoder(x)
    r_err = run_LPC_encoder(emd.residual)
    emd.make_lossless(r_err)
    rice_encode.compress(emd.error)
    

def run_EMD_encoder(x):

    emd = EMD()
    emd.emd(x,None)
    return emd

def run_LPC_encoder(residual):

    lpc = LPC(2,350)
    lpc.lpc_fit(residual)
    lpc.get_fits(lpc.err)
    lpc.get_amp(lpc.err,lpc.h)
    lpc.pack_residual()
    amp,gains,fits = lpc.unpack_residual()
    lpc.recon_err(amp,fits)
    r_err = lpc.lpc_synth(lpc.aaa,gains,lpc.r_err)

    return r_err
    
       

 
if __name__ == "__main__":
    encoder()
       
