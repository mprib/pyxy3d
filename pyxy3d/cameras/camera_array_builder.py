#%%
import pyxy3d.logger
logger = pyxy3d.logger.get(__name__)

import pandas as pd
import toml
from pathlib import Path
import numpy as np
from pyxy3d.cameras.camera_array import CameraData, CameraArray


class CameraArrayBuilder:
    """An ugly class to wrangle the config data into a useful set of camera
    data objects in a common frame of reference and then return it as a CameraArray object;
    Currently set up to only work when all possible stereo pairs have been stereocalibrated;
    I anticipate this is something that will need to be expanded in the future to account
    for second order position estimates. This might be solved cleanly by putting a frame of reference
    in the CameraData object and extending the CameraArray to place elements in a common frame of reference"""

    def __init__(self, config_path: Path):

        self.config = toml.load(config_path)
        self.default_extrinsics = self.get_default_stereoextrinsics()
        #note, still need to set camera here...sorting it out in refactor script
        # self.set_cameras()

    def set_cameras(self):
        self.cameras = {}
        # create the basic cameras based off of intrinsic params stored in config
        for key, data in self.config.items():
            if key.startswith("cam_") and not self.config[key]['ignore']:
                port = data["port"]
                size = data["size"]
                rotation_count = data["rotation_count"]
                error = data["error"]
                matrix = np.array(data["matrix"], dtype=np.float64)
                distortions = np.array(data["distortions"], dtype=np.float64)
                exposure = data["exposure"]
                grid_count = data["grid_count"]
                ignore = data["ignore"]
                verified_resolutions = data["verified_resolutions"]

                # update with extrinsics, though place anchor camera at origin
                if port == self.anchor:
                    translation = np.array([0, 0, 0], dtype=np.float64)
                    rotation = np.array(
                        [[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float64
                    )
                else:
                    anchored_pair = self.extrinsics.query(f"Secondary == {port}")
                    translation = anchored_pair.Translation.to_list()[0][:,0] # indexing in to avoid redundent dimensions
                    rotation = anchored_pair.Rotation.to_list()[0]

                    # testing out random ideas
                    # rotation = np.linalg.inv(rotation)

                cam_data = CameraData(
                    port,
                    size,
                    rotation_count,
                    error,
                    matrix,
                    distortions,
                    exposure,
                    grid_count,
                    ignore,
                    verified_resolutions,
                    translation,
                    rotation,
                )

                self.cameras[port] = cam_data

    def get_default_stereoextrinsics(self):

        stereoextrinsics = {}

        for key, params in self.config.items():
            if key.split("_")[0] == "stereo":
                port_A = int(key.split("_")[1])
                port_B = int(key.split("_")[2])

                pair = (port_A, port_B)
                rotation = np.array(params["rotation"], dtype=np.float64)
                translation = np.array(params["translation"], dtype=np.float64)
                transformation = get_transformation(rotation,translation)
                error = float(params["RMSE"])

                stereoextrinsics[pair] = { "Primary": port_A,
                                           "Secondary": port_B,
                                           "error": error,
                                           "Rotation": rotation,
                                           "Translation": translation,
                                           "Transformation": transformation
                                        }


                # # it will likely appear strange to make B the primary and A the secondary
                # # this is done because cv2.stereocalibrate returns R and t such that it is the
                # # position of the first camera relative to the second camera (which I find counter intuitive),
                # stereoextrinsics["Primary"].append(port_B)
                # stereoextrinsics["Secondary"].append(port_A)

                # stereoextrinsics["Rotation"].append(rotation)
                # stereoextrinsics["Translation"].append(translation)
                # stereoextrinsics["error"].append(error)

        # extrinsics = pd.DataFrame(extrinsics).sort_values("error")

        # # create an inverted version of these to determine best Anchor camera
        # inverted_chain = extrinsics.copy()
        # inverted_chain.Primary, inverted_chain.Secondary = (
        #     inverted_chain.Secondary,
        #     inverted_chain.Primary,
        # )
        
        # # I think that to get the rotation and translation from the other
        
        
        # # Mac....this might be what is causing the issues. 
        # inverted_chain.Translation = inverted_chain.Translation * -1
        # inverted_chain.Rotation = inverted_chain.Rotation.apply(np.linalg.inv)

        # daisy_chain_w_inverted = pd.concat([extrinsics, inverted_chain], axis=0)

        # all_pairs = extrinsics["Pair"].unique()

        # mean_error = (
        #     daisy_chain_w_inverted.filter(["Primary", "error"])
        #     .groupby("Primary")
        #     .agg("mean")
        #     .rename(columns={"error": "MeanError"})
        #     .sort_values("MeanError")
        # )

        # anchor_camera = int(
        #     mean_error.index[0]
        # )  # array anchored by camera with the lowest mean RMSE

        # daisy_chain_w_inverted = daisy_chain_w_inverted.merge(
        #     mean_error, how="left", on="Primary"
        # ).sort_values("MeanError")

        # daisy_chain_w_inverted.insert(
        #     4, "MeanError", daisy_chain_w_inverted.pop("MeanError")
        # )
        # daisy_chain_w_inverted.sort_values(["MeanError"])

        # # need to build an array of cameras in a common frame of reference a starting point for the calibration
        # # if one of the stereo pairs did not get calibrated, then some additional tricks will need to get
        # # deployed to make things work. But fortunately this is the simpler case now.
        # initial_array = daisy_chain_w_inverted[
        #     daisy_chain_w_inverted.Primary == anchor_camera
        # ]
        # initial_array = initial_array[
        #     ["Primary", "Secondary", "Rotation", "Translation"]
        # ]

        # # fix format of Primary/Secondary labels to be integers
        # initial_array[["Primary", "Secondary"]] = initial_array[
        #     ["Primary", "Secondary"]
        # ].apply(pd.to_numeric)

        # return initial_array, all_pairs, anchor_camera
        return stereoextrinsics

    def get_camera_array(self):
        return CameraArray(self.cameras)

def get_transformation(R, t):
    
    R_stack = np.vstack([R, np.array([0,0,0])])
    t_stack = np.vstack([t, np.array([1])])
    Tranformation = np.hstack([R_stack,t_stack])
    return Tranformation

if __name__ == "__main__":
# if True:
    
    from pyxy3d import __root__
    
    config_path = Path(__root__, "tests", "please work", "config.toml")
    array_builder = CameraArrayBuilder(config_path)
    camera_array = array_builder.get_camera_array()

    print("pause")
#%%