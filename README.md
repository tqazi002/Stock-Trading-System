# Stock-Trading-System
## A stock trading platform built with Python's tkinter and SQLite3, for GUI and relational database.

Demo: https://drive.google.com/file/d/1MDg8PCx9ILkMzOPRMUWlsUPT5BHseI2j/view

HOW TO RUN:
- if you have python it should run on any machine/OS (Linux, Windows, Mac). 
 Just compile and run the program like how you would any other python program from your terminal: "python main.py"
- I'm using Ubuntu WSL so I need a server for the GUI. I'm using Xming


IMPORTANT NOTES AND ASSUMPTIONS:
- using tkinter for GUI 
- using SQLite for our relational database --> it supports multiple users concurrently woohoo!
- I'm using Ubuntu WSL, so I need Xming for my GUI
- All hours are in 24hr format
- assuming all entries are without trailing spaces
- assuming ticker for every company is unique
- app has to be running in the background for prices to fluctuate and fill limit orders
- assuming volume means number of shares that are owned by people at one time
- to keep things simple, users can not buy or sell parts of shares
- prices decide to either go up or down for the day (at midnight) from a few set random rates
 and then prices updated every hour, if it meets a limit order during this time, it will fulfill it
 or delete it if expired date is reached and limit order is not met
 It also updates volume, market cap, current price, day high, day low, and customer stocks every hour
- Everything runs on the honor system, trusting admins and users to input their entries in the proper format requested
 as well as trusting everyone to only log into their respective accounts to make changes


FUTURE PLANS:
- add password for both admin and user
- check inputs for any funny entries and proper format
- add market hours to be between any range
- check if emails are actual emails, etc
- make the sold/bought column in transaction history separate
- add the user's name to their dashboard
- make it so that you don't have to push buttons to get updated values/tables
- cancel order button gives you the updated table
- make it so that the application doesn't have to be running in the background for prices to fluctuate and limit orders to be filled
- add a horizontal scrollbar to changing market schedule/hours window (in case their are many dates)
- Make the GUI more exciting with better feedback for users
- Clean up the code more and get rid of redundancy


HELPFUL RESOURCES:
- https://towardsdatascience.com/designing-a-relational-database-and-creating-an-entity-relationship-diagram-89c1c19320b2 (parts 1, 2 and 3)
- https://www.geeksforgeeks.org/creat-an-alarm-clock-using-tkinter/
- https://www.youtube.com/playlist?list=PLCC34OHNcOtoC6GglhF3ncJ5rLwQrLGnV
- https://docs.python.org/3/library/tkinter.html#important-tk-concepts
- https://www.sqlitetutorial.net/
- https://docs.python.org/3/library/sqlite3.html
- other helpful resources for debugging like stack overflow, etc
