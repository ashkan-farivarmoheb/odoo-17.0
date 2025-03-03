# locustfile.py

import os
import json
from locust import HttpUser, task, between
from config import BASE_URL, DB_HOST, HEADERS
from csv import DictReader


class OdooLoadTest(HttpUser):
    wait_time = between(1, 3)  # Simulate user think time

    def on_start(self):
        """ Authenticate and get a valid session """
        self.login()

    def login(self):
        file_path = os.path.join(os.path.dirname(__file__), "data/login_users.csv")
        with open(file_path, mode="r") as file:
          users = list(DictReader(file))

        # Use first user for this instance (can be enhanced for multiple users)
        user = users[0]
        payload = {
            "jsonrpc": "2.0",
            "params": {
                "db": DB_HOST,
                "login": user["username"],
                "password": user["password"]
            }
        }

        response = self.client.post(
            url="/web/session/authenticate",
            headers=HEADERS,
            data=json.dumps(payload)
        )

        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("result") and res_json["result"].get("session_id"):
                self.session_id = res_json["result"]["session_id"]
                self.headers = {
                    **HEADERS,
                    "X-Openerp-Session-Id": self.session_id
                }
            else:
                print("Failed to get session ID.")
        else:
            print("Login failed with status code:", response.status_code)

    # @task(2)
    # def user_login(self):
    #     payload = {
    #         "jsonrpc": "2.0",
    #         "params": {
    #             "db": DB_HOST,
    #             "login": "testuser1",
    #             "password": "pass123"
    #         }
    #     }
    #
    #     with self.client.post("/web/session/authenticate", headers=HEADERS, data=json.dumps(payload),
    #                           catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure("Login failed.")
    #
    # @task(3)
    # def create_sales_order(self):
    #     payload = {
    #         "jsonrpc": "2.0",
    #         "params": {
    #             "customer_id": 1,
    #             "order_lines": [
    #                 {"product_id": 10, "quantity": 2},
    #                 {"product_id": 20, "quantity": 1}
    #             ]
    #         }
    #     }
    #
    #     with self.client.post(
    #         "/sale_order/create",
    #         headers=self.headers,
    #         data=json.dumps(payload),
    #         catch_response=True
    #     ) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure("Failed to create sales order.")
    #
    # @task(2)
    # def browse_products(self):
    #     with self.client.get("/shop", headers=self.headers, catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure("Failed to browse products.")
    #
    # @task(2)
    # def view_product_details(self):
    #     with self.client.get("/shop/product/1", headers=self.headers, catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure("Failed to view product details.")
    #
    # @task(1)
    # def checkout(self):
    #     payload = {"product_id": 1, "quantity": 2}
    #
    #     with self.client.post(
    #         "/shop/cart/update",
    #         headers=self.headers,
    #         data=json.dumps(payload),
    #         catch_response=True
    #     ) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure("Failed to add to cart.")
    #
    #     with self.client.post("/shop/checkout", headers=self.headers, catch_response=True) as response:
    #         if response.status_code == 200:
    #             response.success()
    #         else:
    #             response.failure("Checkout failed.")

    @task(1)
    def product_search(self):
        with self.client.get(
            "/shop/search?filter=category&query=electronics",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Search failed.")


