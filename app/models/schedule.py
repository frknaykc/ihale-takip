from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import time

class ScheduleConfig(BaseModel):
    """Mail gönderimi için zamanlama ayarları"""
    times: List[time]  # time objesi formatında saatler
    is_active: bool = True

class ScheduleUpdate(BaseModel):
    """Mail gönderimi için güncelleme modeli"""
    times: List[str]  # HH:MM formatında saatler
    is_active: bool = True

    def to_schedule_config(self) -> ScheduleConfig:
        """ScheduleUpdate'i ScheduleConfig'e dönüştürür"""
        time_objects = []
        for time_str in self.times:
            hour, minute = map(int, time_str.split(':'))
            time_objects.append(time(hour, minute))
        
        return ScheduleConfig(
            times=time_objects,
            is_active=self.is_active
        )