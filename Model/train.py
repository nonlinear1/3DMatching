import tensorflow as tf
import os
import numpy as np
from Model import TDDD_Net
from Data import dataset
# from Config import config
import pathlib as PH
from Data import dataset
from absl import flags
from absl import app
import shutil
# flags = tf.compat.v1.flags.Flag
FLAGS = flags.FLAGS

flags.DEFINE_integer('max_steps', 2000, 'Number of steps to run trainer.')
flags.DEFINE_float('non_match_M', 1, 'cut_off of non_match')


# def main(argv):

def main():
    # if FLAGS.debug:
    #     print('non-flag arguments:', argv)
    # if FLAGS.age is not None:
    #     pass
    data = dataset()
    data.x_y_split()

    steps = 30
    optimizer = tf.keras.optimizers.Adam(1e-4)
    from_scratch = True

    BASE_DIR = PH.Path(__file__).parent.parent
    MODEL_WEIGHTS_PATH = BASE_DIR.joinpath('Model').joinpath('Model_Weights')
    
    if from_scratch:
        shutil.rmtree(str(MODEL_WEIGHTS_PATH))

    if not os.path.exists(str(MODEL_WEIGHTS_PATH)):
        os.mkdir(str(MODEL_WEIGHTS_PATH))
    weights_path = str(MODEL_WEIGHTS_PATH.joinpath('ckpt'))



    # define Matching Net
    Model = TDDD_Net()
    Model.optimizer = optimizer
    Model.create_ckpt_manager(weights_path)
   
    for i in range(steps):

        #load correspondence and tsdf_volume
        tsdf_volume_batch_train,correspondence_batch_train,non_correspondence_train = data.generate_train_data_batch(1)
        Model.train_and_checkpoint(tsdf_volume_batch_train,correspondence_batch_train,non_match = non_correspondence_train,Non_March_Margin = 0.5,from_scratch = from_scratch)

        # Model.save_parameter(weights_path)
    
    #load model weights
    # Model.load_weights(weights_path)
    # tsdf_volume_batch,correspondence_batch = data.generate_data(5)
    # print(Model(tsdf_volume_batch))



if __name__ == '__main__':
    # app.run(main)
    main()