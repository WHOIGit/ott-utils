from scipy.io import loadmat
import numpy as np
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

def compute_ml_analyzed_s1_adc(adc):
	MIN_PROC_TIME = 0.073
	STEPS_PER_SEC = 40.
	ML_PER_STEP = 5./48000.
	FLOW_RATE = ML_PER_STEP * STEPS_PER_SEC # ml/s
	s = SCHEMA_VERSION_1
	adc = adc.drop_duplicates(subset=s.TRIGGER, keep='first')
	# handle case of bins that span midnight
	# these have negative frame grab and trigger open times
	# that need to have 24 hours added to them
	neg_adj = (adc[s.FRAME_GRAB_TIME] < 0) * 24*60*60.
	frame_grab_time = adc[s.FRAME_GRAB_TIME] + neg_adj
	trigger_open_time = adc[s.TRIGGER_OPEN_TIME] + neg_adj
	# done with that case
	run_time = frame_grab_time.iloc[-1]
	proc_time = np.array(trigger_open_time.iloc[1:]) - np.array(frame_grab_time[:-1])
	proc_time[proc_time < MIN_PROC_TIME] = MIN_PROC_TIME
	look_time = run_time - proc_time.sum()
	ml_analyzed = look_time * FLOW_RATE
	return ml_analyzed, look_time, run_time

def compute_ml_analyzed_s1(abin):
	return compute_ml_analyzed_s1_adc(abin.adc)

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