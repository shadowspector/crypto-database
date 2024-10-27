import sqlite3
from config import Config

class DatabaseService:
    @staticmethod
    def get_db():
        db = sqlite3.connect(Config.DATABASE)
        return db

    @staticmethod
    def close_db(db):
        if db:
            db.close()
    
    @staticmethod
    def execute_query(query, params=None):
        db = DatabaseService.get_db()
        cursor = db.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        db.commit()
        result = cursor.fetchall()
        DatabaseService.close_db(db)
        return result
    
    
    
