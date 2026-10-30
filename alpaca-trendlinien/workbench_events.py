"""Strict boundary for supplied point-in-time event records; never invent dates."""
import re
from complete_strategy import EventCalendar


def validate(payload):
    if not isinstance(payload,dict) or set(payload)!={'coverage','events'}:raise ValueError('coverage and events required')
    for group,fields in (('coverage',{'symbol','knownAt','fromAt','throughAt'}),('events',{'symbol','knownAt','at','kind'})):
        rows=payload[group]
        if not isinstance(rows,list) or len(rows)>100000:raise ValueError('bounded event rows required')
        for row in rows:
            if not isinstance(row,dict) or set(row)!=fields:raise ValueError('unknown calendar fields')
            if not isinstance(row['symbol'],str) or not re.fullmatch(r'[A-Z][A-Z0-9./-]{0,29}',row['symbol']):raise ValueError('invalid symbol')
            for k in fields-{'symbol','kind'}:
                if type(row[k]) is not int or row[k]<=0:raise ValueError('UTC Unix timestamps required')
            if group=='coverage' and row['fromAt']>row['throughAt']:raise ValueError('coverage interval reversed')
            if group=='events' and (row['kind'] not in ('earnings','dividend_announcement') or row['knownAt']>row['at']):raise ValueError('event must be known before occurrence')
    return payload


def calendar(payload=None):
    return EventCalendar(validate(payload) if payload is not None else None)
