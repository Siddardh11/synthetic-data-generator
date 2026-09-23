from generator import generate_customers

# Number of customers to generate
num_rows = 100

# Generate customer data
df = generate_customers(num_rows)

# Display generated data
print(df)

# Export to Excel
df.to_excel("customers.xlsx", index=False)

print("Excel file generated successfully!")