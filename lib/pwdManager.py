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
import hashlib, uuid #hashing and random generator 

class pwdManager:
    def hash(self,pwd):
        salt = uuid.uuid4().hex #generate unique 32 char salt
        pwd += salt #append it to the pwd
        hash = hashlib.sha512(pwd.encode('utf-8')).hexdigest() #generate the hash
        return hash + salt #return the hash followed by the 32 salt
    
    def check(self,pwd,hash):
        pwd += hash[128:160]
        return hash[0:128] == hashlib.sha512(pwd.encode('utf-8')).hexdigest()
