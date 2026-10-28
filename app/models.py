from datetime import datetime, timezone, timedelta
import re
from pydantic import BaseModel, ConfigDict, AwareDatetime, Field, FiniteFloat, StrictInt, field_validator
from app.catalog import SENSORS

class Reading(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sensor_id: str
    asset_id: str
    ts: AwareDatetime
    value: FiniteFloat
    unit: str
    quality: StrictInt = Field(ge=0,le=100)
    seq: StrictInt = Field(ge=0,le=9223372036854775807)

    @field_validator('value', mode='before')
    @classmethod
    def numeric(cls,v):
        if isinstance(v,bool) or not isinstance(v,(int,float)):
            raise ValueError('valor deve ser numérico')
        return v

    @field_validator('ts', mode='before')
    @classmethod
    def iso_timestamp(cls,v):
        if not isinstance(v,datetime) and (not isinstance(v,str) or not re.match(r'^\d{4}-\d{2}-\d{2}T',v)):
            raise ValueError('timestamp deve ser ISO-8601 com fuso')
        return v

    @field_validator('ts')
    @classmethod
    def timestamp(cls,v):
        if v > datetime.now(timezone.utc)+timedelta(seconds=30):
            raise ValueError('timestamp futuro')
        return v.astimezone(timezone.utc)

    def validate_catalog(self, topic):
        s = SENSORS.get(self.sensor_id)
        if not s: raise ValueError('sensor desconhecido')
        if self.asset_id != s['asset_id']: raise ValueError('ativo incompatível')
        if self.unit != s['unit']: raise ValueError('unidade incompatível')
        if topic != s['topic']: raise ValueError('tópico incompatível')
        return self

def severity(value, thresholds):
    if not thresholds: return 'NORMAL'
    for level in ('critical','warn'):
        high, low = thresholds.get(level+'_high'), thresholds.get(level+'_low')
        if (high is not None and value > high) or (low is not None and value < low):
            return level.upper()
    return 'NORMAL'
