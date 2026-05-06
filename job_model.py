#!/usr/bin/env python3
"""Job data model"""

from datetime import datetime
from typing import List, Dict, Any, Optional

class Job:
    def __init__(self, 
                 title: str = "",
                 company: str = "",
                 location: str = "",
                 link: str = "",
                 source: str = "",
                 timestamp: str = "",
                 visa_sponsorship: str = "",
                 remote_work: str = ""):
        self.title = title
        self.company = company
        self.location = location
        self.link = link
        self.source = source
        self.timestamp = timestamp
        self.visa_sponsorship = visa_sponsorship
        self.remote_work = remote_work
    
    def to_dict(self):
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "link": self.link,
            "source": self.source,
            "timestamp": self.timestamp,
            "visa_sponsorship": self.visa_sponsorship,
            "remote_work": self.remote_work
        }