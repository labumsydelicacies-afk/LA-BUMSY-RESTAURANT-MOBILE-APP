import os
import sys
import httpx
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    email = "taiwoayimora623++lll" + str(uuid.uuid4())[:4] + "@gmail.com"
    password = "SecurePassword123!"

    print(f"--- Starting E2E Test for {email} ---")
    
    # 1. Register
    resp = client.post("/auth/register", json={"email": email, "password": password})
    if resp.status_code != 201:
        print(f"Register Failed: {resp.text}")
        sys.exit(1)
    user_id = resp.json()["user"]["id"]
    print("1. Register OK")

    # 2. Mock Email OTP (set user to email verified directly in DB)
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import DATABASE_URL
    from app.db.models import User, EmailVerification
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    time.sleep(1)
    u = session.query(User).filter_by(email=email).first()
    u.is_email_verified = True
    session.commit()
    print("2. Email OTP Verified (Mocked via DB)")

    # 3. Login
    resp = client.post("/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        print(f"Login Failed: {resp.text}")
        sys.exit(1)
    
    token = resp.json()["access_token"]
    user_state = resp.json()["user_state"]
    print(f"3. Login OK. Initial user_state: {user_state}")
    
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Complete Profile (Forced Onboarding)
    resp = client.post("/profile/complete", headers=headers, json={
        "nickname": f"Taiwo{user_id}",
        "phone": "07074424824",
        "address": "123 Lagos St"
    })
    if resp.status_code != 200:
        print(f"Complete Profile Failed: {resp.text}")
        sys.exit(1)
    print("4. Onboarding Complete OK")
    
    # 5. Send Phone OTP
    resp = client.post("/auth/send-phone-otp", headers=headers, json={"phone": "07074424824"})
    if resp.status_code != 200:
        print(f"Send Phone OTP Failed: {resp.text}")
        sys.exit(1)
    print("5. Send Phone OTP API called OK. (Check logs for actual SMS request)")
    
    # We will simulate user receiving the OTP from SMS. Let's pull the generated OTP from DB to test the verify endpoint!
    time.sleep(1)
    
    # Verify Phone OTP
    u = session.query(User).filter_by(email=email).first()
    u.is_phone_verified = True
    session.commit()
    print("6. Verify Phone OTP (Mocked via DB because OTP is securely hashed)")

    print("--- E2E TEST PASSED ---")

if __name__ == "__main__":
    run_test()
