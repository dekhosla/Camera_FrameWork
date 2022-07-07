__author__ = 'Devesh Khosla - github.com/dekhosla'

from re import UNICODE
import sys, serial, serial.tools.list_ports, warnings, io
import unicodedata
from PyQt5.QtCore import QSize, QRect, QObject, pyqtSignal, QThread, pyqtSignal, pyqtSlot
import time
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, \
    QListView
from PyQt5.uic import loadUi
#
import cv2
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import * 
from PyQt5.QtGui import *


import logging
import time
import numpy as np
import cv2
from PyQt5.QtGui import *
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
from PIL import ImageFont,ImageDraw,Image
import serial
import io

# Define Variable
width = 511       # 1920, 720
height = 421      # 1080, 540

display_interval = 1./300.  #
window_name = 'Camera'

# synthetic data
test_img = np.random.randint(0, 255, (height, width), 'uint8') # random image
frame = np.zeros((height,width), dtype=np.uint8) # pre allocate
   
# Setting up logging
logging.basicConfig(level=logging.DEBUG) # options are: DEBUG, INFO, ERROR, WARNING
logger = logging.getLogger("Display")

font          = cv2.FONT_HERSHEY_SIMPLEX
textLocation0 = (10,20)
textLocation1 = (10,60)
fontScale     = 1
fontColor     = (255,255,255)
lineType      = 2

# Init Frame and Thread
measured_dps = 0.0          # displayed frames per second
num_frames = 0              # frame counter
dps_measure_time = 5.0      # count frames for 5 sec
last_time = time.perf_counter()
last_display = time.perf_counter()

#Port Detection START
ports = [
    p.device
    for p in serial.tools.list_ports.comports()
    if 'USB' in p.description
]



if len(ports) > 0:
    ser = serial.Serial(ports[0],115200)  
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
    
    # warnings.warn('Connected....')


#Port Detection END

# MULTI-THREADING

class Worker(QObject):
    finished = pyqtSignal()
    intReady = pyqtSignal(str)

    @pyqtSlot()
    def __init__(self):
        super(Worker, self).__init__()
        self.working = True

    def work(self):        
        while self.working:
            sio.flush()
            line = sio.readline().decode('utf-8')
            #print(line)
            # time.sleep(0.00005)
            self.intReady.emit(line)

        self.finished.emit()

class qt(QMainWindow):

    def __init__(self):

        QMainWindow.__init__(self)
        loadUi('QT_Camera_UI.ui', self)
        self.ser=ser
        self.thread = None
        self.worker = None
        # self.pushButton.clicked.connect(self.start_loop)
        self.Clear_Output.clicked.connect(self.ClearOutput) 
        self.textEdit_2.selectionChanged.connect(self.on_textEdit_2_returnPressed)      
        self.UiComponents()  #setting DropDown
        self.menuBar=self.menuBar()      

    def UiComponents(self):
       
        channel_list =ports
        self.comboBoxDropDown.addItems(channel_list)   
        baudSelection = map(str, ser.BAUDRATES) 
        self.comboBoxDropDown_2.addItems(baudSelection)        
        self.comboBoxDropDown_2.setCurrentIndex(len(ser.BAUDRATES)-1) 
        self.comboBoxDropDown_2.activated.connect(self.activated)
        self.comboBoxDropDown_2.currentTextChanged.connect(self.text_changed)
        self.comboBoxDropDown_2.currentIndexChanged.connect(self.index_changed)
     
        self.start_loop()
      
    def activated(self, index):           
        print("Activated index:", index)

    def text_changed(self, s):              
        ser = serial.Serial(ports[0],s)
        sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser)) 
        print("Text changed:", s)

    def index_changed(self, index):
        self.worker.working = False
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.flushInput()
        self.ser.flushOutput()
        self.ser.close()
        print("Index changed", index)

    def on_textEdit_2_returnPressed(self):
            # self.textEdit_2.setText(self.textEdit_2.text())
            self.on_pushButton_3_clicked()
    def start_loop(self):

        self.worker = Worker()   # a new worker to perform those tasks
        self.thread = QThread()  # a new thread to run our background tasks in
        self.worker.moveToThread(self.thread)  # move the worker into the thread, do this first before connecting the signals

        self.thread.started.connect(self.worker.work) # begin our worker object's loop when the thread starts running

        self.worker.intReady.connect(self.onIntReady)

        # self.pushButton_2.clicked.connect(self.stop_loop)      # stop the loop on the stop button click

        # self.worker.finished.connect(self.loop_finished)       # do something in the gui when the worker loop ends
        self.worker.finished.connect(self.thread.quit)         # tell the thread it's time to stop running
        self.worker.finished.connect(self.worker.deleteLater)  # have worker mark itself for deletion
        self.thread.finished.connect(self.thread.deleteLater)  # have thread mark itself for deletion

        self.label_5.setText("CONNECTED!")
        self.label_5.setStyleSheet('color: green')
        x = 1
        self.textBrowser_3.setText(":")
        self.thread.start()

 

    def onIntReady(self, i):
        # self.textEdit_3.append("{}".format(i))
        self.textBrowser_3.append("{}".format(i))      
        # print(i)

  
    def ClearOutput(self):
        self.textBrowser_3.clear()


    # TXT Save
    def on_pushButton_5_clicked(self):
        with open('Sonuc.txt', 'w') as f:
            my_text = self.textBrowser_3.toPlainText()
            f.write(my_text)

    def on_pushButton_2_clicked(self):
        self.textEdit.setText('Stopped! Please click CONNECT...')



    def on_pushButton_3_clicked(self):
        # Send data from serial port:
        mytext = self.textEdit_2.toPlainText()
        # sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser))
        # print(mytext.encode())
        # ser.write(mytext.encode())     
        mytext="i"  
        sio.write(np.unicode_("i"))
        # sio.write(unicode(mytext))
        # sio.flush()
  
    
    
#
class camera(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.ThreadActive = True
        cap = cv2.VideoCapture(0)
        while self.ThreadActive:
            ret, frame = cap.read()
            if ret:
                Image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                FlippedImage = cv2.flip(Image, 1)
                ConvertToQtFormat = QImage(FlippedImage.data, FlippedImage.shape[1], FlippedImage.shape[0], QImage.Format_RGB888)
                img = ConvertToQtFormat.scaled(511, 421, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(img)
    def stop(self):
        self.ThreadActive = False
        self.quit()
#

def run():
    app = QApplication(sys.argv)
    widget = qt()
    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()