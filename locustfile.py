from locust import HttpUser, task, between

class TokoKitaUser(HttpUser):
    # Set wait_time dynamically between 1 and 3 seconds
    wait_time = between(1, 3)

    @task(8)
    def view_catalogue(self):
        self.client.get("/catalogue")

    @task(2)
    def checkout_product(self):
        self.client.post("/checkout")
