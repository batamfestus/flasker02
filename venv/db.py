# import pymysql
# from pymysql.err import MySQLError

# def create_database():
#     try:
#         # Establishing the connection to MySQL
#         mydb = pymysql.connect(
#             host="localhost",
#             user="root",
#             password="dspzsst1335143"
#         )

#         if mydb.open:
#             my_cursor = mydb.cursor()

#             # Creating a new database
#             my_cursor.execute("CREATE DATABASE IF NOT EXISTS Members")
#             print("Database 'Members' created successfully")

#             # Closing the cursor and connection
#             my_cursor.close()
#             mydb.close()
#             print("MySQL connection is closed")

#     except MySQLError as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     create_database()