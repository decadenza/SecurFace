# SecurFace
This is a **demonstrative-only** application using face recognition for security purpose.

Requirements:
- Python 3+ (tested on 3.4 and 3.6 only)
- OpenCV 3
- Dlib
- face_recognition (https://github.com/ageitgey/face_recognition)
- sqlite3
- other standard libraries
- a webcam

AdminGUI.pyw:
1) Insert a username and relative password
2) Start face recognition training taking 3 photos
3) You can test your face matching clicking "Test face matching"
4) Save current user into database

UserGUI.pyw:
1) Insert username and password previously created with AdminGUI.py
2) Click on "FACE LOGIN"
3) Enjoy


N.B. The "server" folder emulates a remote server that contains user data.


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
