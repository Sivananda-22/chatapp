
import os
import tempfile
import unittest

import app as app_module
import database


class ChatAppTests(unittest.TestCase):

    def setUp(self):
        # Create a separate temporary database for each test
        self.temp_dir = tempfile.TemporaryDirectory()

        self.original_database = database.DATABASE
        database.DATABASE = os.path.join(
            self.temp_dir.name,
            "test_chat.db"
        )

        self.client = app_module.app.test_client()
        app_module.app.config["TESTING"] = True

        # Create the required database tables
        app_module.init_db()
        database.init_messages_table()

    def tearDown(self):
        # Restore the original database setting
        database.DATABASE = self.original_database

        # Delete the temporary test database
        self.temp_dir.cleanup()

    def register_user(self, username="testuser", password="test123"):
        return self.client.post(
            "/register",
            data={
                "username": username,
                "password": password
            }
        )

    def login_user(self, username="testuser", password="test123"):
        return self.client.post(
            "/login",
            data={
                "username": username,
                "password": password
            }
        )

    def test_registration(self):
        response = self.register_user()

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b"Registration successful!",
            response.data
        )

    def test_duplicate_username(self):
        self.register_user()

        response = self.register_user()

        self.assertIn(
            b"Username already exists!",
            response.data
        )

    def test_login_with_correct_password(self):
        self.register_user()

        response = self.login_user()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/chat")

    def test_login_with_wrong_password(self):
        self.register_user()

        response = self.login_user(password="wrongpassword")

        self.assertIn(
            b"Invalid username or password!",
            response.data
        )

    def test_chat_requires_login(self):
        response = self.client.get("/chat")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")

    def test_send_and_retrieve_message(self):
        self.register_user()
        self.login_user()

        response = self.client.post(
            "/send_message",
            data={"message": "Hello from automated testing!"}
        )

        self.assertEqual(response.status_code, 302)

        response = self.client.get("/get_messages")

        self.assertEqual(response.status_code, 200)

        messages = response.get_json()

        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0]["message"],
            "Hello from automated testing!"
        )
        self.assertEqual(
            messages[0]["username"],
            "testuser"
        )

    def test_logout(self):
        self.register_user()
        self.login_user()

        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)

        response = self.client.get("/chat")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")


if __name__ == "__main__":
    unittest.main()