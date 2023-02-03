from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QWidget, QApplication, \
 \
    QAction, qApp, QPushButton, QDesktopWidget, QComboBox, QProgressBar, QLineEdit, \
 \
    QSpacerItem, QVBoxLayout, QGroupBox, QRadioButton, QTableWidget, QTableWidgetItem

import os

from PyQt5 import uic

import requests

from urllib.parse import urlencode

from urllib.request import Request, urlopen

import json

import sceletons

from PyQt5.QtCore import QTimer, QDateTime

from math import ceil, floor

from datetime import datetime

import time


class Settings():
    CURRENT_LOGIN = ''

    CURRENT_PASSWORD = ''

    CURRENT_PROJECT = ''

    URL_MANO = ''

    API_TOKENS = '/admin/v1/tokens'

    API_VIM_ACCOUNTS = '/admin/v1/vim_accounts'

    API_CREATE_VNF = '/vnfpkgm/v1/vnf_packages_content'

    API_CREATE_NS = '/nsd/v1/ns_descriptors_content'

    API_CREATE_INSTANCE = '/nslcm/v1/ns_instances_content'

    API_DELETE_INSTANCE = '/nslcm/v1/ns_instances_content/'

    API_GET_VNFS = '/vnfpkgm/v1/vnf_packages_content'

    API_DELETE_VNFS = '/vnfpkgm/v1/vnf_packages_content/'

    API_GET_NSS = '/nsd/v1/ns_descriptors_content'

    API_DELETE_NSS = '/nsd/v1/ns_descriptors_content/'

    TOKEN = ''

    RAM_SIZES = ['1', '2', '3', '4']

    CPU_QNT = ['1', '2', '3', '4']

    STORAGE_SIZES = ['5', '10', '15', '20']

    OPENSTACK_IMAGES = {"Ubuntu 18.04": "ubuntu18.04", "Ubuntu 20.04": "ubuntu20.04", "CentOS 9": "centos9",
                        "Postgresql": "postgres-image"}

    OPENSTACK_NETWORKS = ["shared", "public"]

    STATUS_VNF_CREATED, STATUS_NS_CREATED, STATUS_INSTANCE_CREATED = 201, 201, 201

    STATUS_NS_DELETE = 202

    STATUS_TOKEN_CREATE = 200


class MainWidget(QWidget):

    def __init__(self):

        super().__init__()

        uic.loadUi('mainWidget.ui', self)

        self.header = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json",

                       "Authorization": "Bearer " + Settings.TOKEN}

        self.vim_list = {}

        self.vnf_list = {}

        self.ns_list = {}

        self.main_list = {}

        self.labelNameInstance.setText("Instance name: ")

        self.label_descr.setText("Description: ")

        self.label_image.setText("Service: ")

        self.label_ram.setText("RAM: ")

        self.label_cpu.setText("vCPU: ")

        self.label_storage.setText("Storage: ")

        self.label_network.setText("Network: ")

        self.label_vim.setText("Set VIM: ")

        self.tableVNFs.setColumnCount(3)

        self.tableVNFs.setRowCount(1)

        self.tableVNFs.setHorizontalHeaderLabels(["NSd", "VNFd", "Date"])

        self.pushButtonDelete.setVisible(False)

        self.radioButtonCloud.setChecked(False)

        self.textEditCloudConfig.setDisabled(True)

        self.radioButtonCloud.clicked.connect(self.radioBtn)

        self.getVims()

        self.fillCombos()

        self.comboBoxVims.currentTextChanged.connect(self.getVimIp)

        self.comboBoxImages.currentTextChanged.connect(self.setStorage)

        self.execBut.clicked.connect(self.execute)

        self.pushButtonDelete.clicked.connect(self.delete)

        self.pushButtonReload.clicked.connect(self.reloadVNFs)

        self.pushButtonDelVNF.clicked.connect(self.delDescriptors)

        self.pushButtonDelAll.clicked.connect(self.delDescriptorsAll)

        self.base_vnf_ns_name = ''

        self.vnf_id = ''

        self.ns_id = ''

        self.service_id = ''

        self.progressBar.setValue(0)

        self.timer = QTimer(self)

        self.timer.start(1000)

        self.timer.timeout.connect(self.showCounter)

        self.counter = 3600

        self.startWatch = True

        self.labelClock.setText('')

        self.reloadVNFs()

    def delDescriptorsAll(self):

        for row in range(self.tableVNFs.rowCount()):

            firstColumnInRow = self.tableVNFs.item(row, 0)

            text = firstColumnInRow.text()

            dict = self.main_list.get(text)

            ns_id = dict['id_ns']

            vnf_id = dict['id_vnf']

            try:

                del_nsd_url = Settings.URL_MANO + Settings.API_DELETE_NSS + ns_id

                del_ns = self.delRequest(del_nsd_url)

                if (del_ns == 204):

                    print("Delete: {}".format(del_ns))

                    del_vnfd_url = Settings.URL_MANO + Settings.API_DELETE_VNFS + vnf_id

                    del_vnf = self.delRequest(del_vnfd_url)

                else:

                    print("NOT delete: {}".format(ns_id))

            except Exception as e:

                print(e)

        self.reloadVNFs()

    def delDescriptors(self):

        row = self.tableVNFs.currentRow()  # Index of Row

        if (row >= 0):

            firstColumnInRow = self.tableVNFs.item(row, 0)  # returns QTableWidgetItem

            text = firstColumnInRow.text()  # content of this

            dict = self.main_list.get(text)

            ns_id = dict['id_ns']

            vnf_id = dict['id_vnf']

            try:

                del_nsd_url = Settings.URL_MANO + Settings.API_DELETE_NSS + ns_id

                del_ns = self.delRequest(del_nsd_url)

                print(del_ns)

                del_vnfd_url = Settings.URL_MANO + Settings.API_DELETE_VNFS + vnf_id

                del_vnf = self.delRequest(del_vnfd_url)

                print(del_vnf)

            except Exception as e:

                print(e)

            self.reloadVNFs()

    def delRequest(self, url):

        header = {"Content-type": "application/json",

                  "Accept": "application/json",

                  "Authorization": "Bearer " + Settings.TOKEN}

        url = url

        r = requests.delete(url, headers=header)

        status = int(r.status_code)

        return status

    def getRequest(self, url):

        header = {"Content-type": "application/json",

                  "Accept": "application/json",

                  "Authorization": "Bearer " + Settings.TOKEN}

        url = url

        r = requests.get(url, headers=header)

        status = int(r.status_code)

        r.encoding

        jsonData = r.json()

        return jsonData

    def reloadVNFs(self):

        self.tableVNFs.setRowCount(0)

        self.vnf_list = {}

        self.ns_list = {}

        self.main_list = {}

        url_ns_list = Settings.URL_MANO + Settings.API_GET_NSS

        jsonData_ns = self.getRequest(url_ns_list)

        url_vnf_list = Settings.URL_MANO + Settings.API_GET_VNFS

        jsonData_vnf = self.getRequest(url_vnf_list)

        #  {'k8s_apache_ns': ['k8s_apache_knf', 1663778630],

        # обработаем возвращенный список NSd

        for item_ns_list in jsonData_ns:
            id_ns = item_ns_list['_id']

            nameNS = item_ns_list['id']

            nameVNF = item_ns_list['vnfd-id'][0]

            time_createNS = int(item_ns_list['_admin']['created'])

            self.ns_list[nameNS] = [nameVNF, time_createNS, id_ns]

        # обработаем возвращенный список NSd

        for item_vnf_list in jsonData_vnf:
            id_vnf = item_vnf_list['_id']

            nameVNF = item_vnf_list['id']

            self.vnf_list[nameVNF] = [id_vnf]

        # сформируем общий словарь:

        key = 0

        for item in self.ns_list.items():
            name_ns = item[0]

            array_data_ns = item[1]

            name_vnf = array_data_ns[0]

            date = time.strftime("%d-%m-%Y %H:%M", time.localtime(int(array_data_ns[1])))

            id_ns = array_data_ns[2]

            id_vnf = self.vnf_list[name_vnf][0]

            val_dict = {'name_ns': name_ns, 'id_ns': id_ns, 'name_vnf': name_vnf, 'id_vnf': id_vnf, 'date': date}

            self.main_list[name_ns] = val_dict

            self.tableVNFs.setRowCount(key + 1)

            self.tableVNFs.setItem(key, 0, QTableWidgetItem(name_ns))

            self.tableVNFs.setItem(key, 1, QTableWidgetItem(name_vnf))

            self.tableVNFs.setItem(key, 2, QTableWidgetItem(str(date)))

            key = key + 1

        # {'k8s_apache_ns':

        #   {

        #       'name_ns': 'k8s_apache_ns',

        #       'id_ns': '6eaae2da-cee2-43ac-975a-835cba5f12f5',

        #       'name_vnf': 'k8s_apache_knf',

        #       'id_vnf': 'c60ebcfa-24ac-43ca-a569-b39e8f816370',

        #       'date': '21-09-2022 19:43'

        #   }, ...

        self.tableVNFs.resizeColumnsToContents()

    def setStorage(self):

        curChek = self.comboBoxImages.currentText()

        if curChek in ('Postgresql'):

            self.label_storage.setText("DB Size: ")

            self.setWindowTitle('Create Database')

        else:

            self.label_storage.setText("Storage: ")

            self.setWindowTitle('Create Instance')

    def radioBtn(self):

        if self.radioButtonCloud.isChecked():

            self.textEditCloudConfig.setDisabled(False)

        else:

            self.textEditCloudConfig.setDisabled(True)

            self.textEditCloudConfig.setText('')

    def showCounter(self):
        if self.startWatch:
            self.counter -= 1
        minutes = floor(self.counter / 60)
        seconds = int(self.counter % 60)
        min_show = f"{minutes:02d}"
        sec_show = f"{seconds:02d}"
        text = min_show + ':' + sec_show
        self.labelClock.setText(text)
        if self.counter < 1:
            self.restart()

    def restart(self):
        self.counter = 3600
        login = Settings.CURRENT_LOGIN
        password = Settings.CURRENT_PASSWORD
        project = Settings.CURRENT_PROJECT
        url = Settings.URL_MANO + Settings.API_TOKENS
        post_fields = {'username': login, 'password': password, 'project_id': project}  # Set POST fields here
        header = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        r = requests.post(url, data=urlencode(post_fields), headers=header)
        r.encoding
        jsonData = r.json()
        status = int(r.status_code)
        if status == Settings.STATUS_TOKEN_CREATE:
            token = jsonData['_id']
            if len(token) > 10:
                Settings.TOKEN = token

    def getVims(self):

        url = Settings.URL_MANO + Settings.API_VIM_ACCOUNTS

        r = requests.get(url, headers=self.header)

        r.encoding

        jsonData = r.json()

        for item in jsonData:
            id = item['_id']

            name = item['name']

            type = item['vim_type']

            url = item["vim_url"]

            self.vim_list[name] = [id, type, url]

    def fillCombos(self):

        # VIM LIST

        vim_names = []

        for k in self.vim_list.keys():
            vim_names.append(k)

        self.comboBoxVims.addItems(vim_names)

        # RAM

        self.comboBoxRam.addItems(Settings.RAM_SIZES)

        # STORAGE

        self.comboBoxStorage.addItems(Settings.STORAGE_SIZES)

        # CPU

        self.comboBoxCpu.addItems(Settings.CPU_QNT)

        # Networks

        self.comboBoxNetwork.addItems(Settings.OPENSTACK_NETWORKS)

        # IMAGE

        image_name = []

        for k in Settings.OPENSTACK_IMAGES.keys():
            image_name.append(k)

        self.comboBoxImages.addItems(image_name)

    def getVimIp(self):

        curChek = self.comboBoxVims.currentText()

        ip = self.vim_list[curChek][2]

        self.labelIp.setText(ip)

    def deleteBtnVisual(self):

        if self.pushButtonDelete.isVisible():

            self.pushButtonDelete.setVisible(False)

        else:

            self.pushButtonDelete.setVisible(True)

    def execute(self):

        imageName = self.comboBoxImages.currentText()

        image = Settings.OPENSTACK_IMAGES[imageName]

        ram = self.comboBoxRam.currentText()

        vcpu = self.comboBoxCpu.currentText()

        storage = self.comboBoxStorage.currentText()

        network_name = self.comboBoxNetwork.currentText()

        self.base_vnf_ns_name = self.lineEdit.text()

        description = self.lineEditDescription.text()

        vimName = self.comboBoxVims.currentText()

        vimId = self.vim_list[vimName][0]

        header = {"Content-type": "application/json",

                  "Accept": "application/json",

                  "Authorization": "Bearer " + Settings.TOKEN}

        if self.base_vnf_ns_name != '':

            # create VNFd

            vnf_id_name = self.base_vnf_ns_name + '_vnf'

            cloud_config = ""

            if self.radioButtonCloud.isChecked():

                data_cloud = self.textEditCloudConfig.toPlainText()

                if data_cloud != "":
                    cloud_config = data_cloud.replace('\n', "\n")

            vnf = sceletons.createVnfNew(image, ram, vcpu, storage, vnf_id_name, description, cloud_config)

            # json.dumps() converts a dictionary to str object

            url = Settings.URL_MANO + Settings.API_CREATE_VNF

            # request to add VNFd

            r = requests.post(url, json=vnf, headers=header)

            jsonDataVnf = r.json()

            status = int(r.status_code)

            self.vnf_id = jsonDataVnf['id']

            print("VNF_ID: ", self.vnf_id)

            if (status == Settings.STATUS_VNF_CREATED):

                self.progressBar.setValue(1)

                # create NSd

                ns_id_name = self.base_vnf_ns_name + '_ns'

                ns = sceletons.createNs(ns_id_name, vnf_id_name, network_name, description)

                url = Settings.URL_MANO + Settings.API_CREATE_NS

                r = requests.post(url, json=ns, headers=header)

                jsonDataNs = r.json()

                status = int(r.status_code)

                print(status)

                self.ns_id = jsonDataNs['id']

                print("NS_ID: ", self.ns_id)

                if (status == Settings.STATUS_NS_CREATED):

                    self.progressBar.setValue(2)

                    # create service!

                    instance_name = self.base_vnf_ns_name

                    instance_description = description

                    ns_id = self.ns_id

                    vim_id = vimId

                    header = {"Content-type": "application/json",

                              "Accept": "application/json",

                              "Authorization": "Bearer " + Settings.TOKEN}

                    ns_create = sceletons.createInstance(instance_name, instance_description, ns_id, vim_id)

                    url = Settings.URL_MANO + Settings.API_CREATE_INSTANCE

                    print(ns_create)

                    r = requests.post(url, json=ns_create, headers=header)

                    jsonDataInstance = r.json()

                    status = int(r.status_code)

                    print(status)

                    try:

                        self.service_id = jsonDataInstance['id']

                    except Exception as e:

                        print(e)

                    if (status == Settings.STATUS_INSTANCE_CREATED):
                        self.progressBar.setValue(3)

                        self.deleteBtnVisual()

        else:

            print("Name instance!!!")

        self.reloadVNFs()

    def delete(self):

        header = {"Content-type": "application/json",

                  "Accept": "application/json",

                  "Authorization": "Bearer " + Settings.TOKEN}

        del_url = Settings.URL_MANO + Settings.API_DELETE_INSTANCE + self.service_id

        r = requests.delete(del_url, headers=header)

        status = int(r.status_code)

        if (status == Settings.STATUS_NS_DELETE):
            self.deleteBtnVisual()

            self.progressBar.setValue(0)

            self.lineEdit.setText('')

            self.lineEditDescription.setText('')

            self.textEditCloudConfig.setText('')


class Login(QDialog):

    def __init__(self, parent=None):

        super(Login, self).__init__(parent)

        uic.loadUi('dialog.ui', self)

        self.buttonLogin.clicked.connect(self.handleLogin)

        self.lineEditProject.setText("")

        self.lineEdit.setText("DKORNEV")

        self.lineEditPass.setText("q12345")

        self.lineEditUrl.setText("http://10.0.69.115")  # http://10.0.69.115/osm

        self.lineEditPass.setEchoMode(QLineEdit.Password)

    def handleLogin(self):

        flag = False

        Settings.URL_MANO = self.lineEditUrl.text() + '/osm'

        login = self.lineEdit.text()

        password = self.lineEditPass.text()

        project = self.lineEditProject.text()

        Settings.CURRENT_LOGIN = login

        Settings.CURRENT_PASSWORD = password

        Settings.CURRENT_PROJECT = project

        url = Settings.URL_MANO + Settings.API_TOKENS

        post_fields = {'username': login, 'password': password, 'project_id': project}  # Set POST fields here

        header = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}

        r = requests.post(url, data=urlencode(post_fields), headers=header)

        r.encoding

        jsonData = r.json()

        status = int(r.status_code)

        if status == Settings.STATUS_TOKEN_CREATE:

            token = jsonData['_id']

            if len(token) > 10:
                flag = True

                Settings.TOKEN = token

                self.accept()

        if flag == False:
            self.labelInfo.setText("ошибка: " + str(status))


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)

    login = Login()

    if login.exec_() == QDialog.Accepted:
        window = MainWidget()

        window.show()

        sys.exit(app.exec_())