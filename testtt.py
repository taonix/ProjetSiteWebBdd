from sqlite3 import *

con = connect("./database/database", check_same_thread=False)
cur = con.cursor()

query = 'INSERT INTO completed_forms (id_user, id_form) VALUES (?, ?)'