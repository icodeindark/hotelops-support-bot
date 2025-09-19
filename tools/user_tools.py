import json, os

USERS_FILE = os.path.join("context", "users.json")

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def list_users():
    users = load_users()
    return users

def create_user(user):
    users = load_users()
    users.append(user)
    save_users(users)
    return f"User {user['name']} created."

def edit_user(user_id, updates):
    users = load_users()
    for u in users:
        if u["id"] == user_id:
            u.update(updates)
            save_users(users)
            return f"User {user_id} updated."
    return f"User {user_id} not found."

def delete_user(user_id):
    users = load_users()
    users = [u for u in users if u["id"] != user_id]
    save_users(users)
    return f"User {user_id} deleted."
