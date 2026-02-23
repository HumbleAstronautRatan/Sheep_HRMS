import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# =========================================
# CONFIGURATION
# =========================================

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_JOB_POST_URL = "https://www.linkedin.com/talent/post-a-job"


# =========================================
# PREPARE LINKEDIN PAYLOAD
# =========================================

def prepare_linkedin_payload(jd_data: dict) -> dict:
    """
    Converts JD structured data into LinkedIn-ready format.
    """

    description = f"""
{jd_data.get('role')}

About the Role:
{jd_data.get('role_summary','')}

Responsibilities:
"""

    for r in jd_data.get("responsibilities", []):
        description += f"\n• {r}"

    description += "\n\nRequired Skills:\n"

    for s in jd_data.get("required_skills", []):
        description += f"\n• {s}"

    description += "\n\nApply now to join SheepAI Advisory LLP."

    payload = {
        "title": jd_data.get("role"),
        "location": jd_data.get("location"),
        "employment_type": jd_data.get("employment_type"),
        "description": description
    }

    return payload


# =========================================
# LINKEDIN ASSISTED POST
# =========================================

def post_job_assisted(jd_data: dict):
    """
    Opens LinkedIn job posting page and auto-fills form.
    Human must review and click 'Post'.
    """

    payload = prepare_linkedin_payload(jd_data)

    # Launch browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()

    # Step 1: Login
    driver.get(LINKEDIN_LOGIN_URL)
    print("Please login manually in the opened browser.")
    time.sleep(40)  # Wait for manual login

    # Step 2: Go to Job Posting Page
    driver.get(LINKEDIN_JOB_POST_URL)
    time.sleep(10)

    try:
        # Fill Job Title
        title_input = driver.find_element(By.XPATH, "//input[contains(@id,'jobTitle')]")
        title_input.clear()
        title_input.send_keys(payload["title"])
        time.sleep(2)

        # Fill Location
        location_input = driver.find_element(By.XPATH, "//input[contains(@id,'jobLocation')]")
        location_input.clear()
        location_input.send_keys(payload["location"])
        time.sleep(2)

        # Fill Description
        description_box = driver.find_element(By.XPATH, "//textarea")
        description_box.clear()
        description_box.send_keys(payload["description"])
        time.sleep(2)

        print("Job fields auto-filled.")
        print("Please review the details and click 'Post' manually.")

    except Exception as e:
        print("Could not auto-fill all fields. LinkedIn UI may have changed.")
        print("Error:", e)

    return "Browser opened for manual completion."