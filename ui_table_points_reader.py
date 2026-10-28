# -*- coding: utf-8 -*-

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QHBoxLayout, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(463, 710)
        MainWindow.setMinimumSize(QSize(463, 710))

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")

        self.mainVerticalLayout = QVBoxLayout(self.centralwidget)
        self.mainVerticalLayout.setObjectName(u"mainVerticalLayout")
        self.mainVerticalLayout.setContentsMargins(10, 10, 10, 10)
        self.mainVerticalLayout.setSpacing(8)

        self.topButtonsLayout = QHBoxLayout()
        self.topButtonsLayout.setObjectName(u"topButtonsLayout")
        self.topButtonsLayout.setSpacing(8)

        self.pushButton_select_file = QPushButton(self.centralwidget)
        self.pushButton_select_file.setObjectName(u"pushButton_select_file")
        self.pushButton_select_file.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.topButtonsLayout.addWidget(self.pushButton_select_file)

        self.pushButton_get_selected_points = QPushButton(self.centralwidget)
        self.pushButton_get_selected_points.setObjectName(u"pushButton_get_selected_points")
        self.pushButton_get_selected_points.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.topButtonsLayout.addWidget(self.pushButton_get_selected_points)

        self.mainVerticalLayout.addLayout(self.topButtonsLayout)

        self.tableWidget_select_points = QTableWidget(self.centralwidget)
        self.tableWidget_select_points.setObjectName(u"tableWidget_select_points")
        self.tableWidget_select_points.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mainVerticalLayout.addWidget(self.tableWidget_select_points)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 463, 26))
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Зчитувач адрес з файлу", None))
        self.pushButton_select_file.setText(QCoreApplication.translate("MainWindow", u"Вибрати файл", None))
        self.pushButton_get_selected_points.setText(QCoreApplication.translate("MainWindow", u"Підтвердити вибрані адреси", None))
    # retranslateUi

