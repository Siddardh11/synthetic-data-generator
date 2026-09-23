from faker import Faker
import pandas as pd

fake = Faker()


def generate_customers(num_rows):
    data = []

    for i in range(num_rows):
        customer = {
            "customer_id": i + 1,
            "name": fake.name(),
            "email": fake.email(),
            "city": fake.city(),
            "age": fake.random_int(min=18, max=60)
        }

        data.append(customer)

    return pd.DataFrame(data)