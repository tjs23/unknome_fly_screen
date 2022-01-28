import os
import sys
import sqlite3


def createTable():
    
    cwd = os.getcwd()
    workdir = '%s\Dropbox\Unknome' %cwd
    dbpath = os.path.join(workdir, 'Databases\Unknome.db')
    
    db = sqlite3.connect(dbpath)
    cursor = db.cursor()
    
    cursor.execute('''CREATE TABLE Dataset (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, Stock_id TEXT NOT NULL, VDRC_id INT NOT NULL,

                                        Off_target INT, s19 REAL, CAN_repeats INT NOT NULL, Insertion INT NOT NULL,
                                        
                                        Status TEXT NOT NULL, TrialScreen TEXT, Gene_id INT NOT NULL, fbgn_id TEXT NOT NULL,
                                        
                                        CG_number TEXT NOT NULL, OrthoMCl_id TEXT, Yeast_id TEXT, Worm_id TEXT, Zebrafish_id TEXT,
                                        
                                        Mouse_id TEXT, Human_id TEXT, DPIM_PPI TEXT, DPiM_stocks TEXT, Viability TEXT, DMPL TEXT,
                                        
                                        Mouse_KO TEXT)''' )
                                        

    db.commit()
    db.close()
    
    return



def insertData(data):
    
    cwd = os.getcwd()
    workdir = '%s\Dropbox\Unknome' %cwd
    dbpath = os.path.join(workdir, 'Databases\Unknome.db')
    
    db = sqlite3.connect(dbpath)
    cursor = db.cursor()
    
    cursor.executemany('''INSERT INTO Dataset(Stock_id, VDRC_id, Off_target, s19, CAN_repeats, Insertion, Status, TrialScreen, Gene_id, 
                    fbgn_id, CG_number, OrthoMCl_id, Yeast_id, Worm_id, Zebrafish_id, Mouse_id, Human_id, DPIM_PPI, DPIM_stocks, Viability, DMPL) 
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', data)

    db.commit()
    db.close()
    
    return