import os
import argparse
import random
import numpy as np
import tensorflow as tf
from sklearn.model_selection import StratifiedKFold
import matplotlib
from labeled_images.labeledimages import LabeledImages
from models.smithsonian import SmithsonianModel
from data_and_visualization_io import Charts
from model_training import ModelTrainer
from timer import Timer
import warnings

matplotlib.use('Agg')  # required when running on server


def main() -> None:
    timer = Timer('Model training')
    class_labels, images, architecture, trainer, n_folds, charts = setup()

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=SEED)
    for index, (training_idx_list, validation_idx_list) in enumerate(skf.split(images.features, images.labels)):
        # set up this model run
        architecture.reset_model()
        training_set = images.subset(training_idx_list)
        validation_set = images.subset(validation_idx_list)

        # train model
        history = trainer.train_new_model_and_save(architecture, training_set, validation_set, index, n_folds)

        # validate newly created model
        validation_predicted_probability = architecture.model.predict_proba(validation_set[0])[:, 1]
        charts.update(history, index, validation_set[1], validation_predicted_probability, class_labels)

    finalize(charts, class_labels, timer)


def setup():
    image_folders, class_labels, img_size, color_mode, lr, n_folds, n_epochs, batch_size = get_arguments()

    trainer = ModelTrainer(n_epochs, batch_size)

    # Load in images and shuffle order
    images = LabeledImages(image_folders, color_mode, SEED)
    architecture = SmithsonianModel(SEED, lr)

    charts = Charts(n_folds)

    return class_labels, images, architecture, trainer, n_folds, charts


def get_arguments():
    args = initialize_argparse()
    image_folders, class_labels = validate_image_folders(args)
    img_size = validate_image_size(args)
    lr = validate_learning_rate(args)
    color_mode = False if args.bw else True
    n_folds = validate_n_folds(args)
    n_epochs = validate_n_epochs(args)
    batch_size = validate_batch_size(args)
    return image_folders, class_labels, img_size, color_mode, lr, n_folds, n_epochs, batch_size


def initialize_argparse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        'Create and train CNNs for binary classification of images, using cross-fold validation.')
    # image arguments
    parser.add_argument('c1', help='Directory name containing images in class 1.')
    parser.add_argument('c2', help='Directory name containing images in class 2.')
    parser.add_argument('-s', '--img_size', type=int, default=256,
                        help='Image dimension in pixels (must be square).')
    color_mode_group = parser.add_mutually_exclusive_group()
    color_mode_group.add_argument('-color', action='store_true', help='(default) Images are in RGB color mode.')
    color_mode_group.add_argument('-bw', action='store_true', help='Images are in grayscale color mode.')

    # model creation argument
    parser.add_argument('-lr', '--learning_rate', type=float, default=0.0001, help='Learning rate for training.')

    # training run arguments
    parser.add_argument('-f', '--n_folds', type=int, default=10,
                        help='Number of folds (minimum 2) for cross validation.')
    parser.add_argument('-e', '--n_epochs', type=int, default=25, help='Number of epochs.')
    parser.add_argument('-b', '--batch_size', type=int, default=64, help='Batch size for training.')

    return parser.parse_args()


def validate_image_folders(args: argparse.Namespace) -> tuple:
    if not os.path.isdir(args.c1):
        raise NotADirectoryError('%s is not a valid directory path.' % args.c1)
    if not os.path.isdir(args.c2):
        raise NotADirectoryError('%s is not a valid directory path.' % args.c2)
    image_folders = (args.c1, args.c2)

    c1 = args.c1.strip(os.path.sep)
    c2 = args.c2.strip(os.path.sep)
    c1 = c1.split(os.path.sep)[c1.count(os.path.sep)]
    c2 = c2.split(os.path.sep)[c2.count(os.path.sep)]
    class_labels = (c1, c2)

    return image_folders, class_labels


def validate_image_size(args: argparse.Namespace) -> int:
    img_size = args.img_size
    if not img_size >= 4:
        raise ValueError('%i is not a valid image dimension (in pixels). Must be >= 4.' % img_size)
    return img_size


def validate_learning_rate(args: argparse.Namespace) -> float:
    lr = args.learning_rate
    if not 0 < lr <= 1:
        raise ValueError('%f.6 is not a valid learning rate. Must be in range 0 (exclusive) to 1 (inclusive).' % lr)
    return lr


def validate_n_folds(args: argparse.Namespace) -> int:
    n_folds = args.n_folds
    if not n_folds >= 2:
        raise ValueError('%i is not a valid number of folds. Must be >= 2.' % n_folds)

    return n_folds


def validate_n_epochs(args: argparse.Namespace) -> int:
    n_epochs = args.n_epochs
    # if not n_epochs >= 10:
    #     raise ValueError('%i is not a valid number of epochs. Must be >= 10.)' % n_epochs)
    return n_epochs


def validate_batch_size(args: argparse.Namespace) -> int:
    batch_size = args.batch_size
    if not batch_size >= 2:
        raise ValueError('%i is not a valid batch size. Must be >= 2.' % batch_size)
    return batch_size


def finalize(charts, class_labels, timer):
    charts.finalize()
    # end
    print('class 1: ' + class_labels[0] + ', class 2: ' + class_labels[1])
    timer.stop()
    timer.results()


if __name__ == '__main__':
    # set up random seeds
    SEED = 1
    np.random.seed(SEED)
    tf.compat.v1.random.set_random_seed(SEED)
    random.seed(SEED)

    warnings.filterwarnings('ignore', category=DeprecationWarning)

    main()
