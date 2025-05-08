from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///DB//sakila.db")

# db_dialect = db.dialect
table_names = db.get_usable_table_names()
tables_info = db.get_table_info_no_throw()

docs = tables_info.split("\n\n\n")





