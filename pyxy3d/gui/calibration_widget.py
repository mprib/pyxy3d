import pyxy3d.logger

logger = pyxy3d.logger.get(__name__)

import os
import sys
import shutil
import time
from pathlib import Path
from threading import Thread
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QFileDialog,
    QStackedWidget,
)

from pyxy3d.session.session import Session, SessionMode
from pyxy3d.gui.wizard_charuco import WizardCharuco
from pyxy3d.gui.camera_config.camera_tabs import CameraWizard
from pyxy3d import __root__, __app_dir__
from pyxy3d.trackers.charuco_tracker import CharucoTracker
# from pyxy3d.gui.qt_logger import QtLogger
from pyxy3d.gui.stereoframe.stereo_frame_widget import (
    ExtrinsicCalibrationWidget,
    MIN_THRESHOLD_FOR_EARLY_CALIBRATE,
)
from pyxy3d.gui.vizualize.calibration.capture_volume_widget import CaptureVolumeWidget
from pyxy3d.configurator import Configurator


class CalibrationWidget(QStackedWidget):
    cameras_connected = pyqtSignal()

    def __init__(self, session:Session):
        super().__init__()
        self.CAMS_IN_PROCESS = False

        self.setWindowTitle("Camera Calibration Wizard")
        self.setWindowIcon(QIcon(str(Path(__root__, "pyxy3d/gui/icons/pyxy_logo.svg"))))
        self.session_path = session.path
        self.session = session
        self.config = session.config

        # self.launch_session()
        logger.info("Creating charuco wizard session")
        self.wizard_charuco = WizardCharuco(self.session)
        
        self.wizard_charuco.navigation_bar.next_wizard_step_btn.clicked.connect(
            self.activate_camera_config
        )
        logger.info("Adding charuco wizard")
        self.session.set_mode(SessionMode.Charuco)
        self.addWidget(self.wizard_charuco)

        logger.info("Setting index to 2 to activate widget")
        self.setCurrentWidget(self.wizard_charuco)

        self.connect_widgets()

    def connect_widgets(self):
        # self.wizard_directory.launch_wizard_btn.clicked.connect(self.begin_wizard)
        # self.cameras_connected.connect(self.on_cameras_connect)
        pass



    def activate_camera_config(self):
        self.session.set_mode(SessionMode.IntrinsicCalibration)
        if not hasattr(self, "camera_wizard"):
            logger.info(f"No camera configuration yet...creating wizard")
            self.camera_wizard = CameraWizard(self.session)
            self.addWidget(self.camera_wizard)
            self.setCurrentWidget(self.camera_wizard)
            self.camera_wizard.navigation_bar.back_btn.clicked.connect(
                self.activate_charuco_wizard
            )
            self.camera_wizard.navigation_bar.next_btn.clicked.connect(
                self.next_to_stereoframe
            )
        else:
            logger.info("Camera config already exists; changing stack current index")
            # active_port = self.camera_wizard.camera_tabs.currentIndex()
            # self.session.active_monocalibrator = active_port
            self.setCurrentWidget(self.camera_wizard)
            self.session.activate_monocalibrator()

    ####################### STEP 2: Single Camera Calibration #################
    def activate_charuco_wizard(self):
        self.session.set_mode(SessionMode.Charuco)
        self.setCurrentWidget(self.wizard_charuco)

    def next_to_stereoframe(self):
        self.session.set_mode(SessionMode.ExtrinsicCalibration)

        if hasattr(self, "stereoframe"):
            self.setCurrentWidget(self.stereoframe)
            # self.stereoframe.deleteLater()
            # self.removeWidget(self.stereoframe)
        else: 
            self.stereoframe = ExtrinsicCalibrationWidget(self.session)
            self.addWidget(self.stereoframe)
            self.setCurrentWidget(self.stereoframe)

            self.stereoframe.navigation_bar.back_btn.clicked.connect(
                self.back_to_camera_config_wizard
            )

            self.stereoframe.calibration_complete.connect(self.next_to_capture_volume)
            # self.stereoframe.calibration_initiated.connect(self.show_calibration_qt_logger)
            self.stereoframe.terminate.connect(self.refresh_stereoframe)

    ###################### Stereocalibration  ######################################
    def refresh_stereoframe(self):
        logger.info("Set current widget to config temporarily")
        self.setCurrentWidget(self.camera_wizard)

        logger.info("Remove stereoframe")
        self.removeWidget(self.stereoframe)
        self.stereoframe.frame_builder.unsubscribe_from_synchronizer()
        del self.stereoframe

        logger.info("Create new stereoframe")
        self.launch_new_stereoframe()


    def back_to_camera_config_wizard(self):
        logger.info("Moving back to camera config from stereoframe")
        self.setCurrentWidget(self.camera_wizard)
        self.session.pause_synchronizer()

        self.stereoframe.frame_builder.unsubscribe_from_synchronizer()
        self.removeWidget(self.stereoframe)
        del self.stereoframe

        active_port = self.camera_wizard.camera_tabs.currentIndex()
        self.camera_wizard.camera_tabs.activate_current_tab(active_port)

    def next_to_capture_volume(self):
        logger.info("Creating Capture Volume widget")
        self.capture_volume = CaptureVolumeWidget(self.session)
        logger.info("Adding capture volume widget to main Wizard")
        self.addWidget(self.capture_volume)
        logger.info("Set current index to capture volume widget")
        self.setCurrentWidget(self.capture_volume)
        self.capture_volume.navigation_bar.back_btn.clicked.connect(
            self.back_to_stereo_frame
        )

        del self.qt_logger

    ################## Capture Volume ########################
    def back_to_stereo_frame(self):
        logger.info("Set current widget to config temporarily")
        self.setCurrentWidget(self.camera_wizard)

        logger.info("Remove stereoframe")
        self.removeWidget(self.stereoframe)
        logger.info("Remove capture volume")
        self.removeWidget(self.capture_volume)
        del self.capture_volume
        self.stereoframe.frame_builder.unsubscribe_from_synchronizer()
        del self.stereoframe

        logger.info("Create new stereoframe")
        self.launch_new_stereoframe()
        self.session.unpause_synchronizer()


def launch_calibration_widget(session_path:Path):
    config = Configurator(session_path)
    session = Session(config)

    app = QApplication(sys.argv)

    window = CalibrationWidget(session)
    window.show()
    app.exec()


