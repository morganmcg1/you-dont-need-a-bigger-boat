import os
import json
import wandb
from wandb.keras import WandbCallback
import neptune.new as neptune
from neptune.new.integrations.tensorflow_keras import NeptuneCallback

def get_filename(path):
    return os.path.splitext(os.path.basename(path))[0]


def return_json_file_content(file_name: str):
    """
    Load data from a json file

    :param file_name: name of the file
    :return: the data content extracted from the file
    """
    with open(file_name) as json_file:
        data = json.load(json_file)

    return data

class ExperimentTracker:
    def __init__(self, tracker_name, current_run_id, config, s3_path):
        self.name = tracker_name
        self.current_run_id = current_run_id
        self.config = config
        self.s3_path = s3_path

    def get_tracker_callback(self):
        if self.name == 'wandb':

            # Check if environment variables are empty
            assert os.getenv('WANDB_API_KEY')
            assert os.getenv('WANDB_ENTITY')
            
            # Initialize wandb
            # init API reference: https://docs.wandb.ai/ref/python/init
            self.wandb_run = wandb.init(entity = os.getenv('WANDB_ENTITY'),
                   project="cart-abandonment",
                   id=self.current_run_id,
                   config=self.config,
                   resume='allow',
                   reinit=True)
                
            return WandbCallback()
        elif self.name == 'neptune':

            # Check if environment variables are empty
            assert os.getenv('NEPTUNE_PROJECT')
            assert os.getenv('NEPTUNE_API_TOKEN')

            # Initialize neptune
            # init API reference: https://docs.neptune.ai/api-reference/neptune#.init
            self.neptune_run = neptune.init(
                name="cart-abandonment"
            )

            # Log Metaflow run ID and hyperparameters
            self.neptune_run["metaflow_run_id"] = self.current_run_id
            self.neptune_run["parameters"] = self.config

            # Log the metaflow config
            self.neptune_run["metaflow_run_id"] = self.current_run_id
            self.neptune_run["hyper-parameters"] = self.config

            # Log data version
            self.neptune_run["artifacts/dataset"].track_files(self.s3_path)

            return NeptuneCallback(run=self.neptune_run)
        else:
            raise ValueError("Invalid tracker name supported values are 'wandb' and 'neptune'")

    def stop_tracker(self):
        if self.name == 'wandb':
            self.wandb_run.finish()
        elif self.name == 'neptune':
            self.neptune_run.stop()