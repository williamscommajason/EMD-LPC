import numpy as np
import scipy.io as io
from rice_encode import signed_to_unsigned
from io import BytesIO

def entropy(labels):
    """ Computes entropy of 0-1 vector. """
    labels = signed_to_unsigned(labels)
    n_labels = len(labels)

    if n_labels <= 1:
        return 0

    counts = np.bincount(labels)
    probs = counts[np.nonzero(counts)] / n_labels
    n_classes = len(probs)

    if n_classes <= 1:
        return 0
    return - np.sum(probs * np.log(probs)) / np.log(n_classes)


if __name__ == '__main__':


    error = io.loadmat('error.mat')['error'][0]
    error = [int(x) for x in error]

    ent = entropy(error)
    print(ent*len(error))
    import rice_encode
    f = BytesIO()
    f = rice_encode.compress(error,f)
    print(f.getbuffer().nbytes)
