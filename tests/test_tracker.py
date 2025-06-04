# test_tracker.py

import time
import pytest
from tracker import AttackTracker

def test_normal_traffic():
    """
    A single successful login should not be marked suspicious or blocked.
    """
    tracker = AttackTracker()
    result = tracker.record_attempt(
        ip="1.2.3.4",
        user_id="user1",
        geo="US",
        sim_type="manual",
        result="SUCCESS"
    )
    assert result["is_suspicious"] is False
    assert result["is_blocked"] is False

def test_bruteforce_detection_and_block():
    """
    Send repeated failures for the same (user, geo). After reaching brute_threshold,
    the next failure should be flagged suspicious; on one more, it should block.
    Default brute_threshold = 5.
    """
    tracker = AttackTracker()

    # Send (brute_threshold - 1) failures → should not yet be blocked
    for _ in range(tracker.brute_threshold - 1):
        r = tracker.record_attempt(
            ip="10.0.0.1",
            user_id="userBF",
            geo="EU",
            sim_type="manual",
            result="FAILURE"
        )
        assert r["is_suspicious"] is False
        assert r["is_blocked"] is False

    # The next failure (5th) should be flagged suspicious but not blocked
    r = tracker.record_attempt(
        ip="10.0.0.1",
        user_id="userBF",
        geo="EU",
        sim_type="manual",
        result="FAILURE"
    )
    assert r["is_suspicious"] is True
    assert r["is_blocked"] is False

    # Another failure immediately → should now block
    r2 = tracker.record_attempt(
        ip="10.0.0.1",
        user_id="userBF",
        geo="EU",
        sim_type="manual",
        result="FAILURE"
    )
    assert r2["is_suspicious"] is True
    assert r2["is_blocked"] is True

def test_geohop_detection_and_block():
    """
    Send alternating geo values for the same user. Default geohop_threshold = 2.
    2 geo‐hops in a row → suspicious; on the 3rd distinct hop → block.
    """
    tracker = AttackTracker()
    user = "userGH"

    # First hop: no last_geo exists, so suspicious=False
    r1 = tracker.record_attempt(ip="2.2.2.2", user_id=user, geo="US", sim_type="geohop", result="SUCCESS")
    assert r1["is_suspicious"] is False
    assert r1["is_blocked"] is False

    # Second hop (different geo) → now length of user_hops = 2 == threshold → suspicious but not blocked
    r2 = tracker.record_attempt(ip="2.2.2.3", user_id=user, geo="CA", sim_type="geohop", result="SUCCESS")
    assert r2["is_suspicious"] is True
    assert r2["is_blocked"] is False

    # Third hop (another different geo) → should now block
    r3 = tracker.record_attempt(ip="2.2.2.4", user_id=user, geo="MX", sim_type="geohop", result="SUCCESS")
    assert r3["is_suspicious"] is True
    assert r3["is_blocked"] is True

def test_credential_stuffing_block():
    """
    Send failures from the same IP but with distinct user_ids.
    Default cred_threshold = 2, so after 2 distinct users, IP is marked suspicious.
    On the 3rd distinct user, should block.
    """
    tracker = AttackTracker()
    ip = "5.5.5.5"

    # First two distinct users → should be marked suspicious at the 2nd, but not blocked
    r1 = tracker.record_attempt(ip=ip, user_id="userA", geo="IN", sim_type="credstuff", result="FAILURE")
    assert r1["is_suspicious"] is False
    assert r1["is_blocked"] is False

    r2 = tracker.record_attempt(ip=ip, user_id="userB", geo="IN", sim_type="credstuff", result="FAILURE")
    assert r2["is_suspicious"] is True
    assert r2["is_blocked"] is False

    # Third distinct user → now should be blocked
    r3 = tracker.record_attempt(ip=ip, user_id="userC", geo="IN", sim_type="credstuff", result="FAILURE")
    assert r3["is_suspicious"] is True
    assert r3["is_blocked"] is True

def test_persistent_blocklist_override():
    """
    If a user or IP is manually inserted into blocklist sets, all future attempts must be blocked.
    """
    tracker = AttackTracker()

    # Manually add user to blocked_users
    tracker.blocked_users.add("blockedUser")
    r = tracker.record_attempt(ip="9.9.9.9", user_id="blockedUser", geo="US", sim_type="manual", result="SUCCESS")
    assert r["is_blocked"] is True
    assert r["is_suspicious"] is True

    # Manually add IP to blocked_ips
    tracker2 = AttackTracker()
    tracker2.blocked_ips.add("8.8.8.8")
    r2 = tracker2.record_attempt(ip="8.8.8.8", user_id="anyUser", geo="US", sim_type="manual", result="SUCCESS")
    assert r2["is_blocked"] is True
    assert r2["is_suspicious"] is True

def test_stats_and_recent_feed_consistency():
    """
    After a few attempts, get_stats() and get_recent() return consistent lengths and counts.
    """
    tracker = AttackTracker()
    # Simulate 3 attempts: 2 successes, 1 failure
    tracker.record_attempt(ip="1.1.1.1", user_id="x", geo="US", sim_type="manual", result="SUCCESS")
    tracker.record_attempt(ip="1.1.1.2", user_id="y", geo="US", sim_type="manual", result="FAILURE")
    tracker.record_attempt(ip="1.1.1.3", user_id="z", geo="US", sim_type="manual", result="SUCCESS")

    stats = tracker.get_stats()
    recent = tracker.get_recent(limit=3)

    # There should be at least one bucket with a total of 3 attempts
    assert sum(stats["attempts"]) == 3
    # Recent feed should return exactly 3 entries (most recent first)
    assert len(recent) == 3
    assert recent[0]["ip"] == "1.1.1.3"
    assert recent[-1]["ip"] == "1.1.1.1"
