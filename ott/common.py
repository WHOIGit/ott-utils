from datetime import datetime, timedelta
from scipy.io import loadmat

CLASS2USE = 'class2useTB'
UNCLASSIFIED = 'unclassified'

def loadmat_validate(path, *keys):
    """load a mat file and check for the presence of given keys"""
    f = loadmat(path, squeeze_me=True)
    for k in f.keys():
        if k not in f:
            raise IOError('missing data in {}: {}'.format(path, k))
    return f

# util for converting MATLAB datenum to Python datetime
# as described in http://stackoverflow.com/questions/13965740/converting-matlabs-datenum-format-to-python
def datenum2datetime(matlab_datenum):
    dt = datetime.fromordinal(int(matlab_datenum)) + timedelta(days=matlab_datenum%1) - timedelta(days = 366)
    return dt

# util for converting datetime to MATLAB datenum
# as described in http://stackoverflow.com/questions/8776414/python-datetime-to-matlab-datenum
def datetime2datenum(dt):
   ord = dt.toordinal()
   mdn = dt + timedelta(days = 366)
   frac = (dt-datetime(dt.year,dt.month,dt.day,0,0,0)).seconds / (24.0 * 60.0 * 60.0)
   return mdn.toordinal() + frac

def split_column(df, colname, names):
    """
    Convert col = [[a1, b1, c1], [a2, b2, c2]]
    into
    col1 = [a1, a2]
    col2 = [b1, b2]
    col3 = [c1, c2]
    ]
    """
    for i, name in enumerate(names):
        df[name] = [v[i] for v in df[colname]]
    df.pop(colname)
    return df