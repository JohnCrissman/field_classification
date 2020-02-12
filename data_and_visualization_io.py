import os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
from abc import abstractmethod


# todo: create a class for each type of chart


class Charts:
    def __init__(self):
        self.all_charts = []
        self.all_charts.append(ROCChart())
        # self.all_charts.append(AccuracyChart())
        # self.all_charts.append(LossChart())

    def update(self, history, index, validation_labels,
               validation_predicted_classification, prediction_probability):
        for each in self.all_charts:
            each.update(index, validation_labels, prediction_probability)

    # def finalize(self):
    #     for each in self.all_charts:
    #         each.finalize()


class Chart:
    def __init__(self, path):
        self.path = path
        self.file_extension = '.png'

    @abstractmethod
    def update(self, index, validation_labels, prediction_probability, history):
        pass

    @abstractmethod
    def create_chart(self, index):
        pass

    @abstractmethod
    def save(self, index):
        pass

    @abstractmethod
    def finalize(self):
        pass

class ROCChart(Chart):
    def __init__(self):
        path = os.path.join('graphs', 'mean_ROC')
        super().__init__(path)

        self.tpr = {}
        self.fpr = {}
        self.auc = {}

    def update(self, index, validation_labels, prediction_probability, history):
        """ Updates ROC plot after each fold, and saves to file system.

        Parameters:
        ------
        @ mean_fpr : float
        false positive rate (mean from all folds run so far)

        @ mean_tpr : float
        true postive rate (mean from all folds run so far)

        @ mean_auc : float
        area under ROC curve (mean from all folds run so far)

        @ std_auc : float
        standard deviation of AUC (mean from all folds run so far)

        Output:
        ------
        none

        Saves plot as `mean_ROC.png` in graphs folder.
        """
        # 1. Compute ROC curve and AUC
        latest_fpr, latest_tpr, thresholds = roc_curve(validation_labels, prediction_probability)
        latest_auc = roc_auc_score(validation_labels, prediction_probability)

        # 2. save new values to instance variables
        self.fpr[index] = latest_fpr
        self.tpr[index] = latest_tpr
        self.auc[index] = latest_auc

        # 3. Create and save ROC chart
        self.create_chart(index)
        self.save(index)

    def create_chart(self, index):
        plt.figure(3)
        plt.xlim([-0.05, 1.05])
        plt.ylim([-0.05, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve - Fold %i' % index)
        plt.plot([0, 1], [0, 1], linestyle='--', lw=2, color='r', label='Random', alpha=0.8)
        plt.plot(self.fpr[index], self.tpr[index], color='blue',
                 label='Mean ROC (AUC = %0.2f)' % (self.auc[index]),
                 lw=2, alpha=0.8)
        plt.legend(loc="lower right")

    def save(self, index):
        plt.savefig(self.path + str(index) + self.file_extension)
        plt.clf()

    def finalize(self):
        # TODO
        pass


class AccuracyChart(Chart):
    def __init__(self):
        path = os.path.join('graphs', 'accuracy')
        super().__init__(path)

        self.training = {}
        self.validation = {}

    def update(self, index, validation_labels, prediction_probability, history):
        """Create plot of training/validation accuracy, and save it to the file system."""
        plt.figure(1)
        self.training[index] = history.history['acc']
        self.validation[index] = history.history['val_acc']

        self.create_chart(index)
        self.save(index)

    def create_chart(self, index):
        plt.plot(self.training[index], label='Training Accuracy')
        plt.plot(self.validation[index], label='Validation Accuracy')
        plt.title('Accuracy - Fold %i' % index)
        plt.ylabel('Accuracy (%)')
        plt.xlabel('Epoch')
        plt.legend(loc='upper left')

    def save(self, index):
        plt.savefig(os.path.join('graphs', 'val_accuracy_' + str(index) + '.png'))
        plt.clf()

    def finalize(self):
        # TODO
        pass



class DataChartIO:
    def __init__(self):
        self.index = 0
        self.history = None
        self.results = pd.DataFrame()

    def update_values(self, history, index, tp, fn, fp, tn):
        self.history = history
        self.index = (index + 1)  # Change index from 0-based to 1-based

        num_epochs = len(history.history['loss'])
        # save the stats of the last epoch (i.e. end of the fold) to the results file
        self.results = self.results.append([[index + 1,
                                             history.history['loss'][num_epochs - 1],
                                             history.history['acc'][num_epochs - 1],
                                             history.history['val_loss'][num_epochs - 1],
                                             history.history['val_acc'][num_epochs - 1],
                                             tn, fp, fn, tp]])

    def plot_accuracy(self):
        """Create plot of training/validation accuracy, and save it to the file system."""
        plt.figure(1)
        plt.plot(self.history.history['acc'])
        plt.plot(self.history.history['val_acc'])
        plt.title('Training & Validation Accuracy for Fold ' + str(self.index))
        plt.ylabel('Accuracy (%)')
        plt.xlabel('Epoch')
        plt.legend(['Training', 'Validation'], loc='upper left')
        plt.savefig(os.path.join('graphs', 'val_accuracy_' + str(self.index) + '.png'))
        plt.clf()

    def plot_loss(self):
        """Create plot of training/validation loss, and save it to the file system."""
        plt.figure(2)
        plt.plot(self.history.history['loss'])
        plt.plot(self.history.history['val_loss'])
        plt.title('Training and Validation Loss for Fold' + str(self.index))
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['Training', 'Validation'], loc='upper left')
        plt.savefig(os.path.join('graphs', 'val_loss_' + str(self.index) + '.png'))
        plt.clf()

    def save_results_to_csv(self):
        self.results.rename(columns={0: 'Fold Number', 1: 'Training Loss', 2: 'Training Accuracy',
                                     3: 'Validation Loss', 4: 'Validation Accuracy',
                                     5: 'True Negatives', 6: 'False Positives', 7: 'False Negatives',
                                     8: 'True Positives'})
        self.results.to_csv(os.path.join('graphs', 'final_acc_loss.csv'), encoding='utf-8', index=False)

    def update_and_save_graphs(self, history, index, validation_labels,
                               validation_predicted_classification, validation_predicted_probability):
        tn, fp, fn, tp = confusion_matrix(validation_labels, validation_predicted_classification).ravel()
        self.update_values(history, index, tp, fn, fp, tn)
        self.plot_accuracy()
        self.plot_loss()
