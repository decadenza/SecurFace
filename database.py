#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Author: Pasquale Lafiosca
#   Date:   20 July 2017
#
import os
import sqlite3 as sql

class Database:
    def __init__(self,p):
        if not os.path.exists(os.path.dirname(p)): #if folder does not exists
            os.makedirs(os.path.dirname(p)) #create it
        self.conn = sql.connect(p) #open connection (creates file if does not exist)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS 'users' ( \
            'id'    INTEGER PRIMARY KEY AUTOINCREMENT, \
            'name'  TEXT UNIQUE, \
            'pwd'   TEXT \
            );")
        
    def query(self,q,args=None):
        if args:
            self.cursor.execute(q,args) #execute query and return result
        else:
            self.cursor.execute(q)
        self.conn.commit() #apply changes
        return self.cursor
    
    def __del__(self):
        self.conn.close() #close database connection
