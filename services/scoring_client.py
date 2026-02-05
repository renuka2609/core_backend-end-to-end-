import requests


def trigger_scoring(assessment_id):
    print("Scoring triggered for assessment:", assessment_id)

    try:
        response = requests.post(
            "http://scoring-service:8001/score",
            json={"assessment_id": assessment_id},
            timeout=3
        )

        print("Scoring response:", response.status_code)

    except Exception as e:
        print("Scoring failed:", str(e))

