# EMD-LPC

## Introduction

Another Python standard implementation of the Empircal Mode Decomposition,
paired with Linear Predictive Coding and Discrete Cosine Transform
as an integer encoder. Most examples will focus on the encoding aspect of the 
algorithm and not the EMD or LPC in particular.

In its current state, EMD-LPC only allows for cubic spline interpolation, basic
local extrema detection and implements a kind of Cauchy convergence as its 
stopping criterion. Rice encoding is the only current option for residual encoding.

## Installation

Simply download this directory either directly from GitHub, or using command line:

> \$ git clone <https://github.com/williamscommajason/EMD_LPC>

Then go into the downloaded project and run from the command line:

> \$ python3 setup.py install

## Example

In most cases default settings are enough. Simply import `EMD` and pass your signal to 
instance or to `emd()` method.

```python
from EMDLPC import EMD
import numpy as np

ts = np.floor(np.random.normal(size=1200,scale=20,loc=0))
emd = EMD.EMD()
n_bytes, f = emd.save(ts)
reconstructed_ts = emd.load(f)
```

## Contact

Feel free to contact me with any questions, requests or to say *hi*.
Contact me through at (williaje@usc.edu).
