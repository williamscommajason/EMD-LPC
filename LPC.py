import logging
import numpy as np
import scipy
import scipy.signal as sig
from scipy.io import loadmat
import math

class LPC:
    """
    LPC:

    **Linear Predictive Coding**

    Method of predicting a signal based on past samples

    """

    logger = logging.getLogger(__name__)

    def __init__(self, order, pred_coeff, frame_width):


        self.aa = [1, -2, 1]
        self.gains = None
        self.h = frame_width
        self.d = None
        self.order = 2
        self.err = None
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

        


if __name__ == "__main__":
    data = loadmat('r10.mat')
    data = data['residual'][0]
    ts = data[:1400]
    #ts = list(range(100))
    #a,g,err,h = lpc_fit(ts, 2, 350)
    #print(a)
    residual = LPC(2, [1,-2,1],350)
    a,g,err = residual.lpc_fit(ts)
    residual.lpc_synth(a,g,err)
    print()
    
