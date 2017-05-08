from scipy.io import loadmat
import pandas as pd

from ifcb.data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2

def read_ml_analyzed(path):
	mat = loadmat(path, squeeze_me=True)
	# ignore variables other than the following
	cols = ['filelist_all', 'looktime', 'minproctime', 'ml_analyzed', 'runtime']
	# convert to dataframe
	df = pd.DataFrame({ c: mat[c] for c in cols }, columns=cols)
	df.index = df.pop('filelist_all') # index by bin LID
	return df

def compute_ml_analyzed_s1(abin):
	raise NotImplementedError

def compute_ml_analyzed_s2(abin):
	FLOW_RATE = 0.25 # ml/minute
	run_time = abin.headers['runTime']
	inhibit_time = abin.headers['inhibitTime']
	look_time = run_time - inhibit_time
	ml_analyzed = FLOW_RATE * (look_time / 60.)
	return ml_analyzed, look_time, run_time

def compute_ml_analyzed(abin):
	"""returns ml_analyzed, look time, run time"""
	s = abin.schema
	if s is SCHEMA_VERSION_1:
		return compute_ml_analyzed_s1(abin)
	elif s is SCHEMA_VERSION_2:
		return compute_ml_analyzed_s2(abin)