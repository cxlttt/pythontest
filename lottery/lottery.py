# -*- coding: utf-8 -*-
"""
Created on Thu May  3 16:15:17 2018

@author: cxl
"""
import random
import sqlite3

db_name = 'lottery_pool';
create_cmd = 'create table if not exists ';
table_name_lottery = 'lottery';
header_lottery = '(ID INT8 PRIMARY KEY NOT NULL,Blue_1 INT8,Blue_2 INT8,Blue_3 INT8,Blue_4 INT8,Blue_5 INT8,Red_1 INT8,Red_2 INT8)';
column_lottery = '(ID,Blue_1,Blue_2,Blue_3,Blue_4,Blue_5,Red_1,Red_2)';

def getNumList(totalcount,resultcount):
    return random.sample(range(1,totalcount),resultcount);
    
if __name__ == '__main__':
    lottery_DB = sqlite3.connect(db_name);
    lottery_CR = lottery_DB.cursor();
    insertCmd = 'insert into %s%s values(?,?,?,?,?,?,?,?)' % (table_name_lottery,column_lottery);
    try:
        lottery_CR.execute(create_cmd + table_name_lottery + header_lottery);
        lottery_CR.execute('delete from ' + table_name_lottery);
   
        for index in range(1000):
            listBlue = getNumList(32,5);
            listBlue.sort();
            listRed = getNumList(16,2);
            listRed.sort();
            insertPara = (index+1,listBlue[0],listBlue[1],listBlue[2],listBlue[3],listBlue[4],listRed[0],listRed[1]);
            lottery_CR.execute(insertCmd,insertPara);
        lottery_DB.commit();          
        lottery_CR.execute('select * from %s' % table_name_lottery);   
        values = lottery_CR.fetchall();
    except:
        print('insert error %d',index);
    finally:
        print('close db');
        lottery_CR.close();
        lottery_DB.close();
        

