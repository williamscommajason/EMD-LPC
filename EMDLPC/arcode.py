import numpy as np
import math
from collections import Counter


def make_freq_dict(L):

	frequency = {}
	minimum = min(L)
	maximum = max(L)
	R = max(L) - min(L)
	K = len(L)
	
	Nr = max([0,math.log2(R/((K**(0.3))*math.sqrt(2)))])
	Nf = math.ceil(R/(2**Nr))
	
	bbins = []

	for i in range(Nf + 1):
		bbins.append(minimum + (2**Nr)*i)

	primary = []
	offset = []
	bbins = [int(x) for x in bbins]
	
	frequency = {str(x):0 for x in range(1,Nf+1)}
	
	for number in L:
		for i in range(Nf):
			if number <= bbins[i+1] and number >= bbins[i]:
				frequency[str(i+1)] += 1/K
				if number < 0:
					offset.append(number - bbins[i])

				if number > 0:
					offset.append(number - bbins[i])
				
				primary.append(i+1)
				
				break
	cum_prob = np.zeros(len(frequency) + 1)

	cum_prob[0] = 0
	cum_prob[1] = frequency['1']
	for i in range(2,len(frequency)+1):
		cum_prob[i] = cum_prob[i-1] + frequency[str(i)]

	print(cum_prob)
	
		
	return cum_prob, primary, offset



def arithmetic_encode(cum_prob,primary):

	high = 1
	low = 0
	count = 0
	
	while True:
		try:
			range_ = high - low
			p1 = cum_prob[primary[count] - 1]
			p2 = cum_prob[primary[count]]
			high = low + range_*p2
			low = low + range_*p1

			count += 1
			

		except IndexError:	
			print((low + (high-low)/2))
			break
	
if __name__ == '__main__':


	L = [1,2,2,2,2,3,4,5,6,9,9,7,6,7,8,9,8,7,5,5,6,7,8]
	L = np.floor(np.random.normal(size=10, scale=20, loc=0))
	prob_dict = make_freq_dict(L)
	arithmetic_encode(prob_dict[0],prob_dict[1])
