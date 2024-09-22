import json
import os

class UserManager:
    def __init__(self):
        self.users_file = 'authorized_users.json'
        self.authorized_users = self.load_users()

    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                return json.load(f)
        return []

    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.authorized_users, f)

    def is_user_authorized(self, user_id):
        return user_id in self.authorized_users

    def add_authorized_user(self, user_id):
        if user_id not in self.authorized_users:
            self.authorized_users.append(user_id)
            self.save_users()

    def remove_authorized_user(self, user_id):
        if user_id in self.authorized_users:
            self.authorized_users.remove(user_id)
            self.save_users()