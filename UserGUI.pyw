#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Author: Pasquale Lafiosca
#   Date:   20 July 2017
#
'''
Copyright 2017 Pasquale Lafiosca

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
#general import
import os,sys,time,threading,json,string,random
from tkinter import Tk,Frame,Label,Entry,Message,Button,messagebox,Text,Menu,Scrollbar,filedialog,IntVar,font,PhotoImage,StringVar,Listbox
from tkinter import constants as c
import sqlite3 as sql #database
import face_recognition #main library
import cv2 #opencv2
import pickle
import pdb #debug library

#custom libraries
from lib.cryptoAES import cryptoAES
from lib.pwdManager import pwdManager

#CONFIG
CURPATH = os.path.dirname(os.path.realpath(__file__)) #current path
DBPATH = os.path.join(CURPATH,"server","db","user.db")
FACEPATH = os.path.join(CURPATH,"server","faces")

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

class faceCamera:
    def _putText(self,text,frame,position,scale=1,thickness=1,color=(0,0,255)): #frame is passed as reference
        a = cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,scale,thickness)[0]
        if(position == "center"):
            cv2.putText(frame,text,(int(frame.shape[1]*0.5 - a[0]/2),int(frame.shape[0]*0.5 - a[1]/2)), cv2.FONT_HERSHEY_SIMPLEX, scale, color,thickness) #text origin bottomLeft
        elif(position == "top"):
            cv2.putText(frame,text,(int(frame.shape[1]*0.5 - a[0]/2),int(a[1])), cv2.FONT_HERSHEY_SIMPLEX, scale, color,thickness)
        elif(position == "bottom"):
            cv2.putText(frame,text,(int(frame.shape[1]*0.5 - a[0]/2),int(frame.shape[0] - a[1]/2)), cv2.FONT_HERSHEY_SIMPLEX, scale, color,thickness)
    
    def shootPhoto(self,nShoot,autoRepeat=False):
        video_capture = cv2.VideoCapture(0) #get a reference to webcam #0 (the default one)
        time.sleep(2) #give the camera the time to autofocus
        photos = []
        i=0
        command=None
        while(i<nShoot):
            ret, frame = video_capture.read() #capture frame-by-frame
            
            frame = cv2.flip(frame, 1)
            
            fakeFrame = frame.copy() #copy of the frame that will be displayed
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5) #resize frame of video for faster face recognition processing
            
            self._putText(str(nShoot-i)+" photo(s) remaining",fakeFrame,"top",0.75,2)
            if not autoRepeat:
                self._putText("Press [SPACE] to shoot photo or [ESC] to quit.",fakeFrame,"bottom",0.75,2)
                
            face_locations = face_recognition.face_locations(frame)
            
            if len(face_locations) < 1:
                self._putText("No face detected!",fakeFrame,"center",1,2)
            elif len(face_locations) >1:
                self._putText("One face at time, please!",fakeFrame,"center",1,2)
            else:
                if autoRepeat or command == ord(' '):
                    photos.append(frame)
                    i+=1
            
            cv2.imshow('SecurFace - Camera', fakeFrame) #display the resulting frame
            cv2.moveWindow('SecurFace - Camera',0,0)
            command = cv2.waitKey(2) & 0xFF #get key command
            
            if command == 27: #premature exit with ESC
                break
                
        video_capture.release() #release handle to the webcam
        cv2.destroyAllWindows()
        return photos

class Gui:
    def __init__(self,root):
        global CURPATH,DBPATH,FACEPATH
        self.root = root
        self.db = Database(DBPATH) #initialize database object at the given path
        
        root.title('SecurFace - Login module')
        root.resizable(False, False)
        root.iconphoto(True,PhotoImage(file=os.path.join(CURPATH,"media","icon_user.png")))
        root.option_add("*Font", "Helvetica 12") #default font
        root.protocol("WM_DELETE_WINDOW", self.onClose)
        
        #main frame
        fmain = Frame(root)
        fmain.pack(side=c.TOP,pady=5,padx=5,fill=c.BOTH,expand=1)
        
        #first panel
        #top frame
        f1 = Frame(fmain)
        f1.pack(side=c.TOP,fill=c.BOTH,expand=1)
        Label(f1,text="= Login =",font="-weight bold",anchor=c.N).pack(side=c.TOP,padx=2,pady=10)
        
        f2 = Frame(fmain) #central frame
        f2.pack(side=c.TOP,expand=1)
        
        Label(f2,text="Username:",anchor=c.E).grid(row=0,column=0,padx=5,pady=5)
        self.username = Entry(f2)
        self.username.grid(row=0,column=1,padx=5,pady=5)
        self.username.focus()
        
        Label(f2,text="Password:",anchor=c.E).grid(row=1,column=0,padx=5,pady=5)
        self.password = Entry(f2,show="*")
        self.password.grid(row=1,column=1,padx=5,pady=5)
        
        Button(f2,text="FACE LOGIN",font="-weight bold",command=self.doLogin).grid(row=2,column=0,padx=5,pady=(15,5),columnspan=2)
        
        root.bind('<Return>', lambda e: self.doLogin())
        
        #message panel
        Frame(fmain, height=2, bd=1, relief=c.SUNKEN).pack(side=c.TOP,fill=c.X, padx=5, pady=5) #separator
        
        fmex = Frame(root) #message frame
        fmex.pack(side=c.TOP,fill=c.BOTH,expand=1)
        self.msg = StringVar()
        Message(fmex,textvariable=self.msg,justify=c.CENTER,width=600,font="-weight bold").pack(side=c.TOP,pady=(0,5),padx=5,fill=c.BOTH,expand=1)
        
        #credits
        f99 = Frame(root)
        f99.pack(side=c.BOTTOM,pady=(5,0),padx=0,fill=c.X,anchor=c.S)
        Label(f99,text="© 2017 Pasquale Lafiosca. Distributed under the terms of the Apache License 2.0.",fg='#111111',bg='#BBBBBB',font=('',9),bd=0,padx=10).pack(fill=c.X,ipady=2,ipadx=2)
        
    def mainloop(self):
        self.root.mainloop()
    
    def onClose(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
    
    def doLogin(self):
        name = self.username.get()
        pwd = self.password.get()
        user = self.db.query('SELECT id,pwd FROM users WHERE name = ? LIMIT 1',[name]).fetchone()
        if not user: #if username not found
            self.msg.set("LOGIN FAILED.\nIncorrect username or password. Try again.")
            return
        if pwdManager().check(pwd,user[1]): #if user is found check his password
            try:
                with open(os.path.join(FACEPATH,str(user[0])),'rb') as f:
                    data = f.read() #load the whole encrypted file
                crypto = cryptoAES(pwd) #initialize cypher object
                userFaceEncodings = pickle.loads(crypto.decrypt(data)) #decrypt face data and convert it to python nparray
            except:
                self.msg.set("LOGIN FAILED.\nAn unknown error occurred during user's data decryption.")
                return
            self.msg.set("Please look at your camera. Recognition in progress...") #starting face recognition
            cam = faceCamera()
            photosNew = cam.shootPhoto(1,True) #do a photo in selfshoot mode
            newEncodings = face_recognition.face_encodings(photosNew[0])[0]
            dist = min(face_recognition.face_distance(userFaceEncodings, newEncodings))
            self.root.update_idletasks()
            if dist < 0.5:
                self.msg.set("Congrats! YOU ARE IN.\nBest match is {:.2%}.".format(1-dist)) #returning the match 1-dist
                return True
            else:
                self.msg.set("LOGIN FAILED.\nYou do NOT seem to be "+str(name)+". Face not recognized. Try again.\nBest match is {:.2%}.".format(1-dist))
                return False
        else: #invalid password
            self.msg.set("LOGIN FAILED.\nIncorrect username or password. Try again.")
            return
        
    
    def center(self):
        self.root.update()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        size = tuple(int(_) for _ in self.root.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.root.geometry("+%d+%d" % (x, y))
        
    
if __name__ == "__main__":
    GUI=Gui(Tk()) #starts gui
    GUI.center() #center the gui on the screen
    GUI.mainloop()
