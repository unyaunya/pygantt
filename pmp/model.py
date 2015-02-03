#! python3
# -*- coding: utf-8 -*-

from .util import s2dt, dt2s, dt
from .task import Task
from datetime import timedelta
import json, codecs

class TaskModel(Task):
    def __init__(self, name='未設定', start=dt.today(), end=None, pv=0, ev=0):
        if end is None:
            end = start+timedelta(days=100)
        super(TaskModel, self).__init__(name, start, end, pv, ev)

    def getEvmData(self):
        _ONEDAY = timedelta(days=1)
        data = []
        d = self.start
        while d <= self.end:
            data.append((d, self.pvFromDate(d), 0))
            d += _ONEDAY
        return data

    @staticmethod
    def dump(obj, path):
        with codecs.open(path, 'w', 'utf8') as f:
            json.dump(obj, f, indent=2, default=_to_json, ensure_ascii=False)

    @staticmethod
    def load(path):
        with open(path, mode='r', encoding='utf-8') as f:
            return json.load(f, object_hook=_from_json)

def _to_json(obj):
    if isinstance(obj, (TaskModel, Task)):
        if isinstance(obj, TaskModel):
            aDict = {'__class__': 'pygantt.TaskModel'}
        else:
            aDict = {'__class__': 'pygantt.Task'}
        aDict['name']       = obj.name
        aDict['start']      = dt2s(obj.start)
        aDict['end']        = dt2s(obj.end)
        aDict['pv']         = obj.pv
        aDict['ev']         = obj.ev
        aDict['children']   = obj.children
        aDict['expanded']   = obj.expanded
        if obj.pic is not None and len(obj.pic) > 0:
            aDict['pic']   = obj.pic
        return aDict
    raise TypeError(repr(obj) + ' is not JSON serializable')

def _from_json(json_object):
    jso = json_object
    if '__class__' in jso:
        _class = None
        if jso['__class__'] == 'pygantt.Task':
            _class = Task
        elif jso['__class__'] == 'pygantt.TaskModel':
            _class = TaskModel
        if _class is not None:
            model = _class(
                    name = jso['name'],
                    start = s2dt(jso['start']),
                    end = s2dt(jso['end']),
                    pv = jso['pv'],
                    ev = jso['ev'],
                    )
            model.children = jso['children']
            model.expanded = jso.get('expanded', True)
            model.pic = jso.get('pic', None)
            return model
    return json_object
