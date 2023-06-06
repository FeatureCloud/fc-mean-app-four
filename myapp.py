"""
Tips:
1. Do not rename the states!
2. Return values of 'run' method will be discarded!
3. Do not define any arguments for run method!
4. Do not rename predefined attributes in classes
5. Do not use predefined attributes in classes for unrelated purposes
"""

import utils
import pandas as pd
import numpy as np

APP_NAME = "fc_example_config"


class MyApp(utils.FeatureCLoudApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.train_set = None
        self.test_set = None
        self.round = 1
        self.global_parameters = None

    def load_data(self):
        print(f"{self.input_root_dir}/{self.config['local_dataset']['train']}")
        self.train_set = pd.read_csv(f"{self.input_root_dir}/{self.config['local_dataset']['train']}",
                                     sep=self.config['local_dataset']['detail']['sep'])
        self.test_set = pd.read_csv(f"{self.input_root_dir}/{self.config['local_dataset']['test']}",
                                    sep=self.config['local_dataset']['detail']['sep'])
        # nothing to share
        return None

    def local_training(self, global_parameters):
        print(self.round)
        if self.round == 1:
            self.round += 1
            local_mean = [np.mean(self.train_set['AGE'].values), np.mean(self.test_set['AGE'].values)]
            local_var = [np.var(self.train_set['AGE'].values), np.var(self.test_set['AGE'].values)]
            return [local_mean, local_var]
        print(self.round, global_parameters[0])
        self.last_round = global_parameters[1]
        if self.last_round:
            (self.train_mean, self.test_mean), (self.train_var, self.test_var) = global_parameters[0]

    def global_aggregation(self, local_parameters):
        last_round = True
        print("G", local_parameters)
        global_params = np.mean(local_parameters, axis=0)
        return [global_params, last_round]

    def write_results(self):
        normal_train_set = (self.train_set['AGE'] - self.train_mean) / self.train_var
        normal_test_set = (self.test_set['AGE'] - self.test_mean) / self.test_var
        normal_train_set.to_csv(f"{self.output_root_dir}/{self.config['result']['normal_trainset']}",
                                sep=self.config['result']['detail']['sep'])
        normal_test_set.to_csv(f"{self.output_root_dir}/{self.config['result']['normal_testset']}",
                               sep=self.config['result']['detail']['sep'])

    def centralized(self):
        pass
