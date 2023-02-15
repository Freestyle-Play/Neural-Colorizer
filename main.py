# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
import socket, os, json, threading
#from PyQt5.QtGui import QIcon
from ui import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow):
    """docstring for MainWindow"""
    finished = QtCore.pyqtSignal()
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        #self.ui.btnChoiceImg.setToolTip("Что такое рендер фактор? - рендер фактор определяет разрешение, с которым отображается цветная часть изображения. Более низкое разрешение будет отображаться быстрее, а цвета также будут выглядеть более яркими. В частности, изображения более старых и низкого качества, как правило, выигрывают от снижения коэффициента визуализации. Более высокие коэффициенты визуализации часто лучше для изображений более высокого качества, но цвета могут слегка размываться.")
        self.dragPos = QtCore.QPoint()
        self.ui.close.clicked.connect(self.close)
        self.ui.roll.clicked.connect(self.minimize)
        self.ui.helpbtn.clicked.connect(self.show_info_messagebox)
        self.ui.btnChoiceImg.clicked.connect(self.choiceFile)
        self.ui.btnChoiceImg_2.clicked.connect(self.choicePath)
        self.ui.btnSend.setVisible(False)
        self.ui.btnSend.clicked.connect(self.sendFileToServer)
        self.FileName = None
        self.SavePath = ''
        self.finished.connect(self.on_finished, QtCore.Qt.QueuedConnection)
        self.cfg = None


    def minimize(self):
        self.showMinimized()

    def choicePath(self):
        self.SavePath = QFileDialog.getExistingDirectory(self, 'Выберите папку сохранения', 'C:\\') + "\\"
        print("SavePath =",self.SavePath)

    def choiceFile(self):
        self.FileName = QFileDialog.getOpenFileName(self, 'Выберите файл', 'c:\\',"Image files (*.jpg *.png)")
        print("FilePath =",self.FileName)
        #print("path =",self.FileName[0][-3:])

        if self.FileName[0][-3:] == "png" or self.FileName[0][-3:] == "jpg":
            if self.SavePath == '':
                self.SavePath = QFileDialog.getExistingDirectory(self, 'Выберите папку сохранения', 'C:\\') + "\\"
                if self.SavePath =='\\':
                    self.SavePath = ''
                print("SavePath =",self.SavePath)
            self.ui.ImageBox.setPixmap(QtGui.QPixmap(self.FileName[0]).scaled(340, 330, QtCore.Qt.KeepAspectRatio))
            self.ui.btnSend.setVisible(True)
            msg = QMessageBox()     
            msg.setIcon(QMessageBox.Information) 
            msg.setWindowTitle(" ")
            msg.setText("Изображение выбрано, теперь вы можете отправить его на обработку!")
            # declaring buttons on Message Box
            msg.setStandardButtons(QMessageBox.Ok)
            # start the app
            retval = msg.exec_()

        else:
            self.ui.ImageBox.setPixmap(QtGui.QPixmap())
            self.ui.btnSend.setVisible(False)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)   
            msg.setWindowTitle("Error:")
            msg.setText("файл должен иметь расширение .jpg или .png")
            # declaring buttons on Message Box
            msg.setStandardButtons(QMessageBox.Ok)
              
            # start the app
            retval = msg.exec_()


    def show_info_messagebox(self):
        msg = QMessageBox()     
        msg.setIcon(QMessageBox.Information) 
        msg.setWindowTitle(" ")
        msg.setText("Что такое рендер фактор? - рендер фактор определяет разрешение, с которым отображается цветная часть изображения. Более низкое разрешение будет отображаться быстрее, а цвета также будут выглядеть более яркими. В частности, изображения более старых и низкого качества, как правило, выигрывают от снижения коэффициента визуализации. Более высокие коэффициенты визуализации часто лучше для изображений более высокого качества, но цвета могут слегка размываться.\n\nArt/Photo:\n        Art - пресет предназначеный для рисунков 2д\n       Photo - пресет предназначеный для обработки фотографий")          
        # declaring buttons on Message Box
        msg.setStandardButtons(QMessageBox.Ok)
        # start the app
        retval = msg.exec_()

    def on_finished(self):
        self.ui.msg.setText(f"Обработка завершена!")

    def RecvFile(self, s, cfg):
        buffer = b''
        EndSym = b"_*<end>*_"
        while True:
            data = s.recv(1024 * 1024)

            if data == b"":
                disconnectClients(client)
                break

            raw_data = buffer + data
            if raw_data.find(EndSym) != -1: # вырезка сообщения из буфера
                endPos = raw_data.find(EndSym) + len(EndSym) # "...{}_*end*_"
                cutted = raw_data[:endPos] # вырезаем
                with open(f"{self.SavePath}colored_{cfg['name']}", "wb") as file:
                    file.write(cutted)
                print(fr"{self.SavePath}colored_{cfg['name']}")
                self.ui.ImageBox_2.setPixmap(QtGui.QPixmap(fr"{self.SavePath}colored_{cfg['name']}").scaled(340, 330, QtCore.Qt.KeepAspectRatio))
                print("Sock close")
                self.finished.emit()
                break
                
            else:
                buffer = raw_data
                
    def sendFileToServer(self):
        try:
            HOST = "127.0.0.1"  # The server's hostname or IP address
            PORT = 65432  # The port used by the server
            EndSym = "_*<end>*_"
            MesSym = "_*<mes>*_"
            ByteEndSym = b"_*<endSending>*_"    

            name = self.FileName[0].split("/")[-1]
            renderF = self.ui.comboBoxF.currentText()
            typeImg = self.ui.comboBoxType.currentText()
            if renderF == "Low🏞":
                renderF = 10
            if renderF == "Medium🌅":
                renderF = 25
            if renderF == "Hight🌄":
                renderF = 40

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            s.sendall(b'im client')
            cfg = {"path":self.FileName[0], "name":name, "size":os.path.getsize(self.FileName[0]), "render_factor":renderF, "type":typeImg}
            self.cfg = cfg
            data = s.recv(1024)
            if data != None and len(data) >= 1: print(f"Received {data}")
            else: return

            with open(cfg["path"], "rb") as f:
                data = f.read()

            msg = f"{MesSym}{json.dumps(cfg)}{EndSym}"
            print(msg)
            print("отправка данных на сервер")
            self.ui.msg.setText("отправка данных на сервер")

            s.sendall(bytes(msg, encoding='utf-8'))
            s.sendall(data + ByteEndSym)
            print("ожидание ответа...")
            self.ui.msg.setText("ожидание ответа...")
            '''
            msg = QMessageBox()     
            msg.setIcon(QMessageBox.Information) 
            msg.setWindowTitle(" ")
            msg.setText("Вы добавлены в очередь! Ожидание результата...")
            # declaring buttons on Message Box
            msg.setStandardButtons(QMessageBox.Ok)
            # start the app
            retval = msg.exec_()
            '''
            self.ui.msg.setText("Вы добавлены в очередь! Ожидание результата...")

            t1 = threading.Thread(target=self.RecvFile, args=(s, cfg))
            t1.deamon = True
            t1.start()
        except Exception as e:
            msg = QMessageBox()     
            msg.setIcon(QMessageBox.Critical) 
            msg.setWindowTitle(" ")
            msg.setText(f"{e}")          
            # declaring buttons on Message Box
            msg.setStandardButtons(QMessageBox.Ok)
            # start the app
            retval = msg.exec_()

        
    

    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()
        
    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()


app = QtWidgets.QApplication([])
application = MainWindow()
application.show()

sys.exit(app.exec())