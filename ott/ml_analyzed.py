from scipy.io import loadmat
import numpy as np
import pandas as pd

from ifcb.data.adc import SCHEMA_VERSION_1, SCHEMA_VERSION_2

ML_ANALYZED = 'ml_analyzed'
CLASSES = 'classes'
LIDS = 'lids'
TIMESTAMPS = 'timestamps'
LOOK_TIME = 'look_time'
RUN_TIME = 'run_time'

def read_ml_analyzed(path):
    mat = loadmat(path, squeeze_me=True)
    # ignore variables other than the following
    cols = ['filelist_all', 'looktime', 'minproctime', 'ml_analyzed', 'runtime']
    # convert to dataframe
    df = pd.DataFrame({ c: mat[c] for c in cols }, columns=cols)
    df.index = df.pop('filelist_all') # index by bin LID
    return df

def compute_ml_analyzed_s1_adc(adc):
    # first, make sure this isn't an empty bin
    if len(adc) == 0:
        return np.nan, np.nan, np.nan
    # we have targets, can proceed
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
    neg_adj = (adc[s.TRIGGER_OPEN_TIME] < 0) * 24*60*60.
    trigger_open_time = adc[s.TRIGGER_OPEN_TIME] + neg_adj
    # done with that case
    # run time is assumed to be final frame grab time
    run_time = frame_grab_time.iloc[-1]
    # proc time is time between trigger open time and previous
    # frame grab time
    proc_time = np.array(trigger_open_time.iloc[1:]) - np.array(frame_grab_time[:-1])
    # set all proc times that are less than min to min
    proc_time[proc_time < MIN_PROC_TIME] = MIN_PROC_TIME
    # look time is run time - proc time
    # not sure why subtracting MIN_PROC_TIME here is necessary
    # to match output from MATLAB code, that code may have a bug
    look_time = run_time - proc_time.sum() - MIN_PROC_TIME
    # ml analyzed is look time times flow rate
    ml_analyzed = look_time * FLOW_RATE
    return ml_analyzed, look_time, run_time

def compute_ml_analyzed_s1(abin):
    return compute_ml_analyzed_s1_adc(abin.adc)

def compute_ml_analyzed_s2(abin):
    FLOW_RATE = 0.25 # ml/minute
    # ml analyzed is (run time - inhibit time) * flow rate
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
    lids = []
    timestamps = []
    ml_analyzed = []
    look_time = []
    run_time = []

    for b in data_dir:
        lids.append(b.lid)
        timestamps.append('{}'.format(b.timestamp))
        ma, lt, rt = compute_ml_analyzed(b)
        if log_callback is not None:
            log_callback('{} {:.3f}'.format(b.lid, ma))
        ml_analyzed.append(ma)
        look_time.append(lt)
        run_time.append(rt)

    return {
        LIDS: lids,
        TIMESTAMPS: timestamps,
        ML_ANALYZED: ml_analyzed,
        LOOK_TIME: look_time,
        RUN_TIME: run_time
    }

def ml_analyzed2df(js):
    """given the output of summarize_ml_analyzed, return
    a dataframe indexed by timestamp"""
    timestamps = [pd.to_datetime(ts) for ts in js[TIMESTAMPS]]
    data = {
        'lid': js[LIDS],
        ML_ANALYZED: js[ML_ANALYZED],
        LOOK_TIME: js[LOOK_TIME],
        RUN_TIME: js[RUN_TIME]
    }
    return pd.DataFrame(data, index=timestamps)

def ml_analyzed2dict(js):
    """given the output of summarize_ml_analyzed, return
    a dict keyed by lid with ml_analyzed as values"""
    return dict(zip(js[LIDS],js[ML_ANALYZED]))