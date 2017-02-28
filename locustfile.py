from locust import HttpLocust, TaskSet, task

"""
This locustfile contains load test definitions for locustio.
To run these tests, install locustio on your host machine and run this command.

locust --host=http://192.168.33.15 Users AnonUsers

Alternatively, you can run it from within the virtual machine like this.
(locustio should be in requirements.txt)

locust --host=http://localhost Users AnonUsers

If you have a port conflict, use the -P flag to change the port.
"""

# Behaviors performed by anyone
class GeneralBehavior(TaskSet):
    @task(50)
    def view_index(self):
        self.client.get("/")
    
    @task(40)
    def view_search(self):
        self.client.get("/departments/")

    @task(10)
    def view_media(self):
        self.client.get("/media")

    @task(10)
    def view_faqs(self):
        self.client.get("/faq/")

    @task(5)
    def view_contact_us(self):
        self.client.get('/contact-us/')

    @task(20)
    def view_department(self):
        self.client.get("/departments/87255/los-angeles-county-fire-department")

    @task(10)
    def view_station(self):
        self.client.get("/stations/47754/los-angeles-county-fire-department-station-1")

    @task(25)
    def search_departments(self):
        self.client.get("/departments?q=Los+Angeles")

    @task(20)
    def search_department_names(self):
        self.client.get("/departments?name=Los+Angeles")

    @task(10)
    def search_department_score_region(self):
        self.client.get("/departments?favorites=false&state=CA&region=West&population=1814307+%2C+8687331&dist_model_score=35+%2C+286")

# Behaviors performed by anonymous users
class AnonBehavior(TaskSet):
    tasks = {GeneralBehavior:10}

# Behaviors performed by logged in users
class UserBehavior(TaskSet):
    tasks = {GeneralBehavior:10}
    
    # Log the user in
    @task(1)
    def on_start(self):
        response = self.client.get("/login/")
        token = response.cookies['csrfmiddlewaretoken']
        self.client.post("/login/", {
            "csrfmiddlewaretoken":token,
            "username":"admin",
            "password":"admin"
        })

class AnonUsers(HttpLocust):
    weight = 10
    task_set = AnonBehavior
    min_wait = 5000
    max_wait = 9000

class Users(HttpLocust):
    weight = 1
    task_set = AnonBehavior
    min_wait = 5000
    max_wait = 9000
