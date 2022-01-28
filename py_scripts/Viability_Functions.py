import os 
import sys


class ViabilityDB:
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.workdir = '%s\Dropbox\Unknome\Screens\ViabilityScreen' %self.cwd
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        return
        
    def fetchRows(self):
        import numpy as np
        #define filepath
        filename = 'ViabilityScreen_120710JR.txt'
        filepath = os.path.join(self.workdir, filename)
        #fetch rows from file
        data = np.genfromtxt(filepath, delimiter = '\t', dtype = None)
        rows = [row.tolist() for row in data[1:,:12]]
        rows = [[val[1:-1] if '"' in val else val for val in row] for row in rows]
        return rows
                 

    def createViabilityDB(self):
        import sqlite3
        #connect to database
        dbname = 'ViabilityDB.db'
        dbpath = os.path.join(self.dbdir, dbname)
        db = sqlite3.connect(dbpath)
        cursor = db.cursor()
        #define table
        print('Creating table Viability. \n')
        colNames = ['Stock', 'Viability_1', 'Viability_2', 'Viability_3', 'Wing_1', 'Wing_2', 'Wing_3', 'Abdomen', 'Comments_1', 'Comments_2', 'Comments_3', 'Viability_Final']
        #create table
        createStatement = '''CREATE TABLE Viability (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL,
        
                                %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, 
                                
                                %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL, %s CHAR(50) NOT NULL)''' %tuple(colNames)
        cursor.execute(createStatement)
        db.commit()
        #fetch rows
        rows = self.fetchRows()
        #insert data 
        insertStatement = '''INSERT INTO Viability  (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''' %tuple(colNames)
        cursor.executemany(insertStatement, rows)
        db.commit()
        db.close()
        return
         

#ViabilityDB().createViabilityDB()