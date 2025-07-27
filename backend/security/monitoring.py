"""
Security monitoring and logging utilities.
Provides security event tracking and suspicious activity detection.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Types of security events to monitor."""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    
    # Authorization events
    ACCESS_DENIED = "access_denied"
    ADMIN_ACCESS = "admin_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    
    # Input validation events
    INJECTION_ATTEMPT = "injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    INVALID_INPUT = "invalid_input"
    
    # Rate limiting events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BOT_DETECTED = "bot_detected"
    
    # API security events
    INVALID_API_KEY = "invalid_api_key"
    API_ABUSE = "api_abuse"
    UNAUTHORIZED_API_ACCESS = "unauthorized_api_access"
    
    # System security events
    FILE_UPLOAD_BLOCKED = "file_upload_blocked"
    MALICIOUS_REQUEST = "malicious_request"
    SECURITY_VIOLATION = "security_violation"


class SeverityLevel(Enum):
    """Security event severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    
    event_type: SecurityEventType
    severity: SeverityLevel
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    timestamp: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging."""
        event_dict = asdict(self)
        event_dict['event_type'] = self.event_type.value
        event_dict['severity'] = self.severity.value
        if self.timestamp:
            event_dict['timestamp'] = self.timestamp.isoformat()
        return event_dict
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class SecurityMonitor:
    """Security monitoring and alerting system."""
    
    def __init__(self):
        # Recent events for pattern detection
        self.recent_events: deque = deque(maxlen=1000)
        
        # IP-based tracking
        self.ip_tracking: Dict[str, Dict] = defaultdict(lambda: {
            "failed_logins": deque(maxlen=10),
            "blocked_requests": deque(maxlen=20),
            "suspicious_score": 0,
            "last_activity": None
        })
        
        # User-based tracking
        self.user_tracking: Dict[str, Dict] = defaultdict(lambda: {
            "login_attempts": deque(maxlen=10),
            "privilege_changes": deque(maxlen=5),
            "api_usage": deque(maxlen=50),
            "risk_score": 0
        })
        
        # Global threat level
        self.threat_level = SeverityLevel.LOW
        
        # Alert thresholds
        self.thresholds = {
            "failed_logins_per_ip": 5,
            "failed_logins_per_user": 3,
            "rate_limit_violations": 10,
            "injection_attempts": 3,
            "high_severity_events": 5
        }
    
    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event and analyze for threats.
        
        Args:
            event: SecurityEvent to log
        """
        # Add to recent events
        self.recent_events.append(event)
        
        # Log to system logger
        log_level = self._get_log_level(event.severity)
        logger.log(log_level, f"Security Event: {event.to_json()}")
        
        # Update tracking data
        self._update_tracking(event)
        
        # Analyze for threats
        self._analyze_threats(event)
        
        # Check for alerts
        self._check_alerts(event)
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security summary for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Security summary dictionary
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent events
        recent = [
            event for event in self.recent_events
            if event.timestamp and event.timestamp > cutoff_time
        ]
        
        # Count events by type and severity
        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent:
            event_counts[event.event_type.value] += 1
            severity_counts[event.severity.value] += 1
        
        # Calculate threat indicators
        threat_indicators = {
            "failed_logins": event_counts.get("login_failed", 0),
            "injection_attempts": (
                event_counts.get("injection_attempt", 0) +
                event_counts.get("xss_attempt", 0)
            ),
            "rate_limit_violations": event_counts.get("rate_limit_exceeded", 0),
            "access_denied": event_counts.get("access_denied", 0),
            "critical_events": severity_counts.get("critical", 0)
        }
        
        # Determine overall threat level
        overall_threat = self._calculate_threat_level(threat_indicators)
        
        return {
            "period_hours": hours,
            "total_events": len(recent),
            "threat_level": overall_threat.value,
            "event_counts": dict(event_counts),
            "severity_counts": dict(severity_counts),
            "threat_indicators": threat_indicators,
            "top_threat_ips": self._get_top_threat_ips(),
            "suspicious_users": self._get_suspicious_users()
        }
    
    def is_ip_suspicious(self, ip_address: str) -> bool:
        """
        Check if an IP address is considered suspicious.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            True if IP is suspicious
        """
        if ip_address not in self.ip_tracking:
            return False
        
        tracking = self.ip_tracking[ip_address]
        
        # Check recent failed logins
        recent_fails = len([
            t for t in tracking["failed_logins"]
            if datetime.utcnow() - t < timedelta(minutes=15)
        ])
        
        if recent_fails >= self.thresholds["failed_logins_per_ip"]:
            return True
        
        # Check suspicious score
        if tracking["suspicious_score"] > 50:
            return True
        
        return False
    
    def is_user_at_risk(self, user_id: str) -> bool:
        """
        Check if a user account is at risk.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if user is at risk
        """
        if user_id not in self.user_tracking:
            return False
        
        tracking = self.user_tracking[user_id]
        
        # Check risk score
        if tracking["risk_score"] > 70:
            return True
        
        # Check recent failed attempts
        recent_attempts = len([
            t for t in tracking["login_attempts"]
            if datetime.utcnow() - t < timedelta(minutes=30)
        ])
        
        if recent_attempts >= self.thresholds["failed_logins_per_user"]:
            return True
        
        return False
    
    def _update_tracking(self, event: SecurityEvent) -> None:
        """Update tracking data based on event."""
        current_time = datetime.utcnow()
        
        # Update IP tracking
        if event.ip_address:
            ip_data = self.ip_tracking[event.ip_address]
            ip_data["last_activity"] = current_time
            
            if event.event_type == SecurityEventType.LOGIN_FAILED:
                ip_data["failed_logins"].append(current_time)
                ip_data["suspicious_score"] += 10
            elif event.event_type in [SecurityEventType.INJECTION_ATTEMPT, SecurityEventType.XSS_ATTEMPT]:
                ip_data["blocked_requests"].append(current_time)
                ip_data["suspicious_score"] += 25
            elif event.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED:
                ip_data["suspicious_score"] += 5
        
        # Update user tracking
        if event.user_id:
            user_data = self.user_tracking[event.user_id]
            
            if event.event_type == SecurityEventType.LOGIN_FAILED:
                user_data["login_attempts"].append(current_time)
                user_data["risk_score"] += 15
            elif event.event_type == SecurityEventType.LOGIN_SUCCESS:
                user_data["risk_score"] = max(0, user_data["risk_score"] - 5)
            elif event.event_type == SecurityEventType.PRIVILEGE_ESCALATION:
                user_data["privilege_changes"].append(current_time)
                user_data["risk_score"] += 30
    
    def _analyze_threats(self, event: SecurityEvent) -> None:
        """Analyze event for threat patterns."""
        current_time = datetime.utcnow()
        
        # Check for coordinated attacks (multiple IPs, same pattern)
        if event.event_type in [SecurityEventType.LOGIN_FAILED, SecurityEventType.INJECTION_ATTEMPT]:
            recent_similar = [
                e for e in self.recent_events
                if (e.event_type == event.event_type and
                    e.timestamp and
                    current_time - e.timestamp < timedelta(minutes=5) and
                    e.ip_address != event.ip_address)
            ]
            
            if len(recent_similar) > 3:
                logger.warning(f"Potential coordinated attack detected: {event.event_type.value}")
        
        # Check for privilege escalation patterns
        if event.user_id and event.event_type == SecurityEventType.ADMIN_ACCESS:
            user_events = [
                e for e in self.recent_events
                if (e.user_id == event.user_id and
                    e.timestamp and
                    current_time - e.timestamp < timedelta(hours=1))
            ]
            
            # Look for unusual admin access patterns
            if len(user_events) > 10:
                logger.warning(f"Unusual admin activity pattern for user: {event.user_id}")
    
    def _check_alerts(self, event: SecurityEvent) -> None:
        """Check if event should trigger alerts."""
        
        # Critical events always trigger alerts
        if event.severity == SeverityLevel.CRITICAL:
            self._send_alert(event, "Critical security event detected")
        
        # Check for threshold breaches
        if event.ip_address and self.is_ip_suspicious(event.ip_address):
            self._send_alert(event, f"Suspicious IP activity: {event.ip_address}")
        
        if event.user_id and self.is_user_at_risk(event.user_id):
            self._send_alert(event, f"User account at risk: {event.user_id}")
    
    def _send_alert(self, event: SecurityEvent, message: str) -> None:
        """Send security alert (placeholder for actual alerting system)."""
        logger.error(f"SECURITY ALERT: {message} - Event: {event.to_json()}")
        
        # In a production system, you would:
        # - Send email/SMS notifications
        # - Post to Slack/Teams
        # - Create incident tickets
        # - Trigger automated responses
    
    def _get_log_level(self, severity: SeverityLevel) -> int:
        """Get Python logging level for severity."""
        mapping = {
            SeverityLevel.LOW: logging.INFO,
            SeverityLevel.MEDIUM: logging.WARNING,
            SeverityLevel.HIGH: logging.ERROR,
            SeverityLevel.CRITICAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.INFO)
    
    def _calculate_threat_level(self, indicators: Dict[str, int]) -> SeverityLevel:
        """Calculate overall threat level from indicators."""
        score = 0
        
        # Weight different threat indicators
        score += indicators.get("critical_events", 0) * 10
        score += indicators.get("injection_attempts", 0) * 5
        score += indicators.get("failed_logins", 0) * 2
        score += indicators.get("rate_limit_violations", 0) * 1
        
        if score >= 50:
            return SeverityLevel.CRITICAL
        elif score >= 25:
            return SeverityLevel.HIGH
        elif score >= 10:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _get_top_threat_ips(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top threat IPs by suspicious score."""
        threat_ips = [
            {
                "ip": ip,
                "score": data["suspicious_score"],
                "failed_logins": len(data["failed_logins"]),
                "blocked_requests": len(data["blocked_requests"])
            }
            for ip, data in self.ip_tracking.items()
            if data["suspicious_score"] > 0
        ]
        
        return sorted(threat_ips, key=lambda x: x["score"], reverse=True)[:limit]
    
    def _get_suspicious_users(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get users with highest risk scores."""
        suspicious_users = [
            {
                "user_id": user_id,
                "risk_score": data["risk_score"],
                "failed_attempts": len(data["login_attempts"]),
                "privilege_changes": len(data["privilege_changes"])
            }
            for user_id, data in self.user_tracking.items()
            if data["risk_score"] > 0
        ]
        
        return sorted(suspicious_users, key=lambda x: x["risk_score"], reverse=True)[:limit]


# Global security monitor instance
security_monitor = SecurityMonitor()