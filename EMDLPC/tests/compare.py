from spt3g import core
import pickle
import numpy as np
import EMD

fname = 'pb2-testdata.g3'
file = core.G3File(fname)

for i in range(4):
    frame = next(file)

flac_fs = []
emd_fs = []

for i in range(3):
    timestreams = frame['RawTimestreams_I'].items()[:1000]
    for k,ts in timestreams:
        
        ts.SetFLACCompression(9)
        flac_fs.append(len(pickle.dumps(ts)))
        print(len(pickle.dumps(ts)))

        emd = EMD.EMD()
        nbytes, f = emd.save(np.asarray(ts))
        emd_fs.append(nbytes)
        print(nbytes)

    frame = next(file)



print(sum(np.array(emd_fs) - np.array(flac_fs)))
