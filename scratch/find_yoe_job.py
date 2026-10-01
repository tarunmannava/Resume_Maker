from backend.app.services.job_queue import list_jobs
from backend.app.services.screening_classifier import hard_disqualifier

needles = ("10+ years", "silicon workflow", "apple container", "podman")
for j in list_jobs(status="all", limit=1000):
    d = (j.get("description_text") or "").lower()
    if any(n in d for n in needles):
        r = hard_disqualifier(j["title"], j.get("description_text") or "")
        print("---")
        print(j["status"], "|", j["id"])
        print(j["title"], "@", j["company"], "| stack=", j.get("primary_stack"))
        print("flag_reason", j.get("flag_reason"), "| now", r)
        idx = d.find("10+")
        if idx < 0:
            idx = d.find("silicon")
        print((j.get("description_text") or "")[max(0, idx - 80) : idx + 160].replace("\n", " "))
