"""
Rate Limiter for API Quota Management
"""
import time
from collections import deque


class RateLimiter:
    """
    Sliding window rate limiter for API quota control.
    Tracks calls per hour and enforces wait times when quota is exhausted.
    """
    def __init__(self, max_calls_per_hour: int):
        """
        Args:
            max_calls_per_hour: Maximum number of calls allowed in a rolling 1-hour window
        """
        self.max = max_calls_per_hour
        self.calls = deque()
    
    def wait_if_needed(self, cost: int = 1) -> float:
        """
        Register a consumption of 'cost' units.
        Returns:
            float: Seconds slept (if any)
        """
        now = time.time()
        # Clean old timestamps (older than 1 hour)
        while self.calls and now - self.calls[0] > 3600: 
            self.calls.popleft()
            
        slept = 0.0
        # Check if adding 'cost' would exceed limit
        # Logic: If len + cost > max, we must wait until enough expire
        if len(self.calls) + cost > self.max:
            # We need to free up 'needed' slots
            needed = (len(self.calls) + cost) - self.max
            
            # Use the timestamp of the 'needed'-th oldest item
            if needed <= len(self.calls):
                target_timestamp = self.calls[needed - 1]
                wait = 3600 - (now - target_timestamp) + 5  # +5s buffer
            else:
                wait = 3600 + 5 
                
            if wait > 0:
                print(f"⏳ Quota reached (Attempting {cost}, Limit {self.max}). Sleeping {wait:.1f}s")
                time.sleep(wait)
                slept = wait
                # Recalculate 'now' after sleep for accurate timestamps
                now = time.time()
                while self.calls and now - self.calls[0] > 3600: 
                    self.calls.popleft()
        
        # Register new calls
        for _ in range(cost):
            self.calls.append(now)
            
        return slept
