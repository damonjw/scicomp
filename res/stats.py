import IPython.display
from collections import namedtuple, OrderedDict
import numpy as np
import pandas
import math

class SummaryNumeric(namedtuple('SummaryNumeric', ['min','q25','med','mean','q75','max','nan'])):
    def _repr_html_(self):
        res = '<pre>'
        res += 'min:  {}\n'.format(self.min)
        res += '25%:  {}\n'.format(self.q25)
        res += 'med:  {}\n'.format(self.med)
        res += 'mean: {}\n'.format(self.mean)
        res += '75%:  {}\n'.format(self.q75)
        res += 'max:  {}'.format(self.max)
        if self.nan > 0:
            res += '\n(nan): {}'.format(self.nan)
        res += '</pre>'
        return res

class SummaryCategorical(list):
    def __init__(self, some_counts, levels, count):
        list.__init__(self, some_counts)
        self.count = count
        self.levels = levels
    def _repr_html_(self):
        res = '<pre>'
        res += '\n'.join('{v}: {n}'.format(v=v, n=n) for v,n in self)
        shown_count = sum(n for v,n in self)
        if shown_count < self.count:
            res += '\n({l} other{s}): {n}'.format(
                l = self.levels-len(self),
                s = '' if (self.count==shown_count+1) else 's',
                n = self.count - shown_count)
        res += '</pre>'
        return res

class SummaryTable(dict):
    def _repr_html_(self):
        res = ''
        for colname, details in self.items():
            res += '<div style="display: inline-block; font-size: 90%; background-color: rgb(240,240,240); margin: 0.5em; padding: 0.2em; vertical-align: top">'
            res += '<strong>' + colname + '</strong>'
            res += details._repr_html_()
            res += '</div>'
        return res

def summary(df):
    got_dict = isinstance(df, dict)
    if not got_dict:
        df = {None: df}
    res = OrderedDict()
    for colname, col in df.items():
        if np.issubdtype(col.dtype, np.number):
            q = np.nanpercentile(col, q=[0,25,50,75,100])
            res[colname] = SummaryNumeric(min=q[0], q25=q[1], med=q[2], q75=q[3], max=q[4],
                                          mean = np.nanmean(col),
                                          nan = np.count_nonzero(np.isnan(col)))
        else:
            vs,ns = np.unique(col, return_counts=True)
            i = np.argsort(-ns)[:5]
            res[colname] = SummaryCategorical(zip(vs[i], ns[i]), len(vs), len(col))
    return SummaryTable(res) if got_dict else res[None]




def different_digits(x, digits=None):
    if digits is None:
        digits = max(-math.floor(math.log(min(x), 10)) + 1, 0)
    for d in range(digits, max(12, digits)):
        fmt = '{:.' + str(d) + 'f}'
        s = [fmt.format(xx) for xx in x]
        if len(set(s)) == len(s):
            return s
    return [str(xx) for xx in x]


def cut(x, breaks, labels=None):
    if not isinstance(breaks, list):
        breaks = np.nanpercentile(x, [100/(breaks+1)*i for i in range(1, (breaks+1))])
    if len(np.unique(breaks)) < len(breaks):
        raise Exception("Breaks are not unique")
    y = np.digitize(x, breaks)
    y[np.isnan(x)] = -1
    if labels is None:
        breaks2 = ['-inf'] + different_digits(breaks) + ['inf']
        labels = ['{}{}, {})'.format('(' if i==0 else '[',l,h) for i,(l,h) in enumerate(zip(breaks2[:-1], breaks2[1:]))]
    else:
        if len(labels) != len(breaks) + 1:
            raise Exception('labels should have length {}, not {}'.format(len(labels), len(breaks)+1))
    return np.take(['nan'] + labels, y+1)


def crosstab(*args, data=None, value='n', format_=None, columns=None, **kwargs):
    cols = OrderedDict()
    for i,a in enumerate(args):
        if isinstance(a, str):
            if data is None:
                raise Exception("To refer to columns by name, 'data' must be provided")
            cols[a] = data[a]
        else:
            r = 0
            while True:
                r += 1
                k = 'X'*r + str(i)
                if k not in cols and k not in kwargs:
                    cols[k] = a
                    break
    for k,v in kwargs.items():
        if isinstance(v, str):
            if data is None:
                raise Exception("To refer to columns by name, 'data' must be provided")
            cols[k] = data[v]
        else:
            cols[k] = v
    x = pandas.DataFrame(cols).groupby(list(cols.keys())).size()
    if format_ == 'Series':
        return x
    elif format_ is None:
        # Work around a pandas bug: it ignores fill_value when unstacking multiple columns
        if columns is None:
            columns = range(1,len(cols.keys()),2)
        for i in columns:
            x = x.unstack(i, fill_value=0)
        return x
    elif format_ == 'DataFrame':
        if value is None:
            x = x.index.to_frame(index=False)
            x = x[list(reversed(x.columns.values))]
        else:
            x = x.to_frame(name=value).reset_index()
        return x
    else:
        raise Exception("Unrecognized value of 'format_'")
