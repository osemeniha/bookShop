import sqlite3

#Open database
conn = sqlite3.connect('database.db')

#Create table
conn.execute('''CREATE TABLE users 
		(userId INTEGER PRIMARY KEY, 
		password TEXT,
		email TEXT,
		firstName TEXT,
		lastName TEXT,
		country TEXT, 
		city TEXT,
		address TEXT,
		zipcode TEXT,
		phone TEXT
		)''')

conn.execute('''CREATE TABLE products
		(productId INTEGER PRIMARY KEY,
		name TEXT,
		price REAL,
		description TEXT,
		categoryId INTEGER,
		FOREIGN KEY(categoryId) REFERENCES categories(categoryId)
		)''')

conn.execute('''CREATE TABLE orders
		(orderId INTEGER PRIMARY KEY,
		userId INTEGER, 
		FOREIGN KEY(userId) REFERENCES users(userId)
		)''')

conn.execute('''CREATE TABLE basket
		(id INTEGER PRIMARY KEY,
		userId INTEGER,
		productId INTEGER,
		count INTEGER DEFAULT 0,
		statusId INTEGER,
		orderId INTEGER DEFAULT 0,
		FOREIGN KEY(userId) REFERENCES users(userId),
		FOREIGN KEY(productId) REFERENCES products(productId),
		FOREIGN KEY(orderId) REFERENCES orders(orderId)		
		)''')



conn.execute('''CREATE TABLE status
		(statusId INTEGER PRIMARY KEY,
		name TEXT
		)''')

conn.execute('''CREATE TABLE categories
		(categoryId INTEGER PRIMARY KEY,
		name TEXT
		)''')

conn.execute('''CREATE TABLE comments
        (body TEXT,
        userId TEXT,
        productId INTEGER,
        FOREIGN KEY(userId) REFERENCES users(userId),
        FOREIGN KEY(productId) REFERENCES products(productId)
        )''')

conn.close()

# conn.execute('''CREATE TABLE orders
# 		(userId INTEGER,
# 		productId INTEGER,
# 		FOREIGN KEY(userId) REFERENCES users(userId),
# 		FOREIGN KEY(productId) REFERENCES products(productId)
# 		)''')