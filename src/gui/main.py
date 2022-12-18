import logging
import sys

LOG_FILE = "log\main.log"
# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO
LOG_FORMAT = " %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"

logging.basicConfig(filename=LOG_FILE, filemode="w", format=LOG_FORMAT, level=LOG_LEVEL)

import time
from pathlib import Path, PurePath
from threading import Thread

from numpy import char
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QToolBar,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.session import Session
from src.gui.left_sidebar.session_summary import SessionSummary
from src.gui.charuco_builder import CharucoBuilder
from src.gui.camera_config.camera_tabs import CameraTabs
class MainWindow(QMainWindow):
    def __init__(self, session=None):
        super().__init__()
        self.repo = Path(__file__).parent.parent.parent
        if session is not None:
            self.session = session

        app = QApplication.instance()
        screen = app.primaryScreen()
        DISPLAY_WIDTH = screen.size().width()
        DISPLAY_HEIGHT = screen.size().height()

        self.setMinimumSize(DISPLAY_WIDTH * 0.45, DISPLAY_HEIGHT * 0.7)
        self.setWindowTitle("FreeMocap Camera Calibration")
        self.setWindowIcon(QIcon("src/gui/icons/fmc_logo.ico"))

        self.menu = self.menuBar()
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.CAMS_IN_PROCESS = False
        # self.
        self.build_file_menu()
        self.build_view_menu()
        self.build_actions_menu()
        
        
    def build_file_menu(self):
        
        file = self.menu.addMenu("&File")
        file_new_session = QAction("Create &New Session", self)
        file_new_session.triggered.connect(self.get_session)
        file.addAction(file_new_session)
        
        file_saved_session = QAction("&Open Saved Session", self)
        file_saved_session.triggered.connect(self.get_session)
        file.addAction(file_saved_session)

    def get_session(self):
        
        logging.info("Prompting for session path...")
        sessions_directory = str(Path(self.repo, "sessions"))
        session_path = QFileDialog.getExistingDirectory(
            self, "Select Session Folder", sessions_directory
        )

        self.open_session(session_path)

    def open_session(self, session_path):
        """The primary action of choosing File--Open or New session"""
        try:
            # self.summary.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose,True)
            self.summary.close()
        except(AttributeError):
            pass
        
        logging.info(f"Opening session located at {session_path}")
        self.session = Session(session_path)
        self.summary = SessionSummary(self.session)
        
        
        self.dock = QDockWidget("Session Summary", self)
        self.dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dock.setWidget(self.summary)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)

    
    def build_view_menu(self): 
        view = self.menu.addMenu("&View")

        build_charuco = QAction("&Build Charuco", self)
        view.addAction(build_charuco)
        build_charuco.triggered.connect(self.activate_charuco_builder)

        self.configure_cameras = QAction("Configure Cameras", self)
        self.configure_cameras.setEnabled(False)
        view.addAction(self.configure_cameras)
        self.configure_cameras.triggered.connect(self.launch_cam_config_dialog)

    def build_actions_menu(self):
        actions = self.menu.addMenu("&Actions")
        # self.menu.addMenu(actions)

        self.connect_cameras_action = QAction("Connect to &Saved Cameras", self)
        actions.addAction(self.connect_cameras_action)
        self.connect_cameras_action.triggered.connect(self.connect_to_cameras)
        
        self.find_additional_action = QAction("&Find Cameras", self)
        actions.addAction(self.find_additional_action)
        self.find_additional_action.triggered.connect(self.find_cameras)
        
        self.disconnect_cam_action = QAction("&Disconnect Cameras", self)
        self.disconnect_cam_action.setEnabled(False)
        actions.addAction(self.disconnect_cam_action)
        self.disconnect_cam_action.triggered.connect(self.disconnect_cameras)

    def launch_cam_config_dialog(self):
        
        # self.camera_tabs = None
        if not hasattr(self,"camera_tabs"):
            self.camera_tabs = CameraTabs(self.session)
            
            def on_save_cam_click():
                self.summary.camera_summary.camera_table.update_data()
            
            for tab_index in range(self.camera_tabs.count()):
                self.camera_tabs.widget(tab_index).save_cal_btn.clicked.connect(on_save_cam_click)
            
            self.central_stack.addWidget(self.camera_tabs)
            self.central_stack.setCurrentWidget(self.camera_tabs) 
        else:
            self.central_stack.setCurrentWidget(self.camera_tabs)
        
    def close_cam_config(self):
        pass
    
    def connect_to_cameras(self):

        if len(self.session.cameras) > 0:
            logging.info("Cameras already connected")
            pass
        else:

            def connect_to_cams_worker():
                logging.info("Initiating camera connect worker")
                self.session.load_cameras()
                logging.info("Camera connect worker about to load stream tools")
                self.session.load_streams()
                logging.info("Camera connect worker about to adjust resolutions")
                self.session.adjust_resolutions()

                logging.info("Camera connect worker about to load monocalibrators")
                self.session.load_monocalibrators()
                self.CAMERAS_CONNECTED = True
                
                # enabling GUI elements 
                self.configure_cameras.setEnabled(True)
                self.summary.synch_fps.frame_rate_spin.setEnabled(True)
                self.summary.camera_summary.connected_cam_count.setText(str(len(self.session.cameras)))
                
                self.disconnect_cam_action.setEnabled(True) #now have cameras to delete
                self.connect_cameras_action.setEnabled(False)
                self.find_additional_action.setEnabled(False)

                self.configure_cameras.trigger()

            self.connect_cams = Thread(target = connect_to_cams_worker, args=[], daemon=True)
            self.connect_cams.start()
            
    def disconnect_cameras(self):
        print("Attempting to disconnect cameras")
        self.configure_cameras.setEnabled(False) 
        self.disconnect_cam_action.setEnabled(False)
        self.connect_cameras_action.setEnabled(True)
        self.find_additional_action.setEnabled(True)

        if hasattr(self, "camera_tabs"):
            self.central_stack.removeWidget(self.camera_tabs) 

        self.session.disconnect_cameras()
        self.summary.camera_summary.connected_cam_count.setText("0")
        del self.camera_tabs 

    def find_cameras(self):

        def find_cam_worker():
            self.CAMS_IN_PROCESS = True
            self.session.find_additional_cameras()
            logging.info("Loading streams")
            self.session.load_streams()
            # logging.info("Adjusting resolutions")
            # self.session.adjust_resolutions()
            logging.info("Loading monocalibrators")
            self.session.load_monocalibrators()
            logging.info("Updating Camera Table")
            self.summary.camera_summary.camera_table.update_data()

            self.CAMS_IN_PROCESS = False
            self.configure_cameras.setEnabled(True)
            self.summary.camera_summary.connected_cam_count.setText(str(len(self.session.cameras)))
            self.disconnect_cam_action.setEnabled(True) #now have cameras to delete
            self.connect_cameras_action.setEnabled(False)
            self.find_additional_action.setEnabled(False)
            self.configure_cameras.trigger()
            
        if not self.CAMS_IN_PROCESS:
            logging.info("Searching for additional cameras...This may take a moment.")
            self.find = Thread(target=find_cam_worker, args=(), daemon=True)
            self.find.start()
        else:
            logging.info("Cameras already connected or in process.")        

    def create_charuco_builder(self):

        self.charuco_builder = CharucoBuilder(self.session)
        self.central_stack.addWidget(self.charuco_builder)
        self.central_stack.setCurrentWidget(self.charuco_builder)

        def update_summary():
            self.summary.charuco_summary.update_charuco_summary()
        
        self.charuco_builder.save_btn.clicked.connect(update_summary)
        
        self.CHARUCO_BUILDER_MADE = True


    def activate_charuco_builder(self):
        if hasattr(self, "charuco_builder"):
            self.central_stack.setCurrentWidget(self.charuco_builder)
        else:
            self.create_charuco_builder()

if __name__ == "__main__":
    repo = Path(__file__).parent.parent.parent
    config_path = Path(repo, "sessions", "high_res_session")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # open in a session already so you don't have to go through the menu each time
    window.open_session(config_path)
    
    window.show()

    app.exec()
