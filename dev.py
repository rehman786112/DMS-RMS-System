from databasemanager import DatabaseManager

db = DatabaseManager()

data = db.get_products("SELECT * FROM products;")

headers = list(data[0].keys()) if data else []

print(headers)

product_names = db.get_any_thing("SELECT company_description from company_data where company_code = %s",16)

print(product_names)