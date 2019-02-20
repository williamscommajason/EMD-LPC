from LPC import LPC
import rice_decode
 
def decoder():

    lpc = LPC(2,350)
    amp,gains,fits = lpc.unpack_residual()
    lpc.recon_err(amp,fits)
    r_err = lpc.lpc_synth(lpc.aaa,gains,lpc.r_err)
 
    error = rice_decode.decompress()
    
    r_sig = error + r_err
   
    return [int(round(x)) for x in r_sig]


if __name__ == "__main__":

   signal = decoder()
   import numpy as np
   np.set_printoptions(threshold=np.nan)
   ts = np.load('timestream11.npy')[:1400]
   print(signal-ts)

        
