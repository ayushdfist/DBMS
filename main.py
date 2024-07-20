import sqlite3
import datetime

class InventoryManagementSystem:
    def __init__(self, db_name='inventory.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                item_id INTEGER,
                quantity INTEGER,
                transaction_type TEXT,
                timestamp DATETIME,
                FOREIGN KEY (item_id) REFERENCES items (id)
            )
        ''')
        self.conn.commit()

    def add_item(self, name, quantity, price):
        self.cursor.execute('INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)',
                            (name, quantity, price))
        self.conn.commit()
        print(f"Added {quantity} {name}(s) to the inventory.")

    def remove_item(self, item_id, quantity):
        self.cursor.execute('SELECT quantity FROM items WHERE id = ?', (item_id,))
        current_quantity = self.cursor.fetchone()
        if current_quantity:
            current_quantity = current_quantity[0]
            if current_quantity >= quantity:
                new_quantity = current_quantity - quantity
                self.cursor.execute('UPDATE items SET quantity = ? WHERE id = ?', (new_quantity, item_id))
                self.conn.commit()
                print(f"Removed {quantity} item(s) with ID {item_id} from the inventory.")
            else:
                print(f"Error: Not enough quantity in inventory. Current quantity: {current_quantity}")
        else:
            print(f"Error: Item with ID {item_id} not found in inventory.")

    def update_item(self, item_id, name=None, quantity=None, price=None):
        update_fields = []
        values = []
        if name:
            update_fields.append('name = ?')
            values.append(name)
        if quantity is not None:
            update_fields.append('quantity = ?')
            values.append(quantity)
        if price is not None:
            update_fields.append('price = ?')
            values.append(price)
        
        if update_fields:
            query = f"UPDATE items SET {', '.join(update_fields)} WHERE id = ?"
            values.append(item_id)
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
            print(f"Updated item with ID {item_id}.")
        else:
            print("No fields to update.")

    def display_inventory(self):
        self.cursor.execute('SELECT * FROM items')
        items = self.cursor.fetchall()
        if items:
            print("\nCurrent Inventory:")
            print("ID | Name | Quantity | Price")
            print("-" * 30)
            for item in items:
                print(f"{item[0]} | {item[1]} | {item[2]} | ${item[3]:.2f}")
        else:
            print("Inventory is empty.")

    def record_transaction(self, item_id, quantity, transaction_type):
        timestamp = datetime.datetime.now()
        self.cursor.execute('''
            INSERT INTO transactions (item_id, quantity, transaction_type, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (item_id, quantity, transaction_type, timestamp))
        self.conn.commit()

    def generate_report(self):
        self.cursor.execute('''
            SELECT items.name, transactions.quantity, transactions.transaction_type, transactions.timestamp
            FROM transactions
            JOIN items ON transactions.item_id = items.id
            ORDER BY transactions.timestamp DESC
            LIMIT 10
        ''')
        transactions = self.cursor.fetchall()
        if transactions:
            print("\nRecent Transactions:")
            print("Item | Quantity | Type | Timestamp")
            print("-" * 50)
            for transaction in transactions:
                print(f"{transaction[0]} | {transaction[1]} | {transaction[2]} | {transaction[3]}")
        else:
            print("No transactions recorded.")

    def close_connection(self):
        self.conn.close()

def main():
    ims = InventoryManagementSystem()

    while True:
        print("\n--- Inventory Management System ---")
        print("1. Add Item")
        print("2. Remove Item")
        print("3. Update Item")
        print("4. Display Inventory")
        print("5. Generate Report")
        print("6. Exit")

        choice = input("Enter your choice (1-6): ")

        if choice == '1':
            name = input("Enter item name: ")
            quantity = int(input("Enter quantity: "))
            price = float(input("Enter price: "))
            ims.add_item(name, quantity, price)
            ims.record_transaction(ims.cursor.lastrowid, quantity, "ADD")

        elif choice == '2':
            item_id = int(input("Enter item ID: "))
            quantity = int(input("Enter quantity to remove: "))
            ims.remove_item(item_id, quantity)
            ims.record_transaction(item_id, quantity, "REMOVE")

        elif choice == '3':
            item_id = int(input("Enter item ID: "))
            name = input("Enter new name (press enter to skip): ")
            quantity = input("Enter new quantity (press enter to skip): ")
            price = input("Enter new price (press enter to skip): ")
            ims.update_item(item_id, 
                            name if name else None, 
                            int(quantity) if quantity else None, 
                            float(price) if price else None)

        elif choice == '4':
            ims.display_inventory()

        elif choice == '5':
            ims.generate_report()

        elif choice == '6':
            print("Exiting the system. Goodbye!")
            ims.close_connection()
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()