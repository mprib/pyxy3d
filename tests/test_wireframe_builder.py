from pathlib import Path
from pyxy3d.trackers.wireframe_builder import get_wireframe
from pyxy3d import __root__

import pyxy3d.logger
from pyxy3d.tracker import WireFrameView, Segment
from pyxy3d.trackers.holistic.holistic_tracker import POINT_NAMES, HolisticTracker
logger = pyxy3d.logger.get(__name__)

def test_wireframe_builder():
    """
    Simple test to aid with development of integrating the wireframe
    """

    test_path = Path(__root__,r"pyxy3d\trackers\holistic\holistic_wireframe.toml")
    logger.info(f"Testing wireframe build of {test_path}")
    wireframe = get_wireframe(test_path, point_names=POINT_NAMES)
    
    assert(isinstance(wireframe,WireFrameView))

    for segment in wireframe.segments:
        assert(isinstance(segment,Segment))

    logger.info(wireframe)
 
def test_holistic_wireframe():
    """
    making sure the integration with the tracker is working...
    at least not throwing an error
    """
    
    tracker = HolisticTracker()
    wireframe = tracker.wireframe

    assert(isinstance(wireframe,WireFrameView))

    for segment in wireframe.segments:
        assert(isinstance(segment,Segment))

    logger.info(wireframe)

if __name__ == "__main__":
    
    # test_wireframe_builder()
    test_holistic_wireframe()