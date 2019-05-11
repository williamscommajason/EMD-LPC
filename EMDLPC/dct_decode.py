import EMDLPC.rice_decode
import scipy.fftpack as fft
import numpy as np
import scipy.io as io

def decode(dct_error,indices,values):
        

    xerror = np.zeros(len(dct_error))

    for i in range(len(indices)):
        xerror[int(indices[i])] = values[int(i)]

    xx = fft.idct(xerror,norm='ortho')
    
    error = -(dct_error - xx)
    error = [int(round(x)) for x in error]
    
   
    return error


if __name__ == '__main__':

    error = decode()
    oerror = io.loadmat('error.mat')['error'][0]
    oerror = [int(x) for x in oerror]
#    print((np.array(oerror)-np.array(error)).tolist())

