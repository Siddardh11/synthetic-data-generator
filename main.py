from faker import Faker
import pandas as pd

fake = Faker()

data = []

for i in range(10):
    customer = {
        "customer_id": i + 1,
        "name": fake.name(),
        "email": fake.email(),
        "city": fake.city(),
        "age": fake.random_int(min=18, max=60)
    }

    data.append(customer)

df = pd.DataFrame(data)
df.to_excel("customers.xlsx", index=False)

print(df)