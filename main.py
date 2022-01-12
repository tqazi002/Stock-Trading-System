from tkinter import *
import sqlite3
from datetime import date
from datetime import datetime
import re
import time
import random
#from decimal import *
from tkinter import ttk
import threading

root = Tk()
root.title("Stock App")
root.geometry("620x300")
#root.grid_rowconfigure(0, weight=1)
#root.grid_columnconfigure(0, weight=1)


#create database
conn = sqlite3.connect("stock_market.db")
# create cursor
c = conn.cursor()

#create tables and link them
c.execute("""CREATE TABLE IF NOT EXISTS customer (
		customer_id text PRIMARY KEY,
		name text,
		username text,
		email text,
		cash real,
		stocks real
		)""")

c.execute("""CREATE TABLE IF NOT EXISTS company (
		ticker text PRIMARY KEY,
		name text,
		volume integer,
		initial_price real,
		curr_price real,
		market_hours text,
		market_schedule text,
		market_cap real,
		day_high real,
		day_low real
		)""")

c.execute("""CREATE TABLE IF NOT EXISTS limit_order (
		customer_id text,
		desired_price real,
		buy_sell text,
		date_expire date,
		ticker text,
		shares integer,
		FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
		)""")

#hist_id integer PRIMARY KEY autoincrement,

c.execute("""CREATE TABLE IF NOT EXISTS history (
		customer_id text,
		cash real,
		stock real,
		trans_date date,
		ticker text,
		trans_balance real,
		ticker_curr_price real,
		shares_buy_sold integer,
		FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
		)""")

c.execute("""CREATE TABLE IF NOT EXISTS stock_owner (
		customer_id text,
		ticker text,
		shares integer,
		stock_money real,
		PRIMARY KEY (ticker, customer_id),
		FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
		FOREIGN KEY (ticker) REFERENCES company (ticker)
		)""")

# Commit changes
conn.commit()
# close connection
conn.close()


# global variables
rates = [-5, -4.35, -2.67, -1, -0.50, 0.50, 1, 2.67, 4.35, 5]
#curr_rate = rates[9]
curr_rate = random.choice(rates)
buy_successful = True
sell_successful = True


def fulfillLimitOrders():
	global buy_successful
	global sell_successful
	global curr_rate
	global rates
	#fulfill any limit orders that meet requirements
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT *, oid FROM limit_order")
	records = c.fetchall()

	conn.commit()
	conn.close()

	for i in records:
		#if buy then see if current price is <= desired price and buy then delete
		if i[2] == "buy":
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()

			c.execute("SELECT curr_price FROM company WHERE ticker=?", (i[4],))
			current_price = c.fetchone()
			
			conn.commit()
			conn.close()
			if current_price[0] <= i[1]:
				buy_stock(i[0], i[4], i[5]) 
				if buy_successful == True:
					# then remove instance from limit order table and set buy successful back to true
					conn = sqlite3.connect("stock_market.db")
					c = conn.cursor()

					c.execute("DELETE FROM limit_order WHERE oid=?", (int(i[6]),))
				
					conn.commit()
					conn.close()
				else:
					buy_successful = True

		#if sell then see if current price is >= desired price and sell then delete
		elif i[2] == "sell":
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()

			c.execute("SELECT curr_price FROM company WHERE ticker=?", (i[4],))
			current_price = c.fetchone()

			conn.commit()
			conn.close()
			if current_price[0] >= i[1]:
				sell_stock(i[0], i[4], i[5])
				if sell_successful == True:
					# then remove instance from limit order table and set buy successful back to true
					conn = sqlite3.connect("stock_market.db")
					c = conn.cursor()

					c.execute("DELETE FROM limit_order WHERE oid=?", (int(i[6]),))
					
					conn.commit()
					conn.close()	
				else:
					sell_successful = True

	return

#runs in a separate thread and keeps track of time
#everyday at midnight it decides whether for prices to go up or down for the day and updates all values and fulfills any limits orders
#if any other hour, it updates according to current rate and updates all values and fulfills an limit orders
def hourly():
	#infinite loop
	while True:
		global buy_successful
		global sell_successful
		global curr_rate
		global rates
		now = datetime.now()
		current_time = now.strftime("%H:%M:%S")
		time_list = current_time.split(":")
		time.sleep(1)

		# if midnight then choose random number from list and update prices
		# delete expired limit orders checking the date
		# then check remaning limit orders and fulfill any, then delete them
		if int(time_list[0]) == 0 and int(time_list[1]) == 0 and int(time_list[2]) == 0:
			curr_rate = random.choice(rates)

			#connect to database
			conn = sqlite3.connect("stock_market.db")
			# create cursor
			c = conn.cursor()

			c.execute("SELECT * FROM company")
			records = c.fetchall()

			# Commit changes
			conn.commit()
			# close connection
			conn.close()

			record_price = 0.0
			updated_amount = 0.0
			for i in records:
				record_price = i[4]
				updated_amount = record_price + curr_rate
				updated_amount = round(float(updated_amount), 2)
				volume = i[2]
				updated_market_cap = volume * updated_amount
				updated_market_cap = round(float(updated_market_cap), 2)
				
				if updated_amount >= 0:
					#connect to database
					conn = sqlite3.connect("stock_market.db")
					# create cursor
					c = conn.cursor()

					#update curr_price, daily high, daily low and market cap
					c.execute("UPDATE company SET curr_price=?, day_high=?, day_low=?, market_cap=? WHERE ticker=?", (updated_amount, updated_amount, updated_amount, updated_market_cap, i[0],))

					# Commit changes
					conn.commit()
					# close connection
					conn.close()

			#update all stock money in stock owner table
			#connect to database
			conn = sqlite3.connect("stock_market.db")
			# create cursor
			c = conn.cursor()

			c.execute("SELECT * FROM stock_owner") # stock money = shares * current price
			records = c.fetchall()

			# Commit changes
			conn.commit()
			# close connection
			conn.close()

			for i in records:
				#connect to database
				conn = sqlite3.connect("stock_market.db")
				# create cursor
				c = conn.cursor()

				c.execute("SELECT curr_price FROM company WHERE ticker=?", (i[0],))
				get_current_price = c.fetchone()
				updated_stock_money = get_current_price[0] * i[2]
				updated_stock_money = round(float(updated_stock_money), 2)
				#c.execute("UPDATE stock_owner SET stock_money=? WHERE ticker=? AND customer_id=?", (updated_stock_money, i[0], i[1],))
				c.execute("REPLACE INTO stock_owner VALUES (:ticker, :customer_id, :shares, :stock_money)",
						{
							"ticker": i[0],
							"customer_id": i[1],
							"shares": i[2],
							"stock_money": updated_stock_money
						})

				# Commit changes
				conn.commit()
				# close connection
				conn.close()


			#update stock wallet for every customer
			#for every customer, add the stock money they have in stock_owner and then update the customer table
			#connect to database
			conn = sqlite3.connect("stock_market.db")
			# create cursor
			c = conn.cursor()

			c.execute("SELECT * FROM customer")
			all_customers = c.fetchall()

			# Commit changes
			conn.commit()
			# close connection
			conn.close()

			for i in all_customers:
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()

				#c.execute("SELECT * FROM stock_owner WHERE customer_id=?", (i[0],))
				c.execute("SELECT * FROM stock_owner")
				all_stocks_for_customer = c.fetchall()
				stockSum = 0.0
				for j in all_stocks_for_customer:
					if j[1]==i[0]:
						stockSum += j[3]

				stockSum = round(float(stockSum), 2)
				c.execute("UPDATE customer SET stocks=? WHERE customer_id=?", (stockSum, i[0],))

				conn.commit()
				conn.close()

			today = date.today()

			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()

			#delete any limit orders that expire today
			c.execute("DELETE FROM limit_order WHERE date_expire=?", (today,))
			conn.commit()
			conn.close()

			fulfillLimitOrders()

		elif int(time_list[1]) == 0 and int(time_list[2]) == 0: 
			# if any other hour not midnight, update prices, stock owner table, customer cash/stock and then fulfill any limit orders
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()

			c.execute("SELECT * FROM company")
			records = c.fetchall()

			conn.commit()
			conn.close()

			record_price = 0.0
			updated_amount = 0.0
			for i in records:
				record_price = i[4]
				updated_amount = record_price + curr_rate
				# if updated amount is > day_high, update day_high
				updated_amount = round(float(updated_amount), 2)
				updated_day_high = i[8]
				updated_day_low = i[9]
				if updated_amount > i[8]:
					updated_day_high = updated_amount
				# if updated amount is < day_low, update day_low
				if updated_amount < i[9]:
					updated_day_low = updated_amount
				volume = i[2]
				updated_market_cap = volume * updated_amount
				
				updated_market_cap = round(float(updated_market_cap), 2)
				updated_day_low = float(updated_day_low)
				updated_day_high = float(updated_day_high)
				if updated_amount >= 0:
					conn = sqlite3.connect("stock_market.db")
					c = conn.cursor()

					#update curr_price, market cap, daily high and daily low
					c.execute("UPDATE company SET curr_price=?, market_cap=?, day_high=?, day_low=? WHERE ticker=?", (updated_amount, updated_market_cap, updated_day_high, updated_day_low, i[0],))
					
					conn.commit()
					conn.close()

			#update all stock money in stock owner table
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()

			c.execute("SELECT * FROM stock_owner") # stock money = shares * current price
			records= c.fetchall()

			conn.commit()
			conn.close()

			for i in records:
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()

				c.execute("SELECT curr_price FROM company WHERE ticker=?", (i[0],))
				get_current_price = c.fetchone()
				updated_stock_money = get_current_price[0] * i[2]
				updated_stock_money = round(float(updated_stock_money), 2)
				#c.execute("UPDATE stock_owner SET stock_money=? WHERE ticker=? AND customer_id=?", (updated_stock_money, i[0], i[1],))
				c.execute("REPLACE INTO stock_owner VALUES (:ticker, :customer_id, :shares, :stock_money)",
						{
							"ticker": i[0],
							"customer_id": i[1],
							"shares": i[2],
							"stock_money": updated_stock_money
						})

				# Commit changes
				conn.commit()
				# close connection
				conn.close()


			#update stock wallet for every customer
			#for every customer, add the stock money they have in stock_owner and then update the customer table
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()

			c.execute("SELECT * FROM customer")
			all_customers = c.fetchall()

			conn.commit()
			conn.close()

			for i in all_customers:
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()

				#c.execute("SELECT * FROM stock_owner WHERE customer_id=?", (i[0],))
				c.execute("SELECT * FROM stock_owner")
				all_stocks_for_customer = c.fetchall()

				conn.commit()
				conn.close()
				stockSum = 0.0
				for j in all_stocks_for_customer:
					if j[1]==i[0]:
						stockSum += j[3]

				stockSum = round(float(stockSum), 2)
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()

				c.execute("UPDATE customer SET stocks=? WHERE customer_id=?", (stockSum, i[0],))

				conn.commit()
				conn.close()

			fulfillLimitOrders()


t = threading.Thread(target=hourly)
t.setDaemon(True)
t.start()


# adds new entry in company table
def addNewStock():
	# check if company already in database
	# check funny inputs
	if len(entry4.get()) == 0 or len(entry5.get())==0 or len(entry7.get())==0:
		myLabel = Label(root, text="No empty entries!     ").grid(row=9, column=0)
	else:
		conn = sqlite3.connect("stock_market.db")
		c = conn.cursor()

		c.execute("SELECT name FROM company WHERE ticker=?", (entry5.get(),)) 
		data = c.fetchone()
		if data is None:
			c.execute("INSERT INTO company VALUES (:ticker, :name, :volume, :initial_price, :curr_price, :market_hours, :market_schedule, :market_cap, :day_high, :day_low)",
					{
						"ticker": entry5.get(),
						"name": entry4.get(),
						"volume": 0,
						"initial_price": entry7.get(),
						"curr_price": entry7.get(),
						"market_hours": "09:00-17:00",
						"market_schedule": "2021-01-01",
						"market_cap": 0,
						"day_high": entry7.get(),
						"day_low": entry7.get()
					})
			myLabel = Label(root, text="new stock added!      ").grid(row=9, column=0)
		else:
			myLabel = Label(root, text="company already exists").grid(row=9, column=0)

		conn.commit()
		conn.close()

	# clear text boxes
	entry4.delete(0, END)
	entry5.delete(0, END)
	entry7.delete(0, END)
	return

#gives you company market hours and schedule based on ticker provided
def compDetails(ticker, frame2):
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT market_hours, market_schedule FROM company WHERE ticker=?", (ticker,))

	got_data = c.fetchone()
	print_record = ""
	print_record += "Hours: " + str(got_data[0]) + "  Schedule: " + str(got_data[1])

	query_label = Label(frame2, text=print_record)
	query_label.grid(row=1, column=0, pady=10)

	conn.commit()
	conn.close()
	return

def changeMarketHours(ticker, market_hours):
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("UPDATE company SET market_hours=? WHERE ticker=?", (market_hours, ticker,))

	conn.commit()
	conn.close()
	return

def changeMarketSchedule(ticker, market_schedule):
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("UPDATE company SET market_schedule=? WHERE ticker=?", (market_schedule, ticker,))

	conn.commit()
	conn.close()
	return

#GUI for changing market hours/schedule
def changeMarket():
	top = Toplevel()
	top.title("Changing Market Schedule/Hours")

	# add entry box to search for company ticker
	frame1 = Frame(top)
	frame1.grid(row=0, column=0)
	frame2 = Frame(top)
	frame2.grid(row=1, column=0)
	entry = Entry(frame1)
	entry.grid(row=0, column=1)
	myBtn = Button(frame1, text="Enter Ticker to get Company Details: ", command=lambda: compDetails(entry.get(), frame2))
	myBtn.grid(row=0, column=0, pady=20)
	
	
	# then display compay name, ticker, market hours and market schedule
	# add 2 entry boxes and buttons next to them:
	# [Ticker] [change market hours] (tell them which format)
	# [Ticker] [change market schedule] 
	frame3 = Frame(top)
	frame3.grid(row=2, column=0)
	myLabel4 = Label(frame3, text="Ticker: ").grid(row=3, column=0)
	entry2 = Entry(frame3)
	entry2.grid(row=3, column=1)
	myLabel5 = Label(frame3, text="Hours: ").grid(row=3, column=2)
	entry3 = Entry(frame3)
	entry3.grid(row=3, column=3)
	myBtn2 = Button(frame3, text="Change market hours", command=lambda: changeMarketHours(entry2.get(), entry3.get()))
	myBtn2.grid(row=3, column=4, pady=10)
	myLabel2 = Label(frame3, text="Enter ticker, market hours in format 09:00-17:00 (between [00:00-23:59])").grid(row=2, column=0, columnspan=5)
	# then can use first entry box to see what changes were made

	frame4 = Frame(top)
	frame4.grid(row=5, column=0, pady=10)
	myLabel6 = Label(frame4, text="Ticker: ").grid(row=5, column=0)
	entry4 = Entry(frame4)
	entry4.grid(row=5, column=1)
	myLabel7 = Label(frame4, text="Dates: ").grid(row=5, column=2)
	entry5 = Entry(frame4)
	entry5.grid(row=5, column=3)
	myBtn3 = Button(frame4, text="Change market schedule", command=lambda: changeMarketSchedule(entry4.get(), entry5.get()))
	myBtn3.grid(row=5, column=4)
	frame5 = Frame(top)
	frame5.grid(row=3, column=0)
	myLabel3 = Label(frame5, text="Enter ticker, updated market schedule (list dates where stock market will be closed in format yyyy-mm-dd,yyyy-mm-dd...)")
	myLabel3.grid(row=4, column=0, pady=10, columnspan=5)

	return

#adds a new customer to database
def addNewUser():
	# check if user already in database
	# check funny inputs

	if len(entry1.get()) == 0 or len(entry2.get())==0 or len(entry3.get())==0:
		myLabel = Label(root, text="No empty entries!     ").grid(row=9, column=0)
	else:

		#connect to database
		conn = sqlite3.connect("stock_market.db")
		# create cursor
		c = conn.cursor()

		c.execute("SELECT name FROM customer WHERE customer_id=?", (entry1.get()+entry2.get()+entry3.get(),)) 
		data = c.fetchone()
		if data is None:
			c.execute("INSERT INTO customer VALUES (:customer_id, :name, :username, :email, :cash, :stocks)",
					{
						"customer_id": entry1.get()+entry2.get()+entry3.get(),
						"name": entry1.get(),
						"username": entry2.get(),
						"email": entry3.get(),
						"cash": 0,
						"stocks": 0
					})
			myLabel = Label(root, text="new user added!       ").grid(row=9, column=0)
		else:
			myLabel = Label(root, text="user already exists   ").grid(row=9, column=0)

		# Commit changes
		conn.commit()
		# close connection
		conn.close()

	# clear text boxes
	entry1.delete(0, END)
	entry2.delete(0, END)
	entry3.delete(0, END)

	
	return

#function for buying stock, and updating history, company, customer and stock owner tables
def buy_stock(unique_id, ticker, shares):
	global buy_successful
	global sell_successful
	shares = int(shares)
	
	#check market hours and schedule
	current_date = date.today()

	now = datetime.now()
	current_time = now.strftime("%H:%M")
	current_time_list = current_time.split(":")

	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT market_hours FROM company WHERE ticker=?", (ticker,))
	hours = c.fetchone()
	market_hour_list = re.split(r':+|-+',hours[0])

	conn.commit()
	conn.close()

	flag = True
	buy_successful = True

	# assuming hours are a reasonable time
	if int(current_time_list[0]) > int(market_hour_list[0]) and int(current_time_list[0]) < int(market_hour_list[2]):
		flag = True
	elif int(current_time_list[0]) == int(market_hour_list[0]):
		# then make sure minutes is after
		if int(current_time_list[1]) >= int(market_hour_list[1]):
			flag = True
		else:
			flag = False
			buy_successful = False
	elif int(current_time_list[0]) == int(market_hour_list[2]):
		if int(current_time_list[1]) <= int(market_hour_list[3]):
			flag = True
		else:
			flag = False
			buy_successful = False
	else:
		flag = False
		buy_successful = False

	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()
	c.execute("SELECT market_schedule FROM company WHERE ticker=?", (ticker,))
	schedule = c.fetchone()
	conn.commit()
	conn.close()
	blacklisted_dates = schedule[0].split(",")

	for i in blacklisted_dates:
		if i == str(current_date):
			flag = False
			buy_successful = False

	#if flag is still true, then we can buy stock
	#update stock owner table

	if flag == True:
		#check if buying more stock or buying new stock for customer
		
		conn = sqlite3.connect("stock_market.db")
		c = conn.cursor()
		#c.execute("SELECT shares FROM stock_owner WHERE ticker=? AND customer_id=?", (ticker, unique_id,)) 
		c.execute("SELECT * FROM stock_owner")
		inner = c.fetchall()
		data = None
		for k in inner:
			if k[0]==ticker and k[1]==unique_id:
				data = int(k[2])
		
		conn.commit()
		conn.close()
		if data is None:
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()
			c.execute("SELECT curr_price FROM company WHERE ticker=?", (ticker,))
			current_price = c.fetchone()
			bought = current_price[0] * int(shares)
			bought = round(float(bought), 2)
			
			# check if customer can pay for it, only carry out buy if they can
			c.execute("SELECT cash, stocks FROM customer WHERE customer_id=?", (unique_id,))
			got_data = c.fetchone()
			conn.commit()
			conn.close()
			updated_cash = got_data[0] - bought
			updated_cash = round(float(updated_cash), 2)
			if updated_cash >= 0:
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()
				c.execute("INSERT INTO stock_owner VALUES (:ticker, :customer_id, :shares, :stock_money)",
					{
						"ticker": ticker,
						"customer_id": unique_id,
						"shares": shares,
						"stock_money": bought
					})
				conn.commit()
				conn.close()
			else:
				buy_successful = False
		else:
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()
			c.execute("SELECT curr_price FROM company WHERE ticker=?", (ticker,))
			current_price = c.fetchone()
			bought = current_price[0] * shares
			bought = round(float(bought), 2)
			# check if customer can pay for it, only carry out buy if they can
			c.execute("SELECT cash, stocks FROM customer WHERE customer_id=?", (unique_id,))
			got_data = c.fetchone()
			conn.commit()
			conn.close()
			updated_cash = got_data[0] - bought
			updated_cash = round(float(updated_cash), 2)
			if updated_cash >= 0:
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()
				#c.execute("SELECT shares, stock_money FROM stock_owner WHERE ticker=? AND customer_id=?", (ticker, unique_id,))
				c.execute("SELECT * FROM stock_owner")
				inner = c.fetchall()
				got_data = [0.0, 0.0]
				for k in inner:
					if k[0]==ticker and k[1]==unique_id:
						got_data[0]=k[2]
						got_data[1]=k[3]
				
				updated_shares = shares + got_data[0]
				updated_money = bought + got_data[1]
				updated_money = round(float(updated_money), 2)
				#c.execute("UPDATE stock_owner SET shares=?, stock_money=? WHERE ticker=? AND customer_id=?", (updated_shares, updated_money, ticker, unique_id,))
				c.execute("REPLACE INTO stock_owner VALUES (:ticker, :customer_id, :shares, :stock_money)",
					{
						"ticker": ticker,
						"customer_id": unique_id,
						"shares": updated_shares,
						"stock_money": updated_money
					})
				conn.commit()
				conn.close()
			else:
				buy_successful = False
		
		#update cash wallet/ stock wallet
		if updated_cash >= 0:
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()
			c.execute("SELECT cash, stocks FROM customer WHERE customer_id=?", (unique_id,))
			got_data = c.fetchone()
			updated_stocks = got_data[1] + bought
			updated_stocks = round(float(updated_stocks), 2)
			
			c.execute("UPDATE customer SET cash=?, stocks=? WHERE customer_id=?", (updated_cash, updated_stocks, unique_id,))
			#update history table
			c.execute("INSERT INTO history VALUES (:customer_id, :cash, :stock, :trans_date, :ticker, :trans_balance, :ticker_curr_price, :shares_buy_sold)",
				{
					"customer_id": unique_id,
					"cash": updated_cash,
					"stock": updated_stocks,
					"trans_date": current_date,
					"ticker": ticker,
					"trans_balance": bought,
					"ticker_curr_price": current_price[0],
					"shares_buy_sold": shares
				})
			#update company volume and market cap
			c.execute("SELECT volume, curr_price FROM company WHERE ticker=?", (ticker,))
			got_data = c.fetchone()
			updated_volume = got_data[0] + int(shares)
			updated_market_cap = got_data[1] * updated_volume
			updated_market_cap = round(float(updated_market_cap), 2)
			c.execute("UPDATE company SET volume=?, market_cap=? WHERE ticker=?", (updated_volume, updated_market_cap, ticker,))
			
			conn.commit()
			conn.close()
		else:
			buy_successful = False

	return

#function for selling stock, and updating history, company, customer and stock owner tables
def sell_stock(unique_id, ticker, shares):
	global buy_successful
	global sell_successful
	shares = int(shares)
	#check market hours and schedule
	#update stock owner table
	#update cash wallet/ stock wallet
	#update history table
	#update company volume and market cap

	#don't need to check how much cash we have but need to check how many shares we have
	
	#check market hours and schedule
	current_date = date.today()

	now = datetime.now()
	current_time = now.strftime("%H:%M")
	current_time_list = current_time.split(":")

	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT market_hours FROM company WHERE ticker=?", (ticker,))
	hours = c.fetchone()
	market_hour_list = re.split(r':+|-+',hours[0])

	conn.commit()
	conn.close()

	flag = True
	sell_successful = True

	# assuming hours are a reasonable time
	if int(current_time_list[0]) > int(market_hour_list[0]) and int(current_time_list[0]) < int(market_hour_list[2]):
		flag = True
	elif int(current_time_list[0]) == int(market_hour_list[0]):
		# then make sure minutes is after
		if int(current_time_list[1]) >= int(market_hour_list[1]):
			flag = True
		else:
			flag = False
			sell_successful = False
	elif int(current_time_list[0]) == int(market_hour_list[2]):
		if int(current_time_list[1]) <= int(market_hour_list[3]):
			flag = True
		else:
			flag = False
			sell_successful = False
	else:
		flag = False
		sell_successful = False

	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()
	c.execute("SELECT market_schedule FROM company WHERE ticker=?", (ticker,))
	schedule = c.fetchone()
	blacklisted_dates = schedule[0].split(",")

	conn.commit()
	conn.close()

	for i in blacklisted_dates:
		if i == str(current_date):
			flag = False
			sell_successful = False

	#if flag is still true, then we can buy stock
	#update stock owner table

	if flag == True:
		#check if stock to sell is in stock owner
		
		conn = sqlite3.connect("stock_market.db")
		c = conn.cursor()
		#c.execute("SELECT shares FROM stock_owner WHERE ticker=? AND customer_id=?", (ticker, unique_id,)) 
		c.execute("SELECT * FROM stock_owner")
		inner = c.fetchall()
		data = None
		for k in inner:
			if k[0]==ticker and k[1]==unique_id:
				data=k[2]
		
		conn.commit()
		conn.close()
		if data is None: # customer doesn't own the stock
			sell_successful = False
		else: # customer does own the stock and we need to make sure shares <= shares customer owns

			if int(shares) < data: # update stock_owner table
				
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()
				c.execute("SELECT curr_price FROM company WHERE ticker=?", (ticker,))
				current_price = c.fetchone()
				sold = current_price[0] * shares
				sold = round(float(sold), 2)
				
				#c.execute("SELECT shares, stock_money FROM stock_owner WHERE ticker=? AND customer_id=?", (ticker, unique_id,))
				c.execute("SELECT * FROM stock_owner")
				inner = c.fetchall()
				got_data = [0, 0.0]
				for k in inner:
					if k[0]==ticker and k[1]==unique_id:
						got_data[0]=k[2]
						got_data[1]=k[3]
				updated_shares = got_data[0] - shares
				updated_money = got_data[1] - sold
				updated_money = round(float(updated_money), 2)
				#c.execute("UPDATE stock_owner SET shares=?, stock_money=? WHERE ticker=? AND customer_id=?", (updated_shares, updated_money, ticker, unique_id,))
				c.execute("REPLACE INTO stock_owner VALUES (:ticker, :customer_id, :shares, :stock_money)",
					{
						"ticker": ticker,
						"customer_id": unique_id,
						"shares": updated_shares,
						"stock_money": updated_money
					})
				
				conn.commit()
				conn.close()

			elif shares == data:
				
				conn = sqlite3.connect("stock_market.db")
				c = conn.cursor()
				c.execute("SELECT curr_price FROM company WHERE ticker=?", (ticker,))
				current_price = c.fetchone()
				sold = current_price[0] * shares
				sold = round(float(sold), 2)

				#c.execute("DELETE FROM stock_owner WHERE ticker=? AND customer_id=?", (ticker, unique_id,))
				c.execute("REPLACE INTO stock_owner VALUES (:ticker, :customer_id, :shares, :stock_money)",
					{
						"ticker": ticker,
						"customer_id": unique_id,
						"shares": 0,
						"stock_money": 0
					})
				
				conn.commit()
				conn.close()
				
			else:
				sell_successful = False
		
		#update cash wallet/ stock wallet
		if sell_successful == True:
			conn = sqlite3.connect("stock_market.db")
			c = conn.cursor()
			c.execute("SELECT cash, stocks FROM customer WHERE customer_id=?", (unique_id,))
			got_data = c.fetchone()
			updated_cash = got_data[0] + sold
			updated_stocks = got_data[1] - sold 
			updated_cash = round(float(updated_cash), 2)
			updated_stocks = round(float(updated_stocks), 2)
			c.execute("UPDATE customer SET cash=?, stocks=? WHERE customer_id=?", (updated_cash, updated_stocks, unique_id,))
			#update history table
			c.execute("INSERT INTO history VALUES (:customer_id, :cash, :stock, :trans_date, :ticker, :trans_balance, :ticker_curr_price, :shares_buy_sold)",
				{
					"customer_id": unique_id,
					"cash": updated_cash,
					"stock": updated_stocks,
					"trans_date": current_date,
					"ticker": ticker,
					"trans_balance": sold,
					"ticker_curr_price": current_price[0],
					"shares_buy_sold": shares
				})
			#update company volume and market cap
			c.execute("SELECT volume, curr_price FROM company WHERE ticker=?", (ticker,))
			got_data = c.fetchone()
			updated_volume = got_data[0] - shares
			updated_market_cap = got_data[1] * updated_volume
			updated_market_cap = round(float(updated_market_cap), 2)
			c.execute("UPDATE company SET volume=?, market_cap=? WHERE ticker=?", (updated_volume, updated_market_cap, ticker,))
			
			conn.commit()
			conn.close()

	return

#adds a new limit order to the database
def set_limit_order(unique_id, desired_price, buy_sell, date_expire, ticker, shares):
	shares = int(shares)
	desired_price = float(desired_price)
	
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("INSERT INTO limit_order VALUES (:customer_id, :desired_price, :buy_sell, :date_expire, :ticker, :shares)",
			{
				"customer_id": unique_id,
				"desired_price": desired_price,
				"buy_sell": buy_sell,
				"date_expire": date_expire,
				"ticker": ticker,
				"shares": shares
			})

	conn.commit()
	conn.close()

	return

#GUI for stock buying/selling setting limit orders and seeing available stocks on the market
def allStocks(top, unique_id, my_canvas, real_canvas):

	for widget in top.winfo_children()[1:]:
		widget.destroy()

	frame0 = Frame(top)
	frame0.grid(row=1, column=0)
	aLabel = Label(frame0, text="Tickers should be entered exactly as you see them\n"\
		"Shares should be entered as positive integers\n"\
		"Dates should be entered in the format: yyyy-mm-dd\n"
		"Prices should be entered without symbols e.g.(139.32)\n"\
		"You will not be able to buy stocks if you do not have enough cash\n"
		"You will not be able to sell stocks if you do not have enough shares\n"\
		"Prices and values will update every hour on the hour. Press 'Buy/Sell Available Stocks' to get updated values").grid(row=0, column=0, pady=5)

	frame1 = Frame(top)
	frame1.grid(row=2, column=0)
	# add button and entry for buying stock
	entry1 = Entry(frame1)
	entry1.grid(row=1, column=1)
	label1 = Label(frame1, text="Ticker: ").grid(row=1, column=0)
	entry2 = Entry(frame1)
	entry2.grid(row=1, column=3)
	label2 = Label(frame1, text="# of shares: ").grid(row=1, column=2)
	btn1 = Button(frame1, text="Buy stock", command=lambda: buy_stock(unique_id, entry1.get(), entry2.get()))
	btn1.grid(row=1, column=4)

	# add button and entry for selling stock
	
	entry3 = Entry(frame1)
	entry3.grid(row=2, column=1)
	label3 = Label(frame1, text="Ticker: ").grid(row=2, column=0)
	entry4 = Entry(frame1)
	entry4.grid(row=2, column=3)
	label4 = Label(frame1, text="# of shares: ").grid(row=2, column=2)
	btn2 = Button(frame1, text="Sell stock", command=lambda: sell_stock(unique_id, entry3.get(), entry4.get()))
	btn2.grid(row=2, column=4)
	

	frame2 = Frame(top)
	frame2.grid(row=3, column=0, pady=5)
	# add button and entry for a limit order
	label5 = Label(frame2, text="Desired price: ").grid(row=3, column=0)
	entry5 = Entry(frame2)
	entry5.grid(row=3, column=1)
	label6 = Label(frame2, text="'buy' or 'sell': ").grid(row=3, column=2)
	entry6 = Entry(frame2)
	entry6.grid(row=3, column=3)
	label7 = Label(frame2, text="Date expire: ").grid(row=3, column=4)
	entry7 = Entry(frame2)
	entry7.grid(row=3, column=5)
	label8 = Label(frame2, text="Ticker: ").grid(row=3, column=6)
	entry8 = Entry(frame2)
	entry8.grid(row=3, column=7)
	label9 = Label(frame2, text="# of shares: ").grid(row=3, column=8)
	entry9 = Entry(frame2)
	entry9.grid(row=3, column=9)
	btn3 = Button(frame2, text="Set limit order", command=lambda: set_limit_order(unique_id, entry5.get(), entry6.get(), entry7.get(), entry8.get(), entry9.get()))
	btn3.grid(row=3, column=10)
	
	frame5 = Frame(top)
	frame5.grid(row=4, column=0)

	frame3 = Frame(top)
	frame3.grid(row=5, column=0)
	
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT * FROM company")
	records = c.fetchall()

	e=Label(frame3, text="Ticker", width=15)
	e.grid(row=0, column=0)
	e=Label(frame3, text="Name", width=15)
	e.grid(row=0, column=1)
	e=Label(frame3, text="Volume", width=15)
	e.grid(row=0, column=2)
	e=Label(frame3, text="Opening_Price", width=15)
	e.grid(row=0, column=3)
	e=Label(frame3, text="Price", width=15)
	e.grid(row=0, column=4)
	e=Label(frame3, text="Market_Cap", width=15)
	e.grid(row=0, column=5)
	e=Label(frame3, text="Day_High", width=15)
	e.grid(row=0, column=6)
	e=Label(frame3, text="Day_Low", width=15)
	e.grid(row=0, column=7)

	frame4 = Frame(top)
	frame4.grid(row=6, column=0)

	this_list = [1, 0, 4, 2, 7, 3, 8, 9]
	i=1
	for one in records:
		for j in this_list:
			e = Label(frame4, text=one[j], width=15)
			e.grid(row=i, column=j)
		i=i+1

	conn.commit()
	conn.close()

	my_canvas.update()
	real_canvas.configure(scrollregion=real_canvas.bbox("all"))
	return

#Withdraw cash from customer account
def withdraw(amount, unique_id):
	if len(amount) != 0:
		conn = sqlite3.connect("stock_market.db")
		c = conn.cursor()

		updated_amount = 0.0
		c.execute("SELECT cash FROM customer WHERE customer_id=?", (unique_id,))
		updated_amount = c.fetchone()
		temp = 0.0
		temp = updated_amount[0] - float(amount)
		#updated_amount -= amount
		# if updated amount is < 0 then don't do this
		if temp >= 0:
			c.execute("UPDATE customer SET cash=? WHERE customer_id=?", (temp, unique_id,))

			currentDateTime = date.today()
			c.execute("INSERT INTO history VALUES (:customer_id, :cash, :stock, :trans_date, :ticker, :trans_balance, :ticker_curr_price, :shares_buy_sold)",
					{
						"customer_id": unique_id,
						"cash": temp,
						"stock": None,
						"trans_date": currentDateTime,
						"ticker": None,
						"trans_balance": amount,
						"ticker_curr_price": None,
						"shares_buy_sold": None
					})

		conn.commit()
		conn.close()
	return

#Deposit cash to customer account
def deposit(amount, unique_id):
	if len(amount) != 0:
		conn = sqlite3.connect("stock_market.db")
		c = conn.cursor()

		updated_amount = 0.0
		c.execute("SELECT cash FROM customer WHERE customer_id=?", (unique_id,))
		updated_amount = c.fetchone()
		temp = 0.0
		temp = updated_amount[0] + float(amount)
		
		# assuming updated amount is a reasonable number (not too big)
		c.execute("UPDATE customer SET cash=? WHERE customer_id=?", (temp, unique_id,))

		currentDateTime = date.today()
		c.execute("INSERT INTO history VALUES (:customer_id, :cash, :stock, :trans_date, :ticker, :trans_balance, :ticker_curr_price, :shares_buy_sold)",
				{
					"customer_id": unique_id,
					"cash": temp,
					"stock": None,
					"trans_date": currentDateTime,
					"ticker": None,
					"trans_balance": amount,
					"ticker_curr_price": None,
					"shares_buy_sold": None
				})

		conn.commit()
		conn.close()
	return

#Returns cash in customer account when button is pressed
def cash_amount(top, unique_id):
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	frame1 = Frame(top)
	frame1.grid(row=4, column=0)
	c.execute("SELECT cash FROM customer WHERE customer_id=?", (unique_id,))
	money = c.fetchall()
	query_label = Label(frame1, text=money)
	query_label.grid(row=4, column=0)

	conn.commit()
	conn.close()
	return

#GUI for deposit/withdraw cash from customer account
def deposit_withdraw_cash(top, unique_id, my_canvas, real_canvas):
	for widget in top.winfo_children()[1:]:
		widget.destroy()

	frame0 = Frame(top)
	frame0.grid(row=1, column=0)
	aLabel = Label(frame0, text="Prices should be entered without symbols e.g.(139.32)\n"\
		"You will not be able to withdraw cash you do not have").grid(row=0, column=0, pady=5)

	frame1 = Frame(top)
	frame1.grid(row=2, column=0)
	# display entry and withdraw button
	entry1 = Entry(frame1)
	entry1.grid(row=1, column=0)
	btn1 = Button(frame1, text="Withdraw", command=lambda: withdraw(entry1.get(), unique_id))
	btn1.grid(row=1, column=1)
	# display entry and deposit button
	entry2 = Entry(frame1)
	entry2.grid(row=2, column=0)
	btn2 = Button(frame1, text="Deposit", command=lambda: deposit(entry2.get(), unique_id))
	btn2.grid(row=2, column=1)
	# display cash amount button
	btn3 = Button(frame1, text="Get cash amount", command=lambda: cash_amount(top, unique_id))
	btn3.grid(row=3, column=0)

	my_canvas.update()
	real_canvas.configure(scrollregion=real_canvas.bbox("all"))
	return

#GUI for customer transaction history
def transaction_history(top, unique_id, my_canvas, real_canvas):
	for widget in top.winfo_children()[1:]:
		widget.destroy()

	frame1=Frame(top)
	frame1.grid(row=1, column=0)
	
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT *, oid FROM history WHERE customer_id=?", (unique_id,))
	records = c.fetchall()

	e=Label(frame1, text="Cash", width=20)
	e.grid(row=0, column=0)
	e=Label(frame1, text="Stock", width=20)
	e.grid(row=0, column=1)
	e=Label(frame1, text="Date", width=20)
	e.grid(row=0, column=2)
	e=Label(frame1, text="Ticker", width=20)
	e.grid(row=0, column=3)
	e=Label(frame1, text="Transaction", width=20)
	e.grid(row=0, column=4)
	e=Label(frame1, text="Price_Bought_Sold", width=20)
	e.grid(row=0, column=5)
	e=Label(frame1, text="Shares_Bought_Sold", width=20)
	e.grid(row=0, column=6)

	frame4 = Frame(top)
	frame4.grid(row=2, column=0)

	this_list = [3, 4, 1, 2, 5, 6, 7]
	i=1
	for one in records:
		for j in this_list:
			e = Label(frame4, text=one[j], width=20)
			e.grid(row=i, column=j)
		i=i+1

	conn.commit()
	conn.close()

	my_canvas.update()
	real_canvas.configure(scrollregion=real_canvas.bbox("all"))
	return

#GUI for customer current stock ownership 
def view_current_stocks(top, unique_id, my_canvas, real_canvas):
	# on top display current stock wallet and cash wallet
	# then display table
	for widget in top.winfo_children()[1:]:
		widget.destroy()

	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	frame1=Frame(top)
	frame1.grid(row=1, column=0)
	c.execute("SELECT cash, stocks FROM customer WHERE customer_id=?", (unique_id,))
	got_data = c.fetchone()
	print_record = ""
	print_record += "cash: " + str(got_data[0]) + "  stocks: " + str(got_data[1])
	myLabel = Label(frame1, text=print_record).grid(row=1, column=0, pady=10)

	c.execute("SELECT * FROM stock_owner")
	records = c.fetchall()

	frame2 = Frame(top)
	frame2.grid(row=2, column=0)
	e=Label(frame2, text="Ticker", width=20)
	e.grid(row=0, column=0)
	e=Label(frame2, text="Shares", width=20)
	e.grid(row=0, column=1)
	e=Label(frame2, text="Stock_Money", width=20)
	e.grid(row=0, column=2)

	frame4 = Frame(top)
	frame4.grid(row=3, column=0)

	this_list = [0, 2, 3]
	i=1
	for one in records:
		if one[1]==unique_id:
			for j in this_list:
				e = Label(frame4, text=one[j], width=20)
				e.grid(row=i, column=j)
			i=i+1

	conn.commit()
	conn.close()

	my_canvas.update()
	real_canvas.configure(scrollregion=real_canvas.bbox("all"))
	return

#deletes a limit order from database for customer based on oid
def cancelOrder(oid_num):
	#deletes a limit order with oid num provided
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("DELETE FROM limit_order WHERE oid=?", (oid_num,))

	conn.commit()
	conn.close()
	return

#GUI for seeing current customer limit orders
def limit_orders(top, unique_id, my_canvas, real_canvas):
	# then display table
	for widget in top.winfo_children()[1:]:
		widget.destroy()

	frame0=Frame(top)
	frame0.grid(row=1, column=0)
	# add button and entry for cancelling an order
	aLabel = Label(frame0, text="Press 'View Curent Limit Orders' button to get updated limit orders\n"\
		"Limit orders expire as soon as the expiration date is reached\n"\
		"Shares will be bought if price <= desired price\n"\
		"Shares will be sold if price >= desired price\n"
		"Limit orders will not be fulfilled if there's not enough cash to buy or if you're trying to sell more shares than you have\n"\
		"Limit orders will not be fulfilled outside of market schedule/hours").grid(row=0, column=0)
	frame1=Frame(top)
	frame1.grid(row=2, column=0)
	myLabel = Label(frame1, text="Enter row #: ").grid(row=0, column=0)
	entry1 = Entry(frame1)
	entry1.grid(row=0, column=1)
	btn1 = Button(frame1, text="Cancel Order", command=lambda: cancelOrder(entry1.get())).grid(row=0, column=2, pady=10)

	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT *, oid FROM limit_order WHERE customer_id=?", (unique_id,))
	records = c.fetchall()

	frame2 = Frame(top)
	frame2.grid(row=3, column=0)
	e=Label(frame2, text="Desired Price", width=20)
	e.grid(row=0, column=0)
	e=Label(frame2, text="Buy or Sell", width=20)
	e.grid(row=0, column=1)
	e=Label(frame2, text="Date Expire", width=20)
	e.grid(row=0, column=2)
	e=Label(frame2, text="Ticker", width=20)
	e.grid(row=0, column=3)
	e=Label(frame2, text="# of Shares", width=20)
	e.grid(row=0, column=4)
	e=Label(frame2, text="Row #", width=20)
	e.grid(row=0, column=5)

	frame4 = Frame(top)
	frame4.grid(row=4, column=0)

	this_list = [4, 3, 2, 1, 5, 6]
	i=1
	for one in records:
		for j in this_list:
			e = Label(frame4, text=one[j], width=20)
			e.grid(row=i, column=j)
		i=i+1

	conn.commit()
	conn.close()

	my_canvas.update()
	real_canvas.configure(scrollregion=real_canvas.bbox("all"))
	return

#GUI for customer dashboard
def UserDashboard():
	top = Toplevel(root)
	top.title("User Dashboard")
	top.geometry("1177x500")

	#creating a scrollbar
	main_frame = Frame(top)
	main_frame.pack(fill=BOTH, expand=1)

	my_canvas = Canvas(main_frame)
	my_canvas.pack(side=LEFT, fill=BOTH, expand=1)

	my_scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=my_canvas.yview)
	my_scrollbar.pack(side=RIGHT, fill=Y)

	my_canvas.configure(yscrollcommand=my_scrollbar.set)
	my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))

	second_frame = Frame(my_canvas)

	my_canvas.create_window((0,0), window=second_frame, anchor="nw")



	unique_id = entry1.get()+entry2.get()+entry3.get()

	#if unique id doesn't exist, don't log them in
	conn = sqlite3.connect("stock_market.db")
	c = conn.cursor()

	c.execute("SELECT name FROM customer WHERE customer_id=?", (unique_id,))
	data = c.fetchone()

	conn.commit()
	conn.close()


	if data != None:

		frame1 = Frame(second_frame)
		frame1.grid(row=0, column=0, sticky="nsew", padx=150)

		query_allStocks = Button(frame1, text="Buy/Sell Available Stocks", command=lambda: allStocks(second_frame, unique_id, top, my_canvas))
		query_allStocks.grid(row=0, column=0)

		dep_wit_cash = Button(frame1, text="Deposit/Withdraw Cash", command=lambda: deposit_withdraw_cash(second_frame, unique_id, top, my_canvas))
		dep_wit_cash.grid(row=0, column=1)

		trans_hist = Button(frame1, text="Transaction History", command=lambda: transaction_history(second_frame, unique_id, top, my_canvas))
		trans_hist.grid(row=0, column=2)

		view_curr = Button(frame1, text="View Current Stocks/Cash", command=lambda: view_current_stocks(second_frame, unique_id, top, my_canvas))
		view_curr.grid(row=0, column=3)

		lim_order = Button(frame1, text="View Current Limit Orders", command=lambda: limit_orders(second_frame, unique_id, top, my_canvas))
		lim_order.grid(row=0, column=4)
	else:
		myLabel1 = Label(second_frame, text="User does not exist").grid(row=1, column=1, columnspan=6)

	return

#GUI for main screen of application
frame1 = Frame(root)
frame1.grid(row=0, column=0)
aLabel = Label(frame1, text="All inputs should be entered without trailing spaces\n"\
	"Prices should be entered without symbols e.g.(139.32)\nCustomers login with the same information they used to create their account\n"\
	"New stocks will be created with default 09:00-17:00 market hours and 2021-01-01 market schedule\n"\
	"The application will close if you close this window").grid(row=0, column=0)
myLabel1 = Label(frame1, text="Admin").grid(row=1, column=0, pady=10)

frame2 = Frame(root)
frame2.grid(row=1, column=0)
# create text boxes for adding new stock
myLabel6 = Label(frame2, text="Company Name: ").grid(row=1, column=0)
entry4 = Entry(frame2)
entry4.grid(row=1, column=1)
myLabel7 = Label(frame2, text="Ticker: ").grid(row=1, column=2)
entry5 = Entry(frame2)
entry5.grid(row=1, column=3)
myLabel9 = Label(frame2, text="Initial price: ").grid(row=1, column=4)
entry7 = Entry(frame2)
entry7.grid(row=1, column=5)

frame3 = Frame(root)
frame3.grid(row=2, column=0)
myButton1 = Button(frame3, text="Create new stock", command=addNewStock).grid(row=2, column=0)
myButton2 = Button(frame3, text="Change market hours/schedule", command=changeMarket).grid(row=3, column=0)


# create text boxes for adding new customer
frame4 = Frame(root)
frame4.grid(row=3, column=0)
myLabel2 = Label(frame4, text="Customer").grid(row=5, column=0, pady=10)

frame5 = Frame(root)
frame5.grid(row=4, column=0)
myLabel3 = Label(frame5, text="Full name: ").grid(row=6, column=0)
entry1 = Entry(frame5)
entry1.grid(row=6, column=1)
myLabel4 = Label(frame5, text="Username: ").grid(row=6, column=2)
entry2 = Entry(frame5)
entry2.grid(row=6, column=3)
myLabel5 = Label(frame5, text="Email: ").grid(row=6, column=4)
entry3 = Entry(frame5)
entry3.grid(row=6, column=5)

frame6 = Frame(root)
frame6.grid(row=5, column=0)
myButton3 = Button(frame6, text="Create new account", command=addNewUser).grid(row=7, column=0)
myButton4 = Button(frame6, text="Login existing customer", command=UserDashboard).grid(row=8, column=0)


root.mainloop()