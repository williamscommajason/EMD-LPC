import numpy as np
from scipy.interpolate import CubicSpline
import math
from math import floor
import logging
import struct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from EMDLPC import rice_encode 
from EMDLPC import rice_decode
from EMDLPC import LPC
from io import BytesIO
from EMDLPC import dct_encode 
from EMDLPC import dct_decode 
import os
import scipy
import scipy.signal as sig

class EMD:
    """
    EMD:

    **Empirical Mode Decomposition**

    Method of decomposing signal into Intrinsic Mode Functions (IMFs)
    based on algorithm presented in Huang et al (1998)

    Thresholds which control the goodness of the decomposition:
        * 'osc' --- (int) --- Number of Oscillations
        * 'resolution' --- (float) --- Ratio of power in mean to power in iteration of IMF
        * 'p_Resid' --- (float) --- power of residual 
        * 'interpolation' --- (Bool) --- interpolation of extrema

    """

    logger = logging.getLogger(__name__)

    def __init__(self,  spline_kind = 'cubic', **config):
        """Initiate EMD as an instance.

        Configuration can be passed as config.

        >>> config = {'osc': 0, 'resolution': 20, 'p_resid': 10, 'alpha': 1}
        >>> emd = EMD(**config)

        """

        self.osc = 1
        self.resolution = 2
        self.p_resid = 1
        self.alpha = 1
        self.sample_rate = None
        self.siglen = None
        self.max_iter = math.inf
        self.count = 1

        self.interpolate = False
        self.imfs = None
        self.residual = None
        self.encoding = True
        self.error = []
        self.p = []
        self.iterations = 0
        self.inner_iter = 0

        for key in config.keys():
            if key in self.__dict__.keys():
                self.__dict__[key] = config[key]

    
    def __call__(self, x , t=None):
        return self.emd(x,t=t)

    
    def discreteMinMax(self,x, t):
        """
        Gets locations of discrete minimums and maximums

        Parameters
        ----------
    
        x : list or numpy array
            Input signal.
        t : list or numpy array
            Position or time array.

        Returns
        -------

        discreteMin : numpy array (2 columns)
            time (1st column) and values (2nd column) of minima.
        discreteMax : numpy array (2 columns)
            time (1st column) and values (2nd column) of maxima.

        """
    
        #initialize empty lists for storing x and y values for min/max
        top = False
        down = False
        discreteMin = []
        discreteMax = []

        for i in range(1,len(x)-1):
            if x[i-1] < x[i] and x[i] > x[i+1]: #and x[i-2] < x[i] and x[i] > x[i+2] and x[i-3] < x[i] and x[i] > x[i+3] and x[i-4] < x[i] and x[i] > x[i+4] and x[i-5] < x[i] and x[i] > x[i+5]: #Maximum
                discreteMax.append([i,x[i]])

            if x[i-1] > x[i] and x[i] < x[i+1]: # and x[i-2] > x[i] and x[i] < x[i+2] and x[i-3] > x[i] and x[i] < x[i+3] and x[i-4] > x[i] and x[i] < x[i+4] and x[i-5] > x[i] and x[i] < x[i+5]: #Minimum
                discreteMin.append([i,x[i]])

            '''this is to handle the off chance of us sampling several minimums of equal
            magnitude next to each other'''

            #begin by marking the index of a repeated minimum and set down to True
            if x[i - 1] > x[i] and x[i] == x[i + 1]:
                mark_min = i
                top = False #top denotes a maximum
                down = True #down denotes a minimum

            #now, this block is for every index after the marked index that is repeated.
            #check when the segment ends, then append each element to the minima list
            if (x[i - 1] == x[i] and x[i] < x[i + 1]):
                if down:
                    for j in range(mark_min,i+1):
                        discreteMin.append([j, x[j]])
                if x[i+1] == x[i]:
                    down = True
                else:
                    down = False
            #this is to handle the off chance of us sampling several maximums of equal
            #magnitude next to each other
            if x[i - 1] < x[i] and x[i] == x[i + 1]:
                mark_max = i
                top = True
                down = False
            if x[i - 1] == x[i] and x[i] > x[i + 1]:
                if top:
                    for k in range(mark_max,i+1):
                        discreteMax.append([k, x[k]])
                if x[i+1] == x[i]:
                    top = True
                else:
                    top = False

        discreteMax = np.array(discreteMax)
        discreteMin = np.array(discreteMin)

        return (discreteMin, discreteMax)

    
    def _find_duplicates(self, discreteMin, discreteMax):

        '''This code finds the indices of the duplicated elements in discreteMin and discreteMax'''

        diff_Min = np.diff(discreteMin[:,0])
        diff_Max = np.diff(discreteMax[:,0])
        #insert the first element of dMin and dMax to make the lengths of the two lists the same
        #(we will delete it later if it's not a repeated extrema)
        diff_Min = np.insert(diff_Min,0,discreteMin[:,0][0])
        diff_Max = np.insert(diff_Max,0,discreteMax[:,0][0])
        dup_Min = []
        dup_Max = []

        for i in range(len(discreteMin)):
            if i == len(discreteMin) - 1:
                if discreteMin[:,0][i] == discreteMin[:,0][i-1]:
                    dup_Min = np.append(dup_Min,discreteMin[:,0][int(i)])
                break

            if diff_Min[i] == 1 and int(i-1) > 0:
                dup_Min = np.append(dup_Min,discreteMin[:,0][int(i)])
                if diff_Min[i-1] != 1:
                    dup_Min = np.append(dup_Min,discreteMin[:,0][int(i-1)])

        for i in range(len(discreteMax)):
            if i == len(discreteMax) - 1:
                if discreteMax[:,0][i] == discreteMax[:,0][i-1]:
                    dup_Max = np.append(dup_Max,discreteMax[:,0][int(i)])
                break

            if diff_Max[i] == 1 and int(i-1) > 0:
                dup_Max = np.append(dup_Max,discreteMax[:,0][int(i)])
                if diff_Max[i-1] != 1:
                    dup_Max = np.append(dup_Max,discreteMax[:,0][int(i-1)])

        if len(dup_Min) > 0 and len(diff_Min) > 1:
            if diff_Min[1] != 1:
                #print(dup_Min)
                #print(diff_Min)
                dup_Min = np.delete(dup_Min,0,0)

        if len(dup_Max) > 0 and len(diff_Max) > 1:
            if diff_Max[1] != 1:
                dup_Max = np.delete(dup_Max,0,0)

        return(dup_Min,dup_Max)


    
    def interp(self, x, discreteMin, discreteMax):

        '''takes as input the locations of the discrete minimums and maximums, interpolates to
        gin a more precise picture of where the mins and maxs are, then outputs those locations
        '''
        #create two separate lists, one that contains all the indices (+1) of the duplicates and one that cointains all the non-duplicates
        if len(discreteMin) < 1 or len(discreteMax) < 1:
            return (discreteMin,discreteMax)

        [tMin, tMax] = [discreteMin[:, 0], discreteMax[:, 0]]
        [tMin_dup, tMax_dup] = find_duplicates(discreteMin,discreteMax)
        [tMin, tMax] = [list(set(tMin) - set(tMin_dup)), list(set(tMax) - set(tMax_dup))]
        [mincoeff, maxcoeff] = [[], []]

        if len(tMin) < 1 or len(tMax) < 1:
            return (discreteMin,discreteMax)

        # get parabolic mins
        lengths = []
        for i in tMin:
            lengths.append(i)
            # get values on opposite sides of the minimum
            [y1, y2, y3] = [x[int(i) - 1], x[int(i)], x[int(i) + 1]]
            A = [];
            # setup a solve linear equation for coefficients of parabola
            A.append([(i - 1) ** 2, i - 1, 1])
            A.append([i ** 2, i, 1])
            A.append([(i + 1) ** 2, i + 1, 1])
            A = np.array(A);
            b = np.array([y1, y2, y3]);
            mincoeff.append(np.linalg.solve(A, b))
        mincoeff = np.vstack([mincoeff[0:len(mincoeff)]])
        # get parabolic maxs
        lengths = []
        for i in tMax:
            lengths.append(i)
            # get values on opposite sides of the maximum
            [y1, y2, y3] = [x[int(i) - 1], x[int(i)], x[int(i) + 1]]
            A = [];
            # setup a solve linear equation for coefficients of parabola
            A.append([(i - 1) ** 2, i - 1, 1])
            A.append([(i) ** 2, i, 1])
            A.append([(i + 1) ** 2, i + 1, 1])
            A = np.array(A);
            b = np.array([y1, y2, y3]);
            maxcoeff.append(np.linalg.solve(A, b))

        maxcoeff = np.vstack([maxcoeff[0:len(maxcoeff)]])
        parabolicMax = np.zeros([len(discreteMax), 2]);
        parabolicMin = np.zeros([len(discreteMin), 2])

        # use t = -b/2a to get values of parabolic maxes
        for i in range(len(mincoeff)):
            # m denotes minimum coefficient and upper case M denotes maximum coefficient
            [am, bm, cm] = [mincoeff[i, 0], mincoeff[i, 1], mincoeff[i, 2]]
            [parabolicMin[i, 0], parabolicMin[i, 1]] = [-bm / (2 * am), -((bm ** 2) / (4 * am)) + cm]
        for i in range(len(maxcoeff)):
            # M denotes maximum coefficient
            [aM, bM, cM] = [maxcoeff[i, 0], maxcoeff[i, 1], maxcoeff[i, 2]]
            [parabolicMax[i, 0], parabolicMax[i, 1]] = [-bM / (2 * aM), -((bM ** 2) / (4 * aM)) + cM]

        count = 0
        for i in discreteMin[:,0]:
            if np.isin(i,tMin_dup):
                parabolicMin[count + len(tMin),0] = i
                parabolicMin[count + len(tMin),1] = x[int(i)]
                count = count + 1

        count = 0
        for i in discreteMax[:,0]:
            if np.isin(i,tMax_dup):
                parabolicMax[count + len(tMax),0] = i
                parabolicMax[count + len(tMax),1] = x[int(i)]
                count = count + 1
        parabolicMin = np.sort(parabolicMin,axis=0)
        parabolicMax = np.sort(parabolicMax,axis=0)
        # these conditionals tell us whether or not we could extrapolate the
        # beginning and end points as mins or maxs
    
        return (parabolicMin, parabolicMax)
    
    
    def extrap(self, x, discreteMin, discreteMax):
        """
        produces two ghost cells on both side of the signal that contain a min and max
        value equal to the first min and max of the signal and the last min and max of
        the signal in order to better extrapolate the first and last points of the signal
        """

        begin_max = False
        begin_min = False
        end_min = False
        end_max = False

        if len(discreteMin) == 0 or len(discreteMax) == 0:
            return (discreteMin, discreteMax)
    
        if len(discreteMax) > 0:
            if x[0] >= discreteMax[0,1]:
                begin_max = True
    #           print('first point is maximum')
                discreteMax = np.flip(discreteMax,0);
                discreteMax = np.append(discreteMax,[[0,x[0]]],axis=0);
                discreteMax = np.flip(discreteMax,0)
            if x[-1] >= discreteMax[-1,1]:
                end_max = True
#                print('end point is maximum')
                discreteMax= np.append(discreteMax,[[len(x)-1,x[-1]]],axis=0)

        if len(discreteMin) > 0:
            if x[0] <= discreteMin[0,1]:
#                print('first point is minimum')
                begin_min = True
                discreteMin = np.flip(discreteMin,0);
                discreteMin = np.append(discreteMin,[[0,x[0]]],axis=0);
                discreteMin = np.flip(discreteMin,0)

            if x[-1] <= discreteMin[-1,1]:
#           print('end point is minimum')
                end_min = True
                discreteMin= np.append(discreteMin,[[len(x)-1,x[-1]]],axis=0)

        if discreteMin[0, 0] == 0 and discreteMax[0, 0] == 0:
               print("First point is both a min and max!")  # IMF is zero at the ends
        else: #otherwise, create ghost point with first maximum
            reflectedMin = [-discreteMax[0, 0], discreteMin[0, 1]]
            discreteMin = np.flip(discreteMin, 0)
            discreteMin = np.append(discreteMin, [reflectedMin], axis=0)
            discreteMin = np.flip(discreteMin, 0)

            reflectedMax = [-discreteMin[1, 0], discreteMax[0, 1]]
            discreteMax = np.flip(discreteMax, 0)
            discreteMax = np.append(discreteMax, [reflectedMax], axis=0)
            discreteMax = np.flip(discreteMax, 0)

        #extrapolating end of signal
        if discreteMin[-1, 0] == len(x) - 1 and discreteMax[-1, 0] == len(x) - 1:
            print("First point is both a min and  max!")  # IMF is zero at the ends
        #we add a ghost point to the end of the discreteMin first, and then do the same to
        #discreteMax, accounting for the change in discreteMin
        else:
            discreteMin = np.append(discreteMin, [[2 * (len(x) + 1) - discreteMax[-1,0], discreteMin[-1,1]]], axis = 0)
            discreteMax = np.append(discreteMax, [[2 * (len(x) + 1) - discreteMin[-2, 0], discreteMax[-1, 1]]], axis = 0)

        return (discreteMin,discreteMax)



    
    @staticmethod
    def monotone(residual):

        """
        checks to see if residual function is monotone
        """
        #print(residual)
        if type(residual) is np.ndarray:
            x = residual
        else:
            x = np.array(residual)
        
        dx = np.diff(x)

        return np.all(dx <= 0) or np.all(dx >= 0)

    def check_recon(self, x):
        """
        checks to see if reconstructed signal is same as original signal
        """
        recon = np.zeros((self.siglen,))
        
        for imf in self.imfs:
            recon += imf

        for i in range(self.siglen):
            recon[i] = int(round(recon[i]))
         
        if self.monotone(self.residual) == True and self.osc == 0:
            self.logger.debug("FINISHED -- RESIDUAL (MONOTONE)")
        else:
            self.logger.debug("RESIDUAL -- NOT MONOTONE")

        if all([y ==0 for y in abs(x-recon)]):
            self.logger.debug("FINISHED -- RECONSTRUCTION")
            return True       

 
		
        self.logger.debug("NOT FINISHED -- RECONSTRUCTION")
        return False

    def emd(self, x, t=None):
        """
        Performs EMD on signal x.
        Returns IMF functions in numpy arrays.

        Parameters
        ----------

        x : numpy array,
            Input signal.
        t : numpy array, (default = None)
            Position or time array. If None, linear time series is created.

        Returns
        -------
        IMFs: numpy array
              Set of IMFs produced from input signal.
        Residual: numpy array
              Residual produced from input signal.

        """
        self.siglen = len(x)

        if t is None and self.siglen == None: t = np.linspace(0, self.siglen - 1, self.siglen)

        else: t = np.linspace(0,len(x)-1,len(x))
        self.t = t 
        self.signal = x
        signal = x
        signal = signal.astype('float64')
        
        pX = np.linalg.norm(x)**2
         
        if pX == 0:
            self.siglen = [self.siglen]
            
            return self.siglen

        imfs = []
        iniResidual = 0
        finished = False

        self.textrema = []
        self.yextrema = []
 
        while finished == False and iniResidual < self.p_resid and self.iterations <= 10:

            iImf = signal
            pSig = np.linalg.norm(signal)**2
            (discreteMin, discreteMax) = self.discreteMinMax(iImf,t)

            if len(discreteMin) < 1 or len(discreteMax) < 1:
                self.logger.info('Residual will have one extrema')
                
                break
                
            if self.interpolate == True:
                (parabolicMin,parabolicMax) = self.interp(iImf,discreteMin,disereteMax)
            else:    
                (parabolicMin, parabolicMax) = self.extrap(iImf,discreteMin,discreteMax)

            topenv = CubicSpline(parabolicMax[:,0],parabolicMax[:,1])
            botenv = CubicSpline(parabolicMin[:,0],parabolicMin[:,1])
            mean = (botenv(t) + topenv(t))/2

            self.inner_iter = 0

            while True or self.inner_iter <= 1000:
                
                pImf = np.linalg.norm(iImf)**2
                pMean = np.linalg.norm(mean)**2

                if pMean == 0:
                    self.logger.info('Iterations taken {}'.format(iterations))
                    self.logger.info('Mean of IMF {} is 0'.format(pMean))
                    
                    break

                if pMean > 0:
                    res = 10*np.log10(pImf/pMean)
                if res>self.resolution:
                    self.logger.info('Mean resolution {} reached for IMF {}'.format(res,self.count))
                    break

                iImf = iImf - (self.alpha)*mean

                (discreteMin,discreteMax) = self.discreteMinMax(iImf,t)
                if len(discreteMin) < 1 or len(discreteMax) < 1:
                    self.logger.info('Residual will have one extrema (inner loop)')
                    break
                if self.interpolate == True:
                    (parabolicMin,parabolicMax) = self.interp(iImf, discreteMin, discreteMax)
                else:
                    (parabolicMin,parabolicMax) = self.extrap(iImf, discreteMin, discreteMax)

                topenv = CubicSpline(parabolicMax[:,0], parabolicMax[:,1])
                botenv = CubicSpline(parabolicMin[:,0], parabolicMin[:,1])
                mean = (topenv(t) + botenv(t))/2

                self.inner_iter += 1
            
            self.textrema.append(parabolicMax[:,0])
            self.yextrema.append(parabolicMax[:,1])
            
            self.iterations += 1
            #if iterations == 1:
            #    self.p = np.polyfit(parabolicMax[:,0],parabolicMax[:,1],20)

                
            iImf = np.array(iImf)
            imfs = np.append(imfs, iImf, axis=0)
            self.count += 1
            signal -= iImf
            pSig = np.linalg.norm(signal)**2
            osc = len(discreteMin) + len(discreteMax)
            
            if pSig > 0:

                iniResidual = 10*np.log10(pX/pSig)
                
            else:
                iniResidual = math.inf
            
            if self.osc == 0:
                finished = self.monotone(signal)
            if self.osc != 0:
                
                finished = osc < self.osc
            
            
        if pSig/pX > 0:
            self.residual = signal
            imfs = np.append(imfs, np.array(signal),axis=0)
            self.count += 1

        self.residual = signal
        imfs = np.array(imfs)
        imfs = imfs.reshape(self.count-1,int(self.siglen))
    
        self.imfs = imfs
        
        if self.residual is not None:
            if all([ i == 0 for i in self.residual]):
                np.delete(imfs,-1,axis=0)
                self.residual = imfs[-1]
                

        self.check_recon(x)
        self.get_error()
        #print(self.imfs[0])
                

        return imfs

    def get_imfs_and_residue(self):
        return self.imfs, self.residual

    def get_residue(self):
        return self.residual
   
    def get_error(self):
        if self.encoding == True:
            error = self.signal - self.residual
        for i in error:
            self.error.append(int(round(i)))
         
        return self.error 

    def make_lossless(self,lpc_residual):
        
        
        for i in range(len(self.signal)):
            truncation_error = int(round(self.signal[i] - (int(round(self.error[i] + lpc_residual[i])))))
            
            self.error[i] += truncation_error
        
        return self.error
    
    @staticmethod
    def truncate(L):

        return [int(round(x)) for x in L]    

    
    def save(self,x,filename=None):
               
        if filename is not None:
            f = open(filename + '.emd','w+b')
            fd = open(filename + '1.emd', 'w+b')
            fd1 = open(filename + '2.emd', 'w+b')

        else:
 
            f = BytesIO()
            fd = BytesIO()
            fd1 = BytesIO()        

   
        #FILTER
     
        even = all([i%2 == 0 for i in x])
        
        fd1.write(struct.pack('@B',0))
        x_filtered = sig.lfilter(np.array([.5,-.5]),np.array([1.0]),x)
        
        fd1.write(struct.pack('@?',False))
        fd1 = rice_encode.compress(x_filtered,fd1)
        
        #EMD
        self.emd(x)
        
        if type(self.siglen) == list:
 
            if filename is not None:
                
                fe = open(filename + '.bin','w+b')
                fe.write(struct.pack('@I',0))
                fe.write(struct.pack('@I',self.siglen[0]))

                return fe.seek(0,os.SEEK_END), fe

            else:
                
                fe = BytesIO()
                fe.write(struct.pack('@I',0))
                fe.write(struct.pack('@I',self.siglen[0]))

                return fe.seek(0,os.SEEK_END), fe

        f.write(struct.pack('@B',1))
        fd.write(struct.pack('@B',1))
        
        #LPC
        lpc = LPC.LPC(2,len(self.residual),len(self.residual))
        lpc.lpc_fit(self.residual)
        lpc.get_fits(lpc.err)
        lpc.get_amp(lpc.err,lpc.h)
        f = lpc.pack_residual(f)
        fd = lpc.pack_residual(fd)
        sign, npts, frame_width, amp, gains, fits, f = lpc.unpack_residual(f)
        lpc.recon_err(npts, frame_width, amp, fits)
        r_err = lpc.lpc_synth(lpc.aaa, gains, LPC.LPC.r_err, npts, frame_width)

        
        self.make_lossless(r_err)
        #DCT
        dct_output = dct_encode.dct_encode(self.error,.99)
        dct_output1 = dct_encode.dct_encode(self.error,.999)

        
        #Encoding  
        dct_nbytes = 0
        dct_nbytes1 = 0

        for i in dct_output:
            if np.var(i) < np.var(np.diff(i)):
                dct_nbytes  += rice_encode.pre_compress(np.diff(i))

            else:      
                dct_nbytes += rice_encode.pre_compress(i)

        for i in dct_output1:
            if np.var(i) < np.var(np.diff(i)):
                dct_nbytes1 += rice_encode.pre_compress(np.diff(i))

            else:
                dct_nbytes1 += rice_encode.pre_compress(i)
       
        if dct_nbytes < dct_nbytes1:

            for i in dct_output:
                if np.var(i) < np.var(np.diff(i)):
                
                    f.write(struct.pack('@?',False))
                    f = rice_encode.compress(i,f)
                
                else:
                    ii = np.diff(i)
                    ii = ii.tolist()
                    ii.insert(0,i[0])
                    #print(len(ii))
                    f.write(struct.pack('@?',True))
                    f = rice_encode.compress(ii,f)
        else:

            for i in dct_output1:
                    if np.var(i) < np.var(np.diff(i)):

                        f.write(struct.pack('@?',False))
                        f = rice_encode.compress(i,f)

                    else:
                        ii = np.diff(i)
                        ii = ii.tolist()
                        ii.insert(0,i[0])
                        #print(len(ii))
                        f.write(struct.pack('@?',True))
                        f = rice_encode.compress(ii,f)

        if np.var(np.diff(self.error)) < np.var(self.error): 
           
            derror = [int(x) for x in np.diff(self.error)]
            derror.insert(0,self.error[0])
            fd.write(struct.pack('@?',True))
           
            fd = rice_encode.compress(derror,fd)
            
        else:
            fd.write(struct.pack('@?',False))
            fd = rice_encode.compress(self.error,fd)
         
        
 
        if f.seek(0,os.SEEK_END) > fd.seek(0,os.SEEK_END) and fd1.seek(0,os.SEEK_END) > fd.seek(0,os.SEEK_END):
            print('1') 
            if filename is not None:
                os.remove(filename + '.emd')
                os.remove(filename + '2.emd')
            return fd.seek(0,os.SEEK_END), fd, 

        elif fd.seek(0,os.SEEK_END) > f.seek(0,os.SEEK_END) and fd1.seek(0,os.SEEK_END) > f.seek(0,os.SEEK_END):
            print('2')
            if filename is not None:
                os.remove(filename + '1.emd')
                os.remove(filename + '2.emd')
            return f.seek(0,os.SEEK_END), f, 

        elif even == True:
            print('3')    
            
            return fd1.seek(0,os.SEEK_END), fd1

        elif fd.seek(0, os.SEEK_END) > f.seek(0,os.SEEK_END):
            print('4')
            if filename is not None:
                os.remove(filename + '1.emd')
                os.remove(filename + '2.emd')
            return f.seek(0,os.SEEK_END), f

        else:
            print('5')
            if filename is not None:
                os.remove(filename + '.emd')
                os.remove(filename + '2.emd')
            return fd.seek(0,os.SEEK_END), fd
            
        
    def load(self,f):

        if f.seek(0,os.SEEK_END) == 8:
            f.seek(0)
            value = struct.unpack('@I',f.read(struct.calcsize('I')))[0]
            siglen = struct.unpack('@I',f.read(struct.calcsize('I')))[0]

            return np.array([0 for x in range(siglen)])

        sign, npts, frame_width, amp, gains, fits, f = LPC.LPC.unpack_residual(f)                
        
        if sign == 1:
            lpc = LPC.LPC(2, frame_width, npts)
            LPC.LPC.recon_err(npts, frame_width, amp, fits)
            r_err = lpc.lpc_synth(lpc.aaa, gains, LPC.LPC.r_err, npts, frame_width)
            
            lists, l_av = rice_decode.decompress(f)
            
            if len(lists) == 1:
                error = lists[0]
                
                '''
                if error[0] == 1 and len(error) > npts:
                    error.pop(0)
                    for i in range(len(error))[1:]:
                        error[i] += error[i-1] 
                '''
            else:
                error = dct_decode.decode(lists[0],lists[1],lists[2])
        
        
            r_sig = error + r_err

        else:
            
            f.seek(1)
            
            lists, l_av = rice_decode.decompress(f)
            
            x_filtered = lists[0]
            r_sig = x_filtered = sig.lfilter(np.array([1.0]),np.array([.5,-.5]),x_filtered)
            
        return [int(round(x)) for x in r_sig]
    
    @staticmethod
    def run_length_encode(input_string):
        count = 1
        prev = ''
        lst = []
        for character in input_string:
            if character != prev:
                if prev:
                    #entry = (prev,count)
                    lst.append(int(prev))
                    lst.append(count)
                    #print lst
                count = 1
                prev = character
            else:
                count += 1
        else:
            try:
                #entry = (character,count)
                lst.append(int(character))
                lst.append(count)
                return (lst, 0)
            except Exception as e:
                print("Exception encountered {e}".format(e=e)) 
                return (e, 1)
    
    @staticmethod 
    def run_length_decode(lst):
        q = ""
        for character, count in lst:
            q += character * count
        return q
    
    
     
 
if __name__ == "__main__":
    
    logging.basicConfig(level=logging.DEBUG)

    import scipy.io as io
    import simulate
    import makewav
    import rice_encode
    import bitstring
    from bitstring import BitArray
    from bitstring import BitStream
    

    x = np.floor(np.random.normal(size=1200,scale=20,loc=0)) 
    #x = np.load('timestream1002.npy')[:1000]
    #fo = open('rice_error.bin','w+b')
    
    emd = EMD()
    '''
    emd.emd(x)
    residual = emd.residual
    io.savemat('residual6161.mat',{'res':residual})
    io.savemat('timestream6161.mat',{'ts':x})
    error = np.array(emd.error)
    error.tofile('error.bin')
    '''
    #x = np.zeros(100)
    nbytes, fo = emd.save(x)
    print('nbytes is:',nbytes) 
    #print(emd.residual)
    recon = emd.load(fo)
    fo.close()
    #print(emd.error)
    
    #rice_encode.compress(emd.error,fo) 
    print((np.array(x) - np.array(recon)).tolist())
    #print(len(recon))
    '''
    rl = emd.run_length_encode(bString)
    print(rl)
    rl_nbytes = rice_encode.pre_compress(rl[0])
    a = BitStream().join([BitArray(se=i) for i in rl[0]])
    print(len(a)/8)
    print(rl_nbytes) 
    ''' 
    
