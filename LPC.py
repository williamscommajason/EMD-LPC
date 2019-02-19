import logging
import numpy as np
import scipy
import scipy.signal as sig
from scipy.io import loadmat
import math
import struct

class LPC:
    """
    LPC:

    **Linear Predictive Coding**

    Method of predicting a signal based on past samples

    """

    logger = logging.getLogger(__name__)

    def __init__(self, order, frame_width):


        self.aa = [1, -2, 1]
        self.gains = None
        self.h = frame_width
        self.npts = None
        self.d = None
        self.order = order
        self.amp = None
        self.fits = None
        self.err = None
        self.r_err = None
        self.a = None

    def __call__(self, signal):
        a,g,err,h = self.lpc_fit(signal, self.order, self.h)
        return self.lpc_synth(a,g,err,h)
     


    def lpc_fit(self,signal):
        """
        Returns

        """
        signal = [float(x) for x in signal]
        signal = np.array(signal)
        if np.array(signal).ndim > 1:
            raise ValueError("Array of rank > 1 not supported")

        if self.order > signal.size:
            raise ValueError("Input signal must have a length >= LPC order")

        if self.order > 0:
            x = [i for i in signal]    
            p = self.order
            h = self.h
            w = 2*h
            npts = len(signal)
            self.npts = npts
            nhops = math.floor(npts/h) 
        
            edges = [0 for i in range(int((w-h)/2))]

            x = edges + x
            x = x + edges

            a = np.zeros((nhops, p + 1))
            g = np.zeros(nhops)
            err = np.zeros(npts)

            for hop in range(nhops):
                xx = x[(hop)*h + 0: hop*h + w]
                xx = np.array(xx)
                wxx = xx*(np.hanning(w+2)[1:-1])
                rxx = np.correlate(wxx,wxx,"full")
                rxx = rxx[w-1:w+p]
                R = scipy.linalg.toeplitz(rxx[0:p])
                an = np.dot(scipy.linalg.inv(R),rxx[1:p+1])
                an = [2,-1]
                aa = self.aa
                rs = scipy.signal.lfilter(aa, 1, xx[int((w-h)/2): int((w-h)/2) + h], axis = 0)
                G = math.sqrt(np.mean(rs**2))
                a[hop,:] = aa
                g[hop] = G
                err[(hop)*h + 0: hop*h + h] = rs/G
        
        self.a = a
        self.gains = g
        self.err = err        
  
        return a,g,err
           
    def lpc_synth(self,a,g,err):
        nhops,p = a.shape
        e = err
        npts = len(err)
        d = np.zeros(npts)
        h = self.h

        for hop in range(nhops):
            hbase = hop*h

            oldbit = d[hbase: hbase + h]
            aa = a[hop,:]
            G = g[hop]
            newbit = G*scipy.signal.lfilter(np.array([1.0]),aa,e[hbase : hbase + h])

            d[hbase : hbase + h] = newbit
       
        self.d = d

        return d        

    def get_amp(self, err,frame):
        self.amp = np.mean(err[::frame])
        if self.amp < 0:
            self.logger.debug("ERROR AMPLITUDE == NEGATIVE")
        else:
            self.logger.debug("ERROR AMPLITUDE == POSITIVE")

        return(np.mean(err[1::frame]))
            
    def get_fits(self,err):
        h = self.h
        nhops = math.floor(self.npts/self.h)
        fits = []
        for i in range(nhops):
            p = np.polyfit(np.array(list(range((i*h)+2,(i+1)*h))),err[(i*h)+2:(i+1)*h],1)
            fits.append(p)
        self.fits = [x for sublist in fits for x in sublist]
        return self.fits

    def get_gains(self):
       return self.gains

    def recon_err(self,amp,fits):
         
        recon_error = np.zeros(self.npts)
        h = self.h
        nhops = math.floor(self.npts/self.h)
        for i in range(nhops):
            recon_error[(i*h)+2:(i+1)*h] = np.polyval(np.array(fits[i]),np.array(list(range((i*h)+2,(i+1)*h))))
            
        recon_error[::self.h] = amp
        recon_error[1::self.h] = -amp
        self.r_err = recon_error

        return recon_error

    def pack_residual(self):
        packed = []
        packed.append(self.gains)
        packed.append(self.fits)

        f = open("packed_residual.bin", 'w+b')
        f.write(struct.pack('@d',self.amp))
        
        for item in packed:
            for x in item:
               f.write(struct.pack('@d', x))
        
        
        f.close()
        return packed
        
    def unpack_residual(self):
     
        f = open("packed_residual.bin", 'rb')

        amp = struct.unpack('@d',f.read(struct.calcsize('d')))[0]
 
        gains = []
        for i in range(4):
            gains.append(struct.unpack('@d',f.read(struct.calcsize('d')))[0])
        
        fits = []
        while True:
        
            try:
                fits.append(struct.unpack('@d',f.read(struct.calcsize('d')))[0])

            except struct.error:
                fits = np.reshape(fits,(4,2))
                fits = fits.tolist()                     
                break

        return amp, gains, fits   
       
                

if __name__ == "__main__":
    data = loadmat('r10.mat')
    data = data['residual'][0]
    ts = data[:1400]
    #ts = list(range(100))
    #a,g,err,h = lpc_fit(ts, 2, 350)
    #print(a)
    lpc = LPC(2,350)
    a,g,err = lpc.lpc_fit(ts)
    lpc.lpc_synth(a,g,err)
    print(lpc.get_amp(err,lpc.h))
    amp,gains,fits = lpc.unpack_residual()
    recon_err = lpc.recon_err(amp,fits)
    #print((recon_err - lpc.err).tolist())
    r_err = lpc.lpc_synth(lpc.a,gains,lpc.r_err)
    print(ts-r_err)
    
