import os
import pandas as pd
from sklearn.metrics import roc_curve, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


class Charts:
    def __init__(self, n_folds: int):
        self.folder_name = 'graphs'
        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
        self.all_charts = []
        self.all_charts.append(ROCChart(self.folder_name))
        self.all_charts.append(AccuracyChart(self.folder_name))
        self.all_charts.append(LossChart(self.folder_name))
        self.all_charts.append(ConfusionMatrix(self.folder_name))

        self.n_folds = n_folds

    def update(self, history, index, validation_labels, prediction_probability, class_labels) -> None:
        for each in self.all_charts:
            each.update(index, validation_labels, prediction_probability, history, class_labels)
            each.save(index)

    def finalize(self) -> None:
        results = pd.DataFrame()
        results['Fold'] = list(range(1, self.n_folds + 1))
        for each in self.all_charts:
            each.finalize(results)
        results.to_csv(os.path.join(self.folder_name, 'final_data.csv'), encoding='utf-8', index=False)


class Chart(ABC):
    def __init__(self, base_filename, folder_name):
        self.path = os.path.join(folder_name, base_filename)
        self.file_extension = '.png'

    @abstractmethod
    def update(self, index, validation_labels, prediction_probability, history, class_labels) -> None:
        pass

    def save(self, index) -> None:
        plt.savefig(self.path + str(index).zfill(2) + self.file_extension)
        plt.clf()

    @abstractmethod
    def finalize(self, results) -> None:
        pass


class ROCChart(Chart):
    def __init__(self, folder_name):
        base_filename = 'mean_ROC'
        super().__init__(base_filename, folder_name)

        self.tpr = {}
        self.fpr = {}
        self.auc = {}

    def update(self, index, validation_labels, prediction_probability, history, class_labels) -> None:
        # 1. Compute ROC curve and AUC
        latest_fpr, latest_tpr, thresholds = roc_curve(validation_labels, prediction_probability)
        latest_auc = roc_auc_score(validation_labels, prediction_probability)

        # 2. save new values to instance variables
        self.fpr[index] = latest_fpr
        self.tpr[index] = latest_tpr
        self.auc[index] = latest_auc

        # 3. Create and save ROC chart
        self.create_chart(index)

    def create_chart(self, index) -> None:
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

    def finalize(self, results) -> None:
        results['auc'] = self.auc.values()


class AccuracyChart(Chart):
    def __init__(self, folder_name):
        base_filename = 'accuracy'
        super().__init__(base_filename, folder_name)

        self.training = {}
        self.validation = {}

    def update(self, index, validation_labels, prediction_probability, history, class_labels) -> None:
        """Create plot of training/validation accuracy, and save it to the file system."""
        self.training[index] = history.history['acc'][-1]
        self.validation[index] = history.history['val_acc'][-1]
        self.create_chart(index, history)

    def create_chart(self, index, history) -> None:
        plt.figure(1)
        plt.plot(history.history['acc'], label='Training Accuracy')
        plt.plot(history.history['val_acc'], label='Validation Accuracy')
        plt.title('Accuracy - Fold %i' % index)
        plt.ylabel('Accuracy (%)')
        plt.xlabel('Epoch')
        plt.legend(loc='upper left')

    def finalize(self, results) -> None:
        results['training_acc'] = self.training.values()
        results['validation_acc'] = self.validation.values()


class LossChart(Chart):
    def __init__(self, folder_name):
        base_filename = 'loss'
        super().__init__(base_filename, folder_name)

        self.training = {}
        self.validation = {}

    def update(self, index, validation_labels, prediction_probability, history, class_labels) -> None:
        self.training[index] = history.history['loss'][-1]
        self.validation[index] = history.history['val_loss'][-1]
        self.create_chart(index, history)

    def create_chart(self, index, history) -> None:
        plt.figure(2)
        plt.plot(history.history['loss'], label='Training Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title('Loss - Fold %i' % index)
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(loc='upper left')

    def finalize(self, results) -> None:
        results['training_loss'] = self.training.values()
        results['validation_loss'] = self.validation.values()


class ConfusionMatrix(Chart):
    def __init__(self, folder_name):
        base_filename = 'confusion_matrix'
        super().__init__(base_filename, folder_name)

        self.tp = {}
        self.fn = {}
        self.fp = {}
        self.tn = {}

    def update(self, index, validation_labels, prediction_probability, history, class_labels) -> None:
        # Determine the class of an image, if >= 0.4999 = class 0, otherwise class 1
        validation_predicted_classification = [round(a + 0.0001) for a in prediction_probability]
        cm = confusion_matrix(validation_labels, validation_predicted_classification)

        new_tn, new_fp, new_fn, new_tp = cm.ravel()
        self.tp[index] = new_tp
        self.fn[index] = new_fn
        self.fp[index] = new_fp
        self.tn[index] = new_tn

        labels = [class_labels[0], class_labels[1]]
        self.create_chart(index, cm, labels)

    def create_chart(self, index, cm, labels) -> None:
        fig = plt.figure(4)
        ax = fig.add_subplot(1, 1, 1)
        cax = ax.matshow(cm)  # todo: figure out what this is about
        plt.title('Confusion Matrix - Fold %i' % index)
        fig.colorbar(cax)
        ax.set_xticklabels([''] + labels)
        ax.set_yticklabels([''] + labels)
        plt.xlabel('Predicted')
        plt.ylabel('Actual')

    def finalize(self, results) -> None:
        results['tp'] = self.tp.values()
        results['fn'] = self.fn.values()
        results['fp'] = self.fp.values()
        results['tn'] = self.tn.values()
