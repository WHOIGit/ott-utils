from collections import defaultdict

from scipy.io import loadmat
import numpy as np
import pandas as pd

from .common import parse_timestamps, unparse_timestamp

from ifcb.data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2

ML_ANALYZED = 'ml_analyzed'
CLASSES = 'classes'
LIDS = 'lids'
LID = 'lid'
TIMESTAMPS = 'timestamps'
LOOK_TIME = 'look_time'
RUN_TIME = 'run_time'

MIN_PROC_TIME = 0.073

def compute_ml_analyzed_s1_adc(adc, min_proc_time):
    # first, make sure this isn't an empty bin
    if len(adc) == 0:
        return np.nan, np.nan, np.nan
    # we have targets, can proceed
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
    neg_adj = (adc[s.TRIGGER_OPEN_TIME] < 0) * 24*60*60.
    trigger_open_time = adc[s.TRIGGER_OPEN_TIME] + neg_adj
    # done with that case
    # run time is assumed to be final frame grab time
    run_time = frame_grab_time.iloc[-1]
    # proc time is time between trigger open time and previous
    # frame grab time
    proc_time = np.array(trigger_open_time.iloc[1:]) - np.array(frame_grab_time[:-1])
    # set all proc times that are less than min to min
    proc_time[proc_time < min_proc_time] = min_proc_time
    # look time is run time - proc time
    # not sure why subtracting min_proc_time here is necessary
    # to match output from MATLAB code, that code may have a bug
    look_time = run_time - proc_time.sum() - min_proc_time
    # ml analyzed is look time times flow rate
    ml_analyzed = look_time * FLOW_RATE
    return ml_analyzed, look_time, run_time

def compute_ml_analyzed_s1(abin, min_proc_time=MIN_PROC_TIME):
    return compute_ml_analyzed_s1_adc(abin.adc, min_proc_time)

def compute_ml_analyzed_s2(abin):
    FLOW_RATE = 0.25 # ml/minute
    # ml analyzed is (run time - inhibit time) * flow rate
    run_time = abin.headers['runTime']
    inhibit_time = abin.headers['inhibitTime']
    look_time = run_time - inhibit_time
    ml_analyzed = FLOW_RATE * (look_time / 60.)
    return ml_analyzed, look_time, run_time

def compute_ml_analyzed(abin, min_proc_time=MIN_PROC_TIME):
    """returns ml_analyzed, look time, run time"""
    s = abin.schema
    if s is SCHEMA_VERSION_1:
        return compute_ml_analyzed_s1(abin, min_proc_time)
    elif s is SCHEMA_VERSION_2:
        return compute_ml_analyzed_s2(abin)

def summarize_ml_analyzed(data_dir, log_callback=None):
    """summarize ml_analyzed for an entire data dir.
    data_dir is any iterable of bins.
    result is a JSON-serializable dict:
    {
        LIDS: [lid1, lid2 ...],
        TIMESTAMPS: [ts1, ts2, ...],
        ML_ANALYZED: [ma1, ma2, ...]
        LOOK_TIME: [lt1, lt2 ...]
        RUN_TIME: [rt1, rt2 ...]
    }
    """
    summary = defaultdict(lambda: [])

    for b in data_dir:
        ml_analyzed, look_time, run_time = compute_ml_analyzed(b)
        if log_callback is not None:
            log_callback('{} {:.3f}'.format(b.lid, ml_analyzed))
        summary[LIDS].append(b.lid)
        summary[TIMESTAMPS].append(unparse_timestamp(b.timestamp))
        summary[ML_ANALYZED].append(ml_analyzed)
        summary[LOOK_TIME].append(look_time)
        summary[RUN_TIME].append(run_time)

    return summary

def ml_analyzed2df(js):
    """given the output of summarize_ml_analyzed, return
    a dataframe indexed by timestamp"""
    timestamps = parse_timestamps(js[TIMESTAMPS])
    data = {
        LID: js[LIDS],
        ML_ANALYZED: js[ML_ANALYZED],
        LOOK_TIME: js[LOOK_TIME],
        RUN_TIME: js[RUN_TIME]
    }
    return pd.DataFrame(data, index=timestamps)

def ml_analyzed2dict(js):
    """given the output of summarize_ml_analyzed, return
    a dict keyed by lid with ml_analyzed as values"""
    return dict(zip(js[LIDS],js[ML_ANALYZED]))