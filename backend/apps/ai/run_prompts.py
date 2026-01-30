from backend.apps.ai.job_prompts import job_generation_prompt
from backend.apps.ai.utils import ask_model
import json, time

start = time.time()
def run_job_generation():
    prompt = job_generation_prompt(count=5)
    result = ask_model(prompt)

    print("Generated jobs:")
    print(json.dumps(result, indent=2))
    print("Elapsed:", round(time.time() - start, 2), "sec")


if __name__ == "__main__":
    run_job_generation()