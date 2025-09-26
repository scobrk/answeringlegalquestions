#!/usr/bin/env python3
"""
Quick test script for the FastAPI endpoint
"""
import requests
import json

def test_api():
    url = "http://localhost:8080/api/query"

    payload = {
        "question": "For a business with a payroll of 3.4 million and 12 properties worth 43.2 million including parking space levy, how much would they pay in total?",
        "enable_approval": True,
        "include_metadata": True
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"Answer: {data['answer']}")
            print(f"Confidence: {data['confidence']}")
            print(f"Classification: {data['classification']}")
            print(f"Approval Status: {data['approval_status']}")
            print(f"Source Count: {data['source_count']}")
            if data['citations']:
                print("Citations:")
                for i, citation in enumerate(data['citations'], 1):
                    print(f"  {i}. {citation}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_api()