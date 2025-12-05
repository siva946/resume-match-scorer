from fastapi import HTTPException, Request
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio

class RateLimiter:
    def __init__(self, requests_per_minute: int = 10, requests_per_hour: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests: Dict[str, list] = defaultdict(list)
        self.hour_requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        now = datetime.utcnow()
        
        async with self.lock:
            # Clean old entries
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            
            self.minute_requests[client_ip] = [
                ts for ts in self.minute_requests[client_ip] if ts > minute_ago
            ]
            self.hour_requests[client_ip] = [
                ts for ts in self.hour_requests[client_ip] if ts > hour_ago
            ]
            
            # Check limits
            if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
                raise HTTPException(status_code=429, detail="Rate limit exceeded: too many requests per minute")
            
            if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
                raise HTTPException(status_code=429, detail="Rate limit exceeded: too many requests per hour")
            
            # Add current request
            self.minute_requests[client_ip].append(now)
            self.hour_requests[client_ip].append(now)

rate_limiter = RateLimiter()
