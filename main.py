import sqlite3
import datetime
import hashlib

class InventoryManagementSystem:
    def __init__(self, db_name='inventory.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category_id INTEGER,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                supplier_id INTEGER,
                reorder_level INTEGER,
                last_restocked DATE,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                item_id INTEGER,
                quantity INTEGER,
                transaction_type TEXT,
                timestamp DATETIME,
                user_id INTEGER,
                reason TEXT,
                total_price REAL,
                FOREIGN KEY (item_id) REFERENCES items (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def add_category(self, name, description):
        self.cursor.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
        self.conn.commit()
        print(f"Added category: {name}")

    def add_supplier(self, name, contact_person, email, phone, address):
        self.cursor.execute('''
            INSERT INTO suppliers (name, contact_person, email, phone, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, contact_person, email, phone, address))
        self.conn.commit()
        print(f"Added supplier: {name}")

    def add_user(self, username, password, role):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                            (username, password_hash, role))
        self.conn.commit()
        print(f"Added user: {username}")

    def add_item(self, name, description, category_id, quantity, price, supplier_id, reorder_level):
        self.cursor.execute('''
            INSERT INTO items (name, description, category_id, quantity, price, supplier_id, reorder_level, last_restocked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, category_id, quantity, price, supplier_id, reorder_level, datetime.date.today()))
        self.conn.commit()
        print(f"Added {quantity} {name}(s) to the inventory.")

    def remove_item(self, item_id, quantity, user_id, reason):
        self.cursor.execute('SELECT quantity, price FROM items WHERE id = ?', (item_id,))
        result = self.cursor.fetchone()
        if result:
            current_quantity, price = result
            if current_quantity >= quantity:
                new_quantity = current_quantity - quantity
                self.cursor.execute('UPDATE items SET quantity = ? WHERE id = ?', (new_quantity, item_id))
                self.conn.commit()
                total_price = quantity * price
                self.record_transaction(item_id, quantity, "REMOVE", user_id, reason, total_price)
                print(f"Removed {quantity} item(s) with ID {item_id} from the inventory.")
            else:
                print(f"Error: Not enough quantity in inventory. Current quantity: {current_quantity}")
        else:
            print(f"Error: Item with ID {item_id} not found in inventory.")

    def update_item(self, item_id, name=None, description=None, category_id=None, quantity=None, price=None, supplier_id=None, reorder_level=None):
        update_fields = []
        values = []
        for field, value in [('name', name), ('description', description), ('category_id', category_id),
                             ('quantity', quantity), ('price', price), ('supplier_id', supplier_id),
                             ('reorder_level', reorder_level)]:
            if value is not None:
                update_fields.append(f'{field} = ?')
                values.append(value)
        
        if update_fields:
            query = f"UPDATE items SET {', '.join(update_fields)} WHERE id = ?"
            values.append(item_id)
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
            print(f"Updated item with ID {item_id}.")
        else:
            print("No fields to update.")

    def display_inventory(self):
        self.cursor.execute('''
            SELECT items.*, categories.name, suppliers.name 
            FROM items 
            LEFT JOIN categories ON items.category_id = categories.id
            LEFT JOIN suppliers ON items.supplier_id = suppliers.id
        ''')
        items = self.cursor.fetchall()
        if items:
            print("\nCurrent Inventory:")
            print("ID | Name | Description | Category | Quantity | Price | Supplier | Reorder Level | Last Restocked")
            print("-" * 100)
            for item in items:
                print(f"{item[0]} | {item[1]} | {item[2][:20]}... | {item[10]} | {item[4]} | ${item[5]:.2f} | {item[11]} | {item[7]} | {item[8]}")
        else:
            print("Inventory is empty.")

    def record_transaction(self, item_id, quantity, transaction_type, user_id, reason, total_price):
        timestamp = datetime.datetime.now()
        self.cursor.execute('''
            INSERT INTO transactions (item_id, quantity, transaction_type, timestamp, user_id, reason, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (item_id, quantity, transaction_type, timestamp, user_id, reason, total_price))
        self.conn.commit()

    def generate_report(self):
        self.cursor.execute('''
            SELECT items.name, transactions.quantity, transactions.transaction_type, 
                   transactions.timestamp, users.username, transactions.reason, transactions.total_price
            FROM transactions
            JOIN items ON transactions.item_id = items.id
            JOIN users ON transactions.user_id = users.id
            ORDER BY transactions.timestamp DESC
            LIMIT 10
        ''')
        transactions = self.cursor.fetchall()
        if transactions:
            print("\nRecent Transactions:")
            print("Item | Quantity | Type | Timestamp | User | Reason | Total Price")
            print("-" * 80)
            for transaction in transactions:
                print(f"{transaction[0]} | {transaction[1]} | {transaction[2]} | {transaction[3]} | {transaction[4]} | {transaction[5]} | ${transaction[6]:.2f}")
        else:
            print("No transactions recorded.")

    def check_low_stock(self):
        self.cursor.execute('SELECT id, name, quantity, reorder_level FROM items WHERE quantity <= reorder_level')
        low_stock_items = self.cursor.fetchall()
        if low_stock_items:
            print("\nLow Stock Alert:")
            print("ID | Name | Current Quantity | Reorder Level")
            print("-" * 50)
            for item in low_stock_items:
                print(f"{item[0]} | {item[1]} | {item[2]} | {item[3]}")
        else:
            print("No items are low in stock.")

    def close_connection(self):
        self.conn.close()

def main():
    ims = InventoryManagementSystem()

    # Example usage
    ims.add_category("Electronics", "Electronic devices and accessories")
    ims.add_supplier("TechCorp", "John Doe", "john@techcorp.com", "123-456-7890", "123 Tech St, City")
    ims.add_user("admin", "password123", "admin")

    while True:
        print("\n--- Inventory Management System ---")
        print("1. Add Item")
        print("2. Remove Item")
        print("3. Update Item")
        print("4. Display Inventory")
        print("5. Generate Report")
        print("6. Check Low Stock")
        print("7. Exit")

        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            name = input("Enter item name: ")
            description = input("Enter item description: ")
            category_id = int(input("Enter category ID: "))
            quantity = int(input("Enter quantity: "))
            price = float(input("Enter price: "))
            supplier_id = int(input("Enter supplier ID: "))
            reorder_level = int(input("Enter reorder level: "))
            ims.add_item(name, description, category_id, quantity, price, supplier_id, reorder_level)
            ims.record_transaction(ims.cursor.lastrowid, quantity, "ADD", 1, "Initial stock", quantity * price)

        elif choice == '2':
            item_id = int(input("Enter item ID: "))
            quantity = int(input("Enter quantity to remove: "))
            user_id = int(input("Enter your user ID: "))
            reason = input("Enter reason for removal: ")
            ims.remove_item(item_id, quantity, user_id, reason)

        elif choice == '3':
            item_id = int(input("Enter item ID: "))
            name = input("Enter new name (press enter to skip): ")
            description = input("Enter new description (press enter to skip): ")
            category_id = input("Enter new category ID (press enter to skip): ")
            quantity = input("Enter new quantity (press enter to skip): ")
            price = input("Enter new price (press enter to skip): ")
            supplier_id = input("Enter new supplier ID (press enter to skip): ")
            reorder_level = input("Enter new reorder level (press enter to skip): ")
            ims.update_item(item_id, 
                            name if name else None, 
                            description if description else None,
                            int(category_id) if category_id else None,
                            int(quantity) if quantity else None, 
                            float(price) if price else None,
                            int(supplier_id) if supplier_id else None,
                            int(reorder_level) if reorder_level else None)

        elif choice == '4':
            ims.display_inventory()

        elif choice == '5':
            ims.generate_report()

        elif choice == '6':
            ims.check_low_stock()

        elif choice == '7':
            print("Exiting the system. Goodbye!")
            ims.close_connection()
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()