import time

def call_scoring_service(assessment_id, timeout=5):
    """
    Dummy scoring service call.
    Replace this later with real HTTP call.
    """

    # simulate delay
    time.sleep(1)

    # fake scoring response
    return {
        "score": 75.0,
        "risk_level": "MEDIUM"
    }
