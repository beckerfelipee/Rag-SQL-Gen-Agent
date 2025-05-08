from langchain_community.utilities import SQLDatabase



db = SQLDatabase.from_uri("sqlite:///DB//sakila.db")
a = db.run("SELECT * FROM actor LIMIT 10;")



if __name__ == '__main__':
    #print(db.dialect)
    #print(db.get_usable_table_names())
    #print(db.get_table_info())
    print(a)





