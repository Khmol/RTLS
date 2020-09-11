#coding: utf8
from PyQt5.QtCore import QBasicTimer
from Ui_RTLS import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import socketserver, socket
import sys, threading
import time
from config import *
from BIN_ASCII import Convert_ArrBite_to_ArrChar
from configparser import ConfigParser         # импортируем парсер ini файлов


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.dataUDP, socket = self.request
        adr, port = self.client_address
        RTLS.DataRxAppend(myapp, self.dataUDP, adr, port)

class RTLS(QtWidgets.QMainWindow):
    #инициализация окна
    # pyuic5 Ui_RTLS.ui -o Ui_RTLS.py
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        #инициализация интерфейса
        self.ui = Ui_RTLS()
        self.ui.setupUi(self)
        # инициализация переменных
        self.curServerAddress = ''
        self.pause = False
        self.positionFilename = ''
        self.file = None
        self.zoom = DEFAULT_ZOOM
        self.timerTxCounter = 0
        self.rxCounter = 0
        self.speed = []
        self.data = ''
        self.time = ''
        self.roverAddress = []
        self.dataRx = []
        self.longitude = []
        self.latitude = []
        self.mode = []
        self.longitudeMap = 0
        self.latitudeMap = 0
        self.altitude = []
        self.altitudeMSL = []
        self.accuracyPDOP = []
        self.accuracyHDOP = []
        self.accuracyVDOP = []
        self.saveLongitude = []
        self.saveLatitude = []

        self.ui.pushButton_Pause.clicked.connect(self.pbPauseHendler)        # формирование спецификации
        # читаем настройки из ini файла
        self.ReadSettings()
        self.ui.comboBox_NomRover_1.addItems(self.roverAddress)
        self.ui.comboBox_NomRover_1.setCurrentIndex(0)
        self.ui.comboBox_NomRover_2.addItems(self.roverAddress)
        if len(self.roverAddress) > 1:
            self.ui.comboBox_NomRover_2.setCurrentIndex(1)
        else:
            self.ui.comboBox_NomRover_2.setCurrentIndex(0)
            self.disableWidgets()
        for i in range(self.roverQuantity):
            self.longitude.append(0)
            self.latitude.append(0)
            self.speed.append(0)
            self.mode.append('')
            self.altitude.append(0)
            self.altitudeMSL.append(0)
            self.accuracyPDOP.append(0)
            self.accuracyHDOP.append(0)
            self.accuracyVDOP.append(0)
            self.saveLongitude.append(0)
            self.saveLatitude.append(0)
        self.UdpServerOpenHendler()
        self.UdpClientConnectHendler()

        self.startBasicTimer()
        self.mainTimer.start(DEFAULT_TIMER, self)

    # *********************************************************************
    def pbPauseHendler(self):
        if self.ui.pushButton_Pause.isChecked():
            self.pause = True
            self.ui.pushButton_Pause.setText('Запуск')
        else:
            self.pause = False
            self.ui.pushButton_Pause.setText('Пауза')

    # *********************************************************************
    def disableWidgets(self):
        self.ui.comboBox_NomRover_2.setEnabled(False)
        self.ui.lineEdit_Longitude_2.setEnabled(False)
        self.ui.lineEdit_Latitude_2.setEnabled(False)
        self.ui.lineEdit_Altitude_2.setEnabled(False)
        self.ui.lineEdit_AltitudeMSL_2.setEnabled(False)
        self.ui.lineEdit_Mode_2.setEnabled(False)
        self.ui.lineEdit_PDOP_2.setEnabled(False)
        self.ui.lineEdit_HDOP_2.setEnabled(False)
        self.ui.lineEdit_VDOP_2.setEnabled(False)
        self.ui.lineEdit_Spead_2.setEnabled(False)

    # *********************************************************************
    def startBasicTimer(self):
        #инициализация таймера приемника по RS
        self.mainTimer = QBasicTimer()
        self.mainTimer.stop()

    #*********************************************************************
    def ReadSettings(self):
        '''
        чтение настроек из ini файла
        :return:
        '''
        #читаем переменные из файла настроек при первом входе
        try:
            # определяем парсер конфигурации из ini файла
            self.config = ConfigParser()
            # читаем конфигурацию
            self.config.read(DEFAULT_SETTINGS_FILENAME)
            # Читаем нужные значения
            self.roverQuantity = int(self.config.get('main', 'rover_quantity'))
            self.positionFilename = self.config.get('main', 'position_file')
            self.udpPort = int(self.config.get('main', 'rover_udp_port'))
            self.zoom = int(self.config.get('main', 'zoom_yandex'))
            self.curServerAddress = self.config.get('main', 'rover_net_address')
            if self.zoom > 21:
                # max zoom 21 for yandex
                self.zoom = 21
            for i in range(self.roverQuantity):
                addr = self.config.get('main', 'rover_address_{}'.format(i + 1))
                self.roverAddress.append(addr)
        except :
            # add a new section and some values
            try:
                self.config.add_section('main')
                # записываем настройки в ini
                self.WriteDefaultSettings()
            except:
                # записываем настройки в ini
                self.WriteDefaultSettings()

    # *********************************************************************
    def WriteDefaultSettings(self):
        '''
        # запись текущих настороек в ini
        :return:
        '''
        # изменяем запись в файле ini
        self.config.set('main', 'rover_quantity', str(DEFAULT_ROVER_QUANTITY))
        self.roverQuantity = DEFAULT_ROVER_QUANTITY
        self.config.set('main', 'rover_udp_port', str(DEFAULT_ROVER_UDP_PORT))
        self.udpPort = DEFAULT_ROVER_UDP_PORT
        self.config.set('main', 'position_file', str(DEFAULT_POSITION_FILENAME))
        self.positionFilename = DEFAULT_POSITION_FILENAME
        self.config.set('main', 'zoom_yandex', str(DEFAULT_ZOOM))
        self.config.set('main', 'rover_net_address', self.curServerAddress)

        for i in range(DEFAULT_ROVER_QUANTITY):
            self.config.set('main', 'rover_address_{}'.format(i+1), str(DEFAULT_ROVER_ADDRESS))
            self.roverAddress.append(DEFAULT_ROVER_ADDRESS)
        # записываем изменения в файл
        with open(DEFAULT_SETTINGS_FILENAME, 'w') as configfile:
            self.config.write(configfile)

    # *********************************************************************
    def UdpServerOpenHendler(self):
        '''
        "Запуск UDP сервера"
        :return:
        '''
        try:
            try:
                if self.curServerAddress == '':
                    pcName = socket.getfqdn()
                    indexPoint = pcName.find('.')
                    if indexPoint > 0:
                        self.curServerAddress = socket.gethostbyname(pcName[0:indexPoint])
                    else:
                        self.curServerAddress = socket.gethostbyname(pcName)
            except:
                pass
            self.udpServer = ThreadedUDPServer((str(self.curServerAddress), DEFAULT_SERVER_UDP_PORT), ThreadedUDPRequestHandler)
            server_thread = threading.Thread(target = self.udpServer.serve_forever)
            server_thread.daemon = True
            server_thread.start()
        except Exception as EXP:
            out_str = str(EXP)
            QMessageBox(QMessageBox.Warning, 'Ошибка открытия сокета', out_str, QMessageBox.Ok).exec()
            return

    # *********************************************************************
    def UdpClientConnectHendler(self):
        try:
            self.sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # передаем данные в sockUDP
            self.sockUDP.bind(('', DEFAULT_SERVER_UDP_PORT))
            for addr in self.roverAddress:
                # передаем данные в sockUDP
                self.sockUDP.sendto(DEFAULT_TX_DATA, (addr, self.udpPort))
        except:
            out_str = "Такого порта нет. Введите корректное значение."
            QMessageBox(QMessageBox.Warning, 'Сообщение', out_str, QMessageBox.Ok).exec()
            return

    #*********************************************************************
    def checkDeltaPosition(self, indexRover):
        if self.saveLongitude[indexRover] == 0 or self.saveLatitude[indexRover] == 0:
            return True
        if self.saveLongitude[indexRover] > self.longitude[indexRover]:
            if (self.saveLongitude[indexRover] - self.longitude[indexRover]) > MIN_DELTA_LOAD_URL:
                return True
        if self.saveLongitude[indexRover] < self.longitude[indexRover]:
            if (self.longitude[indexRover] - self.saveLongitude[indexRover]) > MIN_DELTA_LOAD_URL:
                return True
        if self.saveLatitude[indexRover] > self.latitude[indexRover]:
            if (self.saveLatitude[indexRover] - self.latitude[indexRover]) > MIN_DELTA_LOAD_URL:
                return True
        if self.saveLatitude[indexRover] < self.latitude[indexRover]:
            if (self.latitude[indexRover] - self.saveLatitude[indexRover]) > MIN_DELTA_LOAD_URL:
                return True
        return False

    #*********************************************************************
    def ShowPositions(self, file):
        writeAnable = self.ui.checkBox_writeToFile.isChecked()
        indexRover1 = self.ui.comboBox_NomRover_1.currentIndex()
        indexRover2 = self.ui.comboBox_NomRover_2.currentIndex()
        if writeAnable:
            file.write('address: ' + self.ui.comboBox_NomRover_1.currentText() + '\n')
            file.write('data: {} time: {}\n'.format(self.data, self.time))
        text = str(self.longitude[indexRover1])[:10]
        if writeAnable:
            file.write('    longitude_1: {:>14}\n'.format(text))
        self.ui.lineEdit_Longitude_1.setText(text)
        text = str(self.latitude[indexRover1])[:10]
        if writeAnable:
            file.write('    latitude_1: {:>15}\n'.format(text))
        self.ui.lineEdit_Latitude_1.setText(text)
        text = str(self.speed[indexRover1])[:10]
        self.ui.lineEdit_Spead_1.setText(text)
        if writeAnable:
            file.write('    speed_1: {:>18}\n'.format(text))
        text = str(self.altitude[indexRover1])[:5]
        self.ui.lineEdit_Altitude_1.setText(text)
        if writeAnable:
            file.write('    altitude_1: {:>9}\n'.format(text))
        text = str(self.altitudeMSL[indexRover1])[:5]
        self.ui.lineEdit_AltitudeMSL_1.setText(text)
        if writeAnable:
            file.write('    altitudeMSL_1: {:>5}\n'.format(text))
        text = str(self.accuracyPDOP[indexRover1])[:10]
        self.ui.lineEdit_PDOP_1.setText(text)
        if writeAnable:
            file.write('    accuracyPDOP_1: {:>5}\n'.format(text))
        text = str(self.accuracyHDOP[indexRover1])[:10]
        self.ui.lineEdit_HDOP_1.setText(text)
        if writeAnable:
            file.write('    accuracyHDOP_1: {:>5}\n'.format(text))
        text = str(self.accuracyVDOP[indexRover1])[:10]
        self.ui.lineEdit_VDOP_1.setText(text)
        if writeAnable:
            file.write('    accuracyVDOP_1: {:>5}\n'.format(text))
        text = str(self.mode[indexRover1])
        self.ui.lineEdit_Mode_1.setText(text)
        if writeAnable:
            file.write('    mode_1: {:>17}\n'.format(text))
        if self.roverQuantity == 1:
            if self.checkDeltaPosition(indexRover1):
                self.saveLongitude[indexRover1] = self.longitude[indexRover1]
                self.saveLatitude[indexRover1] = self.latitude[indexRover1]
                url = "http://static-maps.yandex.ru/1.x/?ll={},{}&size=650,450&z={}&l=sat,skl&pt={},{},pmdom1".format(
                    self.longitudeMap, self.latitudeMap, self.zoom, self.saveLongitude[indexRover1], self.saveLatitude[indexRover1])
                self.ui.webView.load(QtCore.QUrl(url))
            else:
                pass
        else:
            if writeAnable:
                file.write('address: ' + self.ui.comboBox_NomRover_2.currentText() + '\n')
                file.write('data: {} time: {}\n'.format(self.data, self.time))
            text = str(self.longitude[indexRover2])[:10]
            if writeAnable:
                file.write('    longitude_2: {:>14}\n'.format(text))
            self.ui.lineEdit_Longitude_2.setText(text)
            text = str(self.latitude[indexRover2])[:10]
            if writeAnable:
                file.write('    latitude_2: {:>15}\n'.format(text))
            self.ui.lineEdit_Latitude_2.setText(text)
            text = str(self.speed[indexRover2])[:10]
            self.ui.lineEdit_Spead_2.setText(text)
            if writeAnable:
                file.write('    speed_2: {:>18}\n'.format(text))
            text = str(self.altitude[indexRover2])[:5]
            self.ui.lineEdit_Altitude_2.setText(text)
            if writeAnable:
                file.write('    altitude_2: {:>9}\n'.format(text))
            text = str(self.altitudeMSL[indexRover2])[:5]
            self.ui.lineEdit_AltitudeMSL_2.setText(text)
            if writeAnable:
                file.write('    altitudeMSL_2: {:>5}\n'.format(text))
            text = str(self.accuracyPDOP[indexRover2])[:10]
            self.ui.lineEdit_PDOP_2.setText(text)
            if writeAnable:
                file.write('    accuracyPDOP_2: {:>5}\n'.format(text))
            text = str(self.accuracyHDOP[indexRover2])[:10]
            self.ui.lineEdit_HDOP_2.setText(text)
            if writeAnable:
                file.write('    accuracyHDOP_2: {:>5}\n'.format(text))
            text = str(self.accuracyVDOP[indexRover2])[:10]
            self.ui.lineEdit_VDOP_2.setText(text)
            if writeAnable:
                file.write('    accuracyVDOP_2: {:>5}\n'.format(text))
            text = str(self.mode[indexRover2])
            self.ui.lineEdit_Mode_2.setText(text)
            if writeAnable:
                file.write('    mode_2: {:>17}\n'.format(text))
            if self.checkDeltaPosition(indexRover1) or self.checkDeltaPosition(indexRover2):
                self.saveLongitude[indexRover1] = self.longitude[indexRover1]
                self.saveLatitude[indexRover1] = self.latitude[indexRover1]
                self.saveLongitude[indexRover2] = self.longitude[indexRover2]
                self.saveLatitude[indexRover2] = self.latitude[indexRover2]
                url = "http://static-maps.yandex.ru/1.x/?ll={:.10},{:.10}&size=650,450&z={}&l=sat,skl&pt={:.10},{:.10},pmdom1~{:.10},{:.10},pmdom2".format(
                    self.longitudeMap, self.latitudeMap, self.zoom, self.saveLongitude[indexRover1], self.saveLatitude[indexRover1],
                    self.saveLongitude[indexRover2], self.saveLatitude[indexRover2])
                self.ui.webView.load(QtCore.QUrl(url))

    # *********************************************************************
    def DataRxAppend(self, data, address, port):
        '''
        добавить данные к allDataRx
        :return:
        '''
        if self.pause == False:
            self.dataRx.append([ Convert_ArrBite_to_ArrChar(data),
                            str(address), str(port)])

    #*********************************************************************
    def UpdateMapPosition(self):
        if self.latitudeMap == 0 or \
                self.latitudeMap - self.latitude[0] > DELTA_LONGITUDE_MAP or \
                self.latitude[0] - self.latitudeMap > DELTA_LONGITUDE_MAP or \
                self.latitudeMap - self.latitude[0] > DELTA_LATITUDE_MAP or \
                self.latitude[0] - self.latitudeMap > DELTA_LATITUDE_MAP:
            self.latitudeMap = self.latitude[0]
            self.longitudeMap = self.longitude[0]

    # *********************************************************************
    def GetCommand(self, parseData, command):
        positionIndex = parseData.find(command)
        nextCommandIndex = parseData.find(SEPARATOR, positionIndex + 1)
        return parseData[positionIndex: nextCommandIndex]

    #*********************************************************************
    def GetCommandList(self, command, parseAddress, parsePort, parseData, lengthCommand, typeCommand):
        commandList = command.split(',')
        if len(commandList) < lengthCommand:
            time.sleep(0.03)
            if len(self.dataRx) > 0:
                dataAdd = self.dataRx.pop(0)
                parseDataAdd, parseAddressAdd, parsePortAdd = dataAdd
                if parseAddressAdd == parseAddress and parsePortAdd == parsePort:
                    parseData = parseData + parseDataAdd
                    commandList = self.GetCommand(parseData, typeCommand).split(',')
            else:
                print('Данные отсутствуют. \ndata:{}\n command:{}\n commandList: {}'.format(str(parseData), str(command), str(commandList)))
        return commandList

    #*********************************************************************
    def ParseRxData(self):
        cntRx = len(self.dataRx)
        if cntRx > 0:
            data = self.dataRx.pop(0)
            self.rxCounter += cntRx
            self.ui.label_NomRx.setText(str(self.rxCounter))
            parseData, parseAddress, parsePort = data
            try:
                if int(parsePort) == self.udpPort:
                    for i in range(self.roverQuantity):
                        if self.roverAddress[i] == parseAddress:
                            command = self.GetCommand(parseData, POSITION)
                            if command != '':
                                commandList = self.GetCommandList(command, parseAddress, parsePort, parseData, LEN_POSITION, POSITION)
                                try:
                                    self.calculatePosition(commandList, i)
                                except:
                                    print("Ошибка расчета позиции. Принято: " + command)
                            command = self.GetCommand(parseData, ALTITUDE)
                            if command != '':
                                commandList = self.GetCommandList(command, parseAddress, parsePort, parseData, LEN_ALTITUDE, ALTITUDE)
                                try:
                                    self.calculateAltitude(commandList, i)
                                except:
                                    print("Ошибка расчета высоты. Принято: " + command)
                            command = self.GetCommand(parseData, ACCURACY)
                            if command != '':
                                commandList = self.GetCommandList(command, parseAddress, parsePort, parseData, LEN_ACCURACY, ACCURACY)
                                try:
                                    self.calculateAccuracy(commandList, i)
                                except:
                                    print("Ошибка расчета точности. Принято: " + command)
                            self.UpdateMapPosition()
                            self.file = open(self.positionFilename, 'at')
                            self.ShowPositions(self.file)
                            self.file.close()
            except Exception as EXP:
                self.file.close()
                print(EXP)

    #*********************************************************************
    def calculateAccuracy(self, comList, pos):
        self.accuracyPDOP[pos] = float(comList[PDOP_POS])
        self.accuracyHDOP[pos] = float(comList[HDOP_POS])
        self.accuracyVDOP[pos] = float(comList[VDOP_POS])

    #*********************************************************************
    def calculateAltitude(self, comList, pos):
        self.altitudeMSL[pos] = float(comList[ALTITUDE_MSL_POS])
        self.altitude[pos] = float(comList[ALTITUDE_DIF_POS]) + self.altitudeMSL[pos]

    #*********************************************************************
    def getMode(self, value):
        if value == 'N' or value == 'E':
            return 'Нет координат'
        elif value == 'D':
            return '3D'
        elif value == 'F':
            return '3D/FLOAT'
        elif value == 'R':
            return '3D/FIXED'

    #*********************************************************************
    def calculatePosition(self, comList, pos):
        self.data = comList[DATA_POS]
        self.time = comList[TIME_POS]
        deg = int(comList[LATITUDE_POS][0:2])
        min = float(comList[LATITUDE_POS][2:])
        self.latitude[pos] = deg + min / 60
        deg = int(comList[LONGITUDE_POS][0:3])
        min = float(comList[LONGITUDE_POS][3:])
        self.longitude[pos] = deg + min / 60
        self.mode[pos] = self.getMode(comList[MODE_POS])
        self.speed[pos] = float(comList[SPEED_POS]) * 1.852 # 1.852 это перевод узлов в километры в час

    #*********************************************************************
    def timerEvent(self, e):
        self.mainTimer.stop() #выключаем таймер
        if self.timerTxCounter > DEFAULT_TX_TIMER:
            self.timerTxCounter = 0
            for addr in self.roverAddress:
                # передаем данные в sockUDP
                self.sockUDP.sendto(DEFAULT_TX_DATA, (addr, self.udpPort))
        self.timerTxCounter += 1
        self.ParseRxData()
        self.mainTimer.start(DEFAULT_TIMER, self)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = RTLS()
    myapp.show()
    sys.exit(app.exec_())
