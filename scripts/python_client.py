#!/usr/bin/env python3
import requests

BASE = "http://localhost:8000"

def register(username, display_name, password):
    r = requests.post(f"{BASE}/register", json={"username":username, "display_name":display_name, "password":password})
    r.raise_for_status()
    return r.json()

def login(username, password):
    r = requests.post(f"{BASE}/token", data={"username":username, "password":password})
    r.raise_for_status()
    return r.json()["access_token"]

def create_post(token, content, parent_id=None):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"content": content}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    r = requests.post(f"{BASE}/posts", json=payload, headers=headers)
    r.raise_for_status()
    return r.json()

def feed(page=0, page_size=50):
    r = requests.get(f"{BASE}/feed", params={"page": page, "page_size": page_size})
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print("Registering user alice...")
    print(register("alice2", "Alice Two", "secret"))
    token = login("alice2", "secret")
    print("Got token... creating a post")
    print(create_post(token, "Hello from python client"))
    print("Feed:\n", feed())
