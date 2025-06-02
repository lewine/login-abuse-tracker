import time
import pytest
from tracker import AttackTracker

def test_normal_traffic():
    tracker = AttackTracker()
    result = tracker.record_attempt(
        ip="1.2.3.4",
        user_id="user1",
        geo="US",
        sim_type="manual",
        result="SUCCESS"
    )
    assert not result["is_suspicious"]
    assert not result["is_blocked"]

def test_brute_force_blocking():
    tracker = AttackTracker()
    ip = "1.2.3.4"
    user = "100"
    geo = "US:NY"
    
    # Send 4 failed attempts (just under the BRUTE_THRESHOLD of 5)
    for _ in range(4):
        result = tracker.record_attempt(ip, user, geo, "bruteforce", "FAILURE")
        assert result["is_suspicious"] is False
        assert result["is_blocked"] is False
    
    # 5th failed attempt = should trigger suspicion
    result = tracker.record_attempt(ip, user, geo, "bruteforce", "FAILURE")
    assert result["is_suspicious"] is True
    assert result["is_blocked"] is False  # still not blocked yet

    # 6th failed attempt = should now escalate to blocked
    result = tracker.record_attempt(ip, user, geo, "bruteforce", "FAILURE")
    assert result["is_suspicious"] is True
    assert result["is_blocked"] is True

def test_geo_hop_block():
    tracker = AttackTracker()
    # First login (normal)
    tracker.record_attempt(ip="1.2.3.4", user_id="user2", geo="US", sim_type="geo-hop", result="FAILURE")
    # Second login from different geo → suspicious
    tracker.record_attempt(ip="1.2.3.4", user_id="user2", geo="RU", sim_type="geo-hop", result="FAILURE")
    # Third login from yet another geo → now blocked
    result = tracker.record_attempt(ip="1.2.3.4", user_id="user2", geo="CN", sim_type="geo-hop", result="FAILURE")
    assert result["is_suspicious"]
    assert result["is_blocked"]

def test_credential_stuffing_block():
    tracker = AttackTracker()
    # First suspicious (2 distinct users → marked IP suspicious)
    tracker.record_attempt(ip="5.6.7.8", user_id="user3", geo="CN", sim_type="cred-stuff", result="FAILURE")
    tracker.record_attempt(ip="5.6.7.8", user_id="user4", geo="CN", sim_type="cred-stuff", result="FAILURE")
    # Second time from same IP → now triggers block
    result = tracker.record_attempt(ip="5.6.7.8", user_id="user5", geo="CN", sim_type="cred-stuff", result="FAILURE")
    assert result["is_suspicious"]
    assert result["is_blocked"]
