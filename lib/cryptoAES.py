#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   Author: Pasquale Lafiosca
#   Date:   08 August 2017
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
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol import KDF

class cryptoAES:
    def __init__(self,pwd):
        self.pwd = pwd
        
    def encrypt(self,data):
        salt = get_random_bytes(8) #random salt to calculate the key
        key = KDF.PBKDF2(self.pwd,salt) #128bit key derivation function
        iv = get_random_bytes(16) #initialization vector of the chain blocks
        cipher = AES.new(key, AES.MODE_CFB, iv) #CFB mode does not need message padding
        return salt + iv + cipher.encrypt(data)
        
    def decrypt(self,msg):
        key = KDF.PBKDF2(self.pwd,msg[:8])
        cipher = AES.new(key, AES.MODE_CFB, msg[8:24])
        return cipher.decrypt(msg[24:])
