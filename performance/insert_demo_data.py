import xmlrpc.client

# Odoo connection parameters
url = 'http://localhost:8069'  # Replace with your Odoo URL
db = 'odoo'             # Replace with your database name
username = '+12345678629'       # Replace with your Odoo username
password = 'StrongPassword!2'       # Replace with your Odoo password

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Function to create a customer
def create_customer(name):
    customer_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{
        'name': name,
        # 'customer': True,  # Set customer to True to indicate this is a customer
        'email': f'{name.lower().replace(" ", "_")}@example.com',
    }])
    return customer_id

# Function to create a sale order
def create_sale_order(customer_id, order_lines):
    sale_order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [{
        'partner_id': customer_id,
        'order_line': order_lines,
    }])
    return sale_order_id

# Prepare demo data
customer_name = 'Demo Customer'
customer_id = create_customer(customer_name)

# Prepare order lines
order_lines = [
    (0, 0, {'product_id': 10, 'product_uom_qty': 2}),  # Replace product_id with actual product IDs
    (0, 0, {'product_id': 20, 'product_uom_qty': 1}),
]

# Create sale order
sale_order_id = create_sale_order(customer_id, order_lines)

# Output the created IDs
print(f'Created Customer ID: {customer_id}')
print(f'Created Sale Order ID: {sale_order_id}')
