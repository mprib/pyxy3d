from PyQt6.QtWidgets import QApplication
from pyxy3d.gui.calibration_widget import CalibrationWidget
import sys
from time import sleep
from pyxy3d import __root__
from pathlib import Path
from pyxy3d.configurator import Configurator
from pyxy3d.session import Session

# config_path = Path(__root__, "dev", "sample_sessions", "post_optimization")
# config_path = Path(__root__, "dev", "sample_sessions", "real_time")
session_path = Path(__root__, "dev", "sample_sessions", "293")
# config_path = Path(__root__, "dev", "sample_sessions", "test_calibration")
config = Configurator(session_path)
session = Session(config)
   
app = QApplication(sys.argv)
window = CalibrationWidget(session)

# open in a session already so you don't have to go through the menu each time
# window.open_session(config_path)
# window.wizard_directory.from_previous_radio.click()
# window.wizard_directory.from_previous_radio.setChecked(True)
# window.wizard_directory.launch_wizard_btn.setEnabled(True)
# window.wizard_directory.original_path.textbox.setText(str(session_path))
# window.wizard_directory.modified_path.textbox.setText(str(session_path))
# window.wizard_directory.launch_wizard_btn.click()
# window.wizard_charuco.navigation_bar.next_wizard_step_btn.click()

window.show()

app.exec()