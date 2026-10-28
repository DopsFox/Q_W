# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_start_or_finish.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(627, 203)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.layoutWidget = QWidget(self.centralwidget)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(0, 0, 381, 91))
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.textEdit_text_adress_start_finish = QTextEdit(self.layoutWidget)
        self.textEdit_text_adress_start_finish.setObjectName(u"textEdit_text_adress_start_finish")

        self.verticalLayout_3.addWidget(self.textEdit_text_adress_start_finish)

        self.textEdit_coordinates_address_start_finish = QTextEdit(self.layoutWidget)
        self.textEdit_coordinates_address_start_finish.setObjectName(u"textEdit_coordinates_address_start_finish")

        self.verticalLayout_3.addWidget(self.textEdit_coordinates_address_start_finish)

        self.layoutWidget_2 = QWidget(self.centralwidget)
        self.layoutWidget_2.setObjectName(u"layoutWidget_2")
        self.layoutWidget_2.setGeometry(QRect(380, 0, 241, 91))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.layoutWidget_2)
        self.label.setObjectName(u"label")

        self.verticalLayout_4.addWidget(self.label)

        self.label_2 = QLabel(self.layoutWidget_2)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_4.addWidget(self.label_2)

        self.pushButton_add_start_finish = QPushButton(self.centralwidget)
        self.pushButton_add_start_finish.setObjectName(u"pushButton_add_start_finish")
        self.pushButton_add_start_finish.setGeometry(QRect(220, 100, 211, 51))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 627, 26))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"- \u0422\u0435\u043a\u0441\u0442\u043e\u0432\u0430 \u0430\u0434\u0440\u0435\u0441\u0430", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"- \u0410\u0434\u0440\u0435\u0441\u0430 \u0437\u0430\u0434\u0430\u043d\u0430 \u043a\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u0430\u043c\u0438 ", None))
        self.pushButton_add_start_finish.setText(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u0434\u0430\u0442\u0438 \u0421\u0422\u0410\u0420\u0422/\u0424\u0406\u041d\u0406\u0428", None))
    # retranslateUi

