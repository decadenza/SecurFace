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

import face_recognition #main library
import cv2 #opencv2
import pickle
import pdb #debug library

#custom libraries
from lib.cryptoAES import cryptoAES
from lib.pwdManager import pwdManager
from database import Database

#CONFIG
CURPATH = os.path.dirname(os.path.realpath(__file__)) #current path
DBPATH = os.path.join(CURPATH,"server","db","user.db")
FACEPATH = os.path.join(CURPATH,"server","faces")

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
            elif len(face_locations) > 1:
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
        
        root.title('SecurFace - Admin module')
        root.resizable(False, False)
        root.iconphoto(True,PhotoImage(file=os.path.join(CURPATH,"media","icon_admin.png")))
        root.option_add("*Font", "Helvetica 12") #default font
        root.protocol("WM_DELETE_WINDOW", self.onClose)
        
        #main frame
        fmain = Frame(root)
        fmain.pack(side=c.TOP,pady=5,padx=5,fill=c.BOTH,expand=1)
        
        #first panel
        #top frame
        f1 = Frame(fmain)
        f1.pack(side=c.TOP,fill=c.BOTH,expand=1)
        Label(f1,text="= Authorize new user =",font="-weight bold",anchor=c.N).pack(side=c.TOP,padx=2,pady=10)
        
        f2 = Frame(fmain) #central frame
        f2.pack(side=c.TOP,fill=c.BOTH,expand=1)
        
        Label(f2,text="Username:",anchor=c.E).grid(row=0,column=0,padx=5,pady=5)
        self.username = Entry(f2,validate='focus',validatecommand=self._validateUser)
        self.username.grid(row=0,column=1,padx=5,pady=5)
        
        Label(f2,text="Password:",anchor=c.E).grid(row=1,column=0,padx=5,pady=5)
        self.password = Entry(f2,validate='focus',validatecommand=self._validatePwd)
        self.password.grid(row=1,column=1,padx=5,pady=5)
        Label(f2,text="Set length:",font="-size 9", anchor=c.E).grid(row=1,column=2,padx=2,pady=5,sticky=c.E)
        self.pwdLength = Entry(f2,width=3)
        self.pwdLength.insert(0,'12')
        self.pwdLength.grid(row=1,column=3,padx=5,pady=5)
        Button(f2,text="Generate",anchor=c.W,command=self.generatePwd).grid(row=1,column=4,padx=5,pady=5)
        
        self.userFaceEncodings = None #var that will be containing face characterization data
        Button(f2,text="Start face recognition TRAINING",command=self.doTraining).grid(row=2,column=0,padx=5,pady=(15,5),columnspan=2,sticky=c.W)
        
        Button(f2,text="Test face matching",command=self.testFace).grid(row=3,column=0,padx=5,pady=5,columnspan=2,sticky=c.W)
        
        Button(f2,text="Save new user in database",command=self.saveUser).grid(row=4,column=0,padx=5,pady=5,columnspan=2,sticky=c.W)
        
        #second panel
        Frame(fmain, height=2, bd=1, relief=c.SUNKEN).pack(side=c.TOP,fill=c.X, padx=5, pady=5) #separator
        
        f4 = Frame(fmain)
        f4.pack(side=c.TOP,fill=c.BOTH,expand=1)
        Label(f4,text="= Delete existing user =",font="-weight bold",anchor=c.N).pack(side=c.TOP,padx=2,pady=10)
        
        f5 = Frame(fmain) #central frame
        f5.pack(side=c.TOP,fill=c.BOTH)
        
        Label(f5,text="Username:",anchor=c.E).grid(row=0,column=0,padx=5,pady=5)
        
        delListScroll = Scrollbar(f5)
        delListScroll.grid(row=0,column=2,padx=5,pady=5,sticky=c.N+c.S)
        self.delList = Listbox(f5,selectmode=c.SINGLE,height=5,yscrollcommand=delListScroll.set)
        self.updateUserList() #get all the usernames in database
        self.delList.grid(row=0,column=1,padx=5,pady=5)
        self.delList.select_set(0) #select first default element
        delListScroll.config(command=self.delList.yview)
        
        Button(f5,text="Delete user",anchor=c.W,command=self.delUser).grid(row=0,column=3,padx=5,pady=5)
        
        #third panel
        Frame(fmain, height=2, bd=1, relief=c.SUNKEN).pack(side=c.TOP,fill=c.X, padx=5, pady=5) #separator
        
        fmex = Frame(root) #message frame
        fmex.pack(side=c.TOP,fill=c.BOTH,expand=1)
        self.msg = StringVar()
        Message(fmex,textvariable=self.msg,width=600,font="-weight bold").pack(side=c.TOP,pady=(0,5),padx=5,fill=c.BOTH,expand=1)
        
        #credits
        f99 = Frame(root)
        f99.pack(side=c.BOTTOM,pady=(5,0),padx=0,fill=c.X,anchor=c.S)
        Label(f99,text="© 2017 Pasquale Lafiosca. Distributed under the terms of the Apache License 2.0.",fg='#111111',bg='#BBBBBB',font=('',9),bd=0,padx=10).pack(fill=c.X,ipady=2,ipadx=2)
        
    def mainloop(self):
        self.root.mainloop()
    
    def onClose(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
            
    def generatePwd(self):
        try:
            length = int(self.pwdLength.get())
        except ValueError:
            return
        if(length<8):
            self.pwdLength.config(bg='#FF5555')
            return
        self.pwdLength.config(bg='#FFFFFF')
        chars = string.ascii_letters + string.digits + '!@#$%^&*()?\/' #password dataset
        random.seed = (os.urandom(1024))
        self.password.delete(0, c.END)
        self.password.insert(0,''.join(random.choice(chars) for i in range(length)))
        self.password.config(bg='#FFFFFF')
    
    def _validatePwd(self):
        p = self.password.get()
        
        if len(p)<8 or not set(p) <= set(string.ascii_uppercase + string.ascii_lowercase + string.digits + '!.@#$%^&*()?\'"\/'):
            self.password.config(bg='#FF5555')
            self.msg.set("Password must contain at least 8 characters in the set [A-Za-z0-9!.@#$%^&'\"*()?\/[]].")
            return False   
        
        self.msg.set("")
        self.password.config(bg='#FFFFFF') #reset to white
        return True
    
    def _validateUser(self):
        u = self.username.get()
        
        if len(u)<3 or not set(u) <= set(string.ascii_uppercase + string.ascii_lowercase + string.digits):
            self.username.config(bg='#FF5555')
            self.msg.set("Username must contain at least 3 characters in the set [A-Za-z0-9].")
            return False
        
        if self.db.query('SELECT name from users WHERE name COLLATE NOCASE = ? LIMIT 1 ', (u,)).fetchone():
            self.msg.set("Username already taken. Please choose another one.")
            return False
            
        self.msg.set("")
        self.username.config(bg='#FFFFFF')
        return True
    
    def _validateFace(self):
        if not self.userFaceEncodings:
            self.msg.set("No face characterization done!")
            return False
        return True
    
    def doTraining(self):
        self.msg.set("Look in your webcam. Be sure to have acceptable light conditions and take pictures with different facial expressions for better characterization.\nPress [SPACE] to shoot the photos or [ESC] to quit.")
        worker = threading.Thread(target=self._doTrainingWorker) #doing it in separate thread
        worker.setDaemon(True)
        worker.start()
    
    def _doTrainingWorker(self):
        cam = faceCamera()
        photos = cam.shootPhoto(3,False)
        if photos:
            self.userFaceEncodings = []
            for p in photos:
                self.userFaceEncodings.append(face_recognition.face_encodings(p)[0]) #extracting encodings
            self.msg.set("Face characterization correctly acquired.")
        else:
            self.msg.set("Face characterization NOT acquired.")
        return
    
    def _resetFields(self):
        self.username.delete(0,c.END)
        self.password.delete(0,c.END)
        self.userFaceEncodings=None
        self.root.update_idletasks()
        
    def saveUser(self):
        if self._validateUser() and self._validatePwd() and self._validateFace():
            pwd = self.password.get()
            q = self.db.query('INSERT INTO users (name,pwd) VALUES (?,?)',(self.username.get(), pwdManager().hash(pwd))) #save username and hashed password in database
            if q:
                crypto = cryptoAES(pwd) #initialize cryptoAES object with user's password
                data = crypto.encrypt(pickle.dumps(self.userFaceEncodings)) #encrypt face data
                #pickle.loads(crypto.decrypt(data)) #Function to get the data back
                with open(os.path.join(FACEPATH,str(q.lastrowid)),'wb') as f:
                    f.write(data)
                self._resetFields()
                self.updateUserList()
                self.msg.set("User correctly added to database.")
                return True
            return False
        return False
    
    def delUser(self):
        u = self.delList.get(c.ACTIVE) #get selected username
        if messagebox.askokcancel("Are you sure?", "Do you really want to delete the user "+str(u)+"?"):
            uid = self.db.query('SELECT id FROM users WHERE name = ? LIMIT 1',[u]).fetchone() #get user id
            if u and uid and self.db.query('DELETE FROM users WHERE name = ? LIMIT 1',[u]).rowcount>0:
                try:
                    os.remove(os.path.join(FACEPATH,str(uid[0])))
                except:
                    print("WARNING: Face data of user id ",uid[0]," was not found! However the user was removed from the database.")
                self.updateUserList()
                self.msg.set("User correctly deleted from database.")
                return True
            self.msg.set("Error during deleting user. Operation aborted.")
            return False
        return False
    
    def updateUserList(self):
        self.delList.delete(0, c.END)
        for u in self.db.query('SELECT name FROM users'):
            self.delList.insert(c.END, u[0])
    
    def center(self):
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        size = tuple(int(_) for _ in self.root.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.root.geometry("+%d+%d" % (x, y))
    
    def testFace(self):
        #self.root.update_idletasks()
        self.msg.set("Testing... Please wait.")
        if not self._validateFace():
            self.msg.set("Face characterization NOT acquired.")
            return
        cam = faceCamera()
        photosNew = cam.shootPhoto(1,True) #do a photo in selfshoot mode
        newEncodings = face_recognition.face_encodings(photosNew[0])[0]
        print(sys.getsizeof(newEncodings)) # gives 1120 bytes
        dist = min(face_recognition.face_distance(self.userFaceEncodings, newEncodings))
        self.msg.set("Best match is {:.2%}.".format(1-dist))
    
if __name__ == "__main__":
    GUI=Gui(Tk()) #starts gui
    GUI.center() #center the gui on the screen
    GUI.mainloop()
