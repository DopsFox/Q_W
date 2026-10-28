# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_main.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QHeaderView, QMainWindow, QMenuBar, QPushButton, QSizePolicy, QStatusBar,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1082, 851)
        MainWindow.setMinimumSize(QSize(1082, 851))

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")

        # Main Vertical Layout for CentralWidget
        self.mainVerticalLayout = QVBoxLayout(self.centralwidget)
        self.mainVerticalLayout.setObjectName(u"mainVerticalLayout")
        self.mainVerticalLayout.setContentsMargins(10, 10, 10, 10)
        self.mainVerticalLayout.setSpacing(10)

        # Top Horizontal Layout (Map on Left, Controls & Metrics on Right)
        self.topHorizontalLayout = QHBoxLayout()
        self.topHorizontalLayout.setObjectName(u"topHorizontalLayout")
        self.topHorizontalLayout.setSpacing(10)

        # Map Container
        self.widget_map_container = QWidget(self.centralwidget)
        self.widget_map_container.setObjectName(u"widget_map_container")
        self.widget_map_container.setMinimumSize(QSize(400, 300))
        self.widget_map_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.widget_map_container.setStyleSheet(u"background-color: rgb(193, 199, 153);")
        self.topHorizontalLayout.addWidget(self.widget_map_container, 3)

        # Right Vertical Layout (Navigation + Buttons + Controls on top, Calculation Table on bottom)
        self.rightVerticalLayout = QVBoxLayout()
        self.rightVerticalLayout.setObjectName(u"rightVerticalLayout")
        self.rightVerticalLayout.setSpacing(8)

        # Top Navigation Layout (Back & Forward)
        self.navHorizontalLayout = QHBoxLayout()
        self.navHorizontalLayout.setObjectName(u"navHorizontalLayout")
        self.navHorizontalLayout.setSpacing(10)

        self.pushButton_back = QPushButton(self.centralwidget)
        self.pushButton_back.setObjectName(u"pushButton_back")
        self.pushButton_back.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.navHorizontalLayout.addWidget(self.pushButton_back)

        self.pushButton_forward = QPushButton(self.centralwidget)
        self.pushButton_forward.setObjectName(u"pushButton_forward")
        self.pushButton_forward.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.navHorizontalLayout.addWidget(self.pushButton_forward)

        self.rightVerticalLayout.addLayout(self.navHorizontalLayout)

        # Controls Grid Layout (Left sub-column & Right sub-column)
        self.controlsGridLayout = QGridLayout()
        self.controlsGridLayout.setObjectName(u"controlsGridLayout")
        self.controlsGridLayout.setHorizontalSpacing(10)
        self.controlsGridLayout.setVerticalSpacing(6)

        # Left Column of Controls
        self.pushButton_add_start = QPushButton(self.centralwidget)
        self.pushButton_add_start.setObjectName(u"pushButton_add_start")
        self.pushButton_add_start.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_add_start, 0, 0, 1, 1)

        self.pushButton_add_finish = QPushButton(self.centralwidget)
        self.pushButton_add_finish.setObjectName(u"pushButton_add_finish")
        self.pushButton_add_finish.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_add_finish, 1, 0, 1, 1)

        self.comboBox_search_method = QComboBox(self.centralwidget)
        self.comboBox_search_method.setObjectName(u"comboBox_search_method")
        self.comboBox_search_method.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.controlsGridLayout.addWidget(self.comboBox_search_method, 2, 0, 1, 1)

        self.comboBox_rout_type = QComboBox(self.centralwidget)
        self.comboBox_rout_type.setObjectName(u"comboBox_rout_type")
        self.comboBox_rout_type.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.controlsGridLayout.addWidget(self.comboBox_rout_type, 3, 0, 1, 1)

        self.pushButton_information = QPushButton(self.centralwidget)
        self.pushButton_information.setObjectName(u"pushButton_information")
        self.pushButton_information.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_information, 4, 0, 1, 1)

        self.pushButton_logic = QPushButton(self.centralwidget)
        self.pushButton_logic.setObjectName(u"pushButton_logic")
        self.pushButton_logic.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_logic, 5, 0, 1, 1)

        # Right Column of Controls
        self.pushButton_add_new_point = QPushButton(self.centralwidget)
        self.pushButton_add_new_point.setObjectName(u"pushButton_add_new_point")
        self.pushButton_add_new_point.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_add_new_point, 0, 1, 1, 1)

        self.pushButton_delete_point = QPushButton(self.centralwidget)
        self.pushButton_delete_point.setObjectName(u"pushButton_delete_point")
        self.pushButton_delete_point.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_delete_point, 1, 1, 1, 1)

        self.pushButton_calculate_route = QPushButton(self.centralwidget)
        self.pushButton_calculate_route.setObjectName(u"pushButton_calculate_route")
        self.pushButton_calculate_route.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_calculate_route, 2, 1, 1, 1)

        self.pushButton_save_route = QPushButton(self.centralwidget)
        self.pushButton_save_route.setObjectName(u"pushButton_save_route")
        self.pushButton_save_route.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_save_route, 3, 1, 1, 1)

        self.pushButton_regular_deliveries = QPushButton(self.centralwidget)
        self.pushButton_regular_deliveries.setObjectName(u"pushButton_regular_deliveries")
        self.pushButton_regular_deliveries.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_regular_deliveries, 4, 1, 1, 1)

        self.pushButton_edit_delivery = QPushButton(self.centralwidget)
        self.pushButton_edit_delivery.setObjectName(u"pushButton_edit_delivery")
        self.pushButton_edit_delivery.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_edit_delivery, 5, 1, 1, 1)

        # File Reader Button (Spanning both columns)
        self.pushButton_open_points_file = QPushButton(self.centralwidget)
        self.pushButton_open_points_file.setObjectName(u"pushButton_open_points_file")
        self.pushButton_open_points_file.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.controlsGridLayout.addWidget(self.pushButton_open_points_file, 6, 0, 1, 2)

        self.rightVerticalLayout.addLayout(self.controlsGridLayout)

        # Calculation Metrics Table
        self.tableWidget_calculation = QTableWidget(self.centralwidget)
        self.tableWidget_calculation.setObjectName(u"tableWidget_calculation")
        self.tableWidget_calculation.setMinimumSize(QSize(250, 150))
        self.tableWidget_calculation.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.rightVerticalLayout.addWidget(self.tableWidget_calculation)

        self.topHorizontalLayout.addLayout(self.rightVerticalLayout, 2)

        # Add Top Section to Main Layout with stretch
        self.mainVerticalLayout.addLayout(self.topHorizontalLayout, 3)

        # Bottom Waypoints Table
        self.tableWidget_waypoints = QTableWidget(self.centralwidget)
        self.tableWidget_waypoints.setObjectName(u"tableWidget_waypoints")
        self.tableWidget_waypoints.setMinimumSize(QSize(600, 200))
        self.tableWidget_waypoints.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.mainVerticalLayout.addWidget(self.tableWidget_waypoints, 2)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1082, 21))
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Маршрутизатор замовлень", None))
        self.pushButton_back.setText(QCoreApplication.translate("MainWindow", u"◀ Назад", None))
        self.pushButton_forward.setText(QCoreApplication.translate("MainWindow", u"Вперед ▶", None))
        self.pushButton_add_new_point.setText(QCoreApplication.translate("MainWindow", u"\u0414\u043e\u0434\u0430\u0442\u0438 \u0442\u043e\u0447\u043a\u0443", None))
        self.pushButton_delete_point.setText(QCoreApplication.translate("MainWindow", u"\u0412\u0438\u0434\u0430\u043b\u0438\u0442\u0438 \u0442\u043e\u0447\u043a\u0443", None))
        self.pushButton_calculate_route.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0431\u0447\u0438\u0441\u043b\u0438\u0442\u0438 \u043c\u0430\u0440\u0448\u0440\u0443\u0442", None))
        self.pushButton_save_route.setText(QCoreApplication.translate("MainWindow", u"\u0417\u0430\u043f\u0438\u0441\u0430\u0442\u0438 \u043c\u0430\u0440\u0448\u0440\u0443\u0442", None))
        self.pushButton_regular_deliveries.setText(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0433\u0443\u043b\u044f\u0440\u043d\u0456 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443", None))
        self.pushButton_edit_delivery.setText(QCoreApplication.translate("MainWindow", u"\u0420\u0435\u0434\u0430\u0433\u0443\u0432\u0430\u0442\u0438 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0443", None))
        self.pushButton_information.setText(QCoreApplication.translate("MainWindow", u"Information", None))
        self.pushButton_logic.setText(QCoreApplication.translate("MainWindow", u"Logic", None))
        self.pushButton_add_start.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.pushButton_add_finish.setText(QCoreApplication.translate("MainWindow", u"Finish", None))
        self.pushButton_open_points_file.setText(QCoreApplication.translate("MainWindow", u"Зчитати точки з файлу", None))
    # retranslateUi
