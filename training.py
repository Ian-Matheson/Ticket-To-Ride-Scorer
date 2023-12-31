import torch
import numpy as np
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import Adam
import matplotlib.pyplot as plt
from torchvision import transforms
from torch.utils.data import random_split
import time
from scipy.ndimage import rotate

import os
import cv2
import matplotlib.pyplot as plt


class TrainsCNN(nn.Module):
    """Convolutional Neural Network for train spot image classification."""

    def __init__(self):
        """Initialize the CNN model."""
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(3, 15, kernel_size=3),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(21960, 512),
            nn.ReLU(),
            nn.Linear(512, 6)
        )

    def forward(self, x):
        """Forward pass through the CNN model."""
        return self.model(x)


class StationsCNN(nn.Module):
    """Convolutional Neural Network for station spot image classification."""

    def __init__(self):
        """Initialize the CNN model."""
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(3, 15, kernel_size=3),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(36015, 512),
            nn.ReLU(),
            nn.Linear(512, 6)
        )

    def forward(self, x):
        """Forward pass through the CNN model."""
        return self.model(x)


class T2RDataset(Dataset):
    """Custom dataset class for Train/Station Spot images."""

    def __init__(self, root_dir, transform, dtype):
        """
        Initialize T2RDataset.

        Loads data from the specified root directory and sets up necessary attributes.

        Args:
        - root_dir (str): Root directory containing image folders.
        - transform (callable): Optional transform to be applied to images.
        - dtype (str): Type of data ('station' or 'train').
        """
        self.root_dir = root_dir
        self.data = []
        self.targets = []
        self.transform = transform
        self.color_mapping = {'blue': 1, 'black': 2, 'green': 3, 'red': 4, 'yellow': 5}

        self.load_data(dtype)

    def load_data(self, dtype):
        """
        Load images from the specified data type folder.

        Args:
        - dtype (str): Type of data ('station' or 'train').
        """
        big_folder = self.root_dir
        for folder in os.listdir(big_folder):
            if folder != '.DS_Store':
                folder_path = os.path.join(big_folder, folder)
                for filename in os.listdir(folder_path):
                    if filename != '.DS_Store':
                        img_path = os.path.join(folder_path, filename)
                        original_image = cv2.imread(img_path)
                        
                        if dtype == 'station':
                            self.load_station_image(original_image, filename)
                        elif dtype == 'train':
                            self.load_train_image(original_image, filename)


    def load_station_image(self, original_image, filename):
        """
        Load and augment station images to increase training data.

        Args:
        - original_image: Original station image.
        - filename (str): Image filename.
        """
        desired_height, desired_width = 100, 100
        resized_image = cv2.resize(original_image, (desired_width, desired_height))
        
        for rotation_angle in [0, 90, 180, 270]:
            rotated_image = rotate(resized_image, rotation_angle, reshape=False)
            label = filename.split('-')[0]
            self.data.append(rotated_image)
            self.targets.append(self.color_mapping.get(label, 0))

    def load_train_image(self, original_image, filename):
        """
        Load and process train images.

        Args:
        - original_image: Original train image.
        - filename (str): Image filename.
        """
        desired_height, desired_width = 50, 125
        image = cv2.resize(original_image, (desired_width, desired_height))
        label = filename.split('-')[0]
        self.data.append(image)
        self.targets.append(self.color_mapping.get(label, 0))


    def split_data(self, train_percentage=0.7):
        """
        Split the dataset into training and testing sets.

        Args:
        - train_percentage (float): Percentage of data to be used for training.

        Returns:
        - train_dataset (Subset): Subset for training.
        - test_dataset (Subset): Subset for testing.
        """
        dataset_size = len(self.data)
        train_size = int(train_percentage * dataset_size)
        test_size = dataset_size - train_size
        train_dataset, test_dataset = random_split(self, [train_size, test_size])
        return train_dataset, test_dataset
    
    def __getitem__(self, idx):
        """
        Get image and target at the specified index.

        Args:
        - idx (int): Index of the data.

        Returns:
        - img: Image at the specified index.
        - target: Target label for the image.
        """
        img, target = self.data[idx], self.targets[idx]

        if self.transform:
            img = self.transform(img)

        return img, target

    def __len__(self):
        """
        Get the total number of images in the dataset.

        Returns:
        - int: Total number of images in the dataset.
        """
        return len(self.data)


class Classifier:
    """Simple image classifier using a PyTorch model."""

    def __init__(self, model, root_dir, dtype, batch_size=32, learning_rate=1e-3, num_epochs=10):
        """
        Initialize the Classifier.

        Sets up the model, optimizer, loss function, and data loaders.

        Args:
        - model (nn.Module): PyTorch model for classification.
        - root_dir (str): Root directory containing image folders.
        - dtype (str): Type of data ('station' or 'train').
        - batch_size (int): Batch size for training and testing. Default is 32.
        - learning_rate (float): Learning rate for optimization. Default is 1e-3.
        - num_epochs (int): Number of training epochs. Default is 10.
        """
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.root_dir = root_dir
        self.dtype = dtype
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        self.model = model.to(self.device)
        self.optimizer = Adam(self.model.parameters(), lr=self.learning_rate)
        self.loss_func = nn.CrossEntropyLoss()

        self.train_dataset, self.train_loader, self.test_dataset, self.test_loader = self.load_data()

    def load_data(self):
        """
        Load and split the dataset into training and testing sets.

        Returns:
        - train_dataset (Subset): Training dataset.
        - train_loader (DataLoader): Training data loader.
        - test_dataset (Subset): Testing dataset.
        - test_loader (DataLoader): Testing data loader.
        """
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])

        custom_dataset = T2RDataset(self.root_dir, transform=transform, dtype=self.dtype)
        train_dataset, test_dataset = custom_dataset.split_data()
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=self.batch_size, shuffle=True)

        return train_dataset, train_loader, test_dataset, test_loader

    def train_batch(self, x, y):
        """
        Train the model on a batch of data.

        Args:
        - x: Input data.
        - y: Target labels.

        Returns:
        - float: Batch loss value.
        """
        self.model.train()
        self.optimizer.zero_grad()
        batch_loss = self.loss_func(self.model(x), y)
        batch_loss.backward()
        self.optimizer.step()
        return batch_loss.item()

    @torch.no_grad()
    def accuracy(self, x, y):
        """
        Calculate the accuracy of the model on a batch of data.

        Args:
        - x: Input data.
        - y: Target labels.

        Returns:
        - float: Batch accuracy.
        """
        self.model.eval()
        prediction = self.model(x)
        argmaxes = prediction.argmax(dim=1)
        s = torch.sum((argmaxes == y).float()) / len(y)
        return s.item()


    def train(self):
        """
        Train the model for a specified number of epochs.

        Prints and plots training and testing results.
        """
        train_losses, train_accuracies, test_losses, test_accuracies, time_per_epoch = [], [], [], [], []
        
        for epoch in range(self.num_epochs):
            print(f"Running epoch {epoch + 1} of {self.num_epochs}")
            start_time = time.time()

            epoch_losses, epoch_accuracies = [], []

            for batch in self.train_loader:
                x, y = batch
                batch_loss = self.train_batch(x, y)
                epoch_losses.append(batch_loss)
                batch_acc = self.accuracy(x, y)
                epoch_accuracies.append(batch_acc)

            train_losses.append(np.mean(epoch_losses))
            train_accuracies.append(np.mean(epoch_accuracies))

            epoch_test_accuracies, epoch_test_losses = [], []
            for ix, batch in enumerate(iter(self.test_loader)):
                x, y = batch
                test_loss = self.train_batch(x, y)
                test_acc = self.accuracy(x, y)
                epoch_test_accuracies.append(test_acc)
                epoch_test_losses.append(test_loss)

            test_losses.append(np.mean(epoch_test_losses))
            test_accuracies.append(np.mean(epoch_test_accuracies))

            end_time = time.time()
            time_per_epoch.append(end_time - start_time)

        results = (train_losses, train_accuracies, test_losses, test_accuracies, time_per_epoch)
        self.plot_results(results)
        print(train_accuracies)
        print(test_accuracies)
    
    @torch.no_grad()
    def visualize_predictions(self, loader, num_images=5):
        """
        Visualize model predictions on a subset of the dataset.

        Args:
        - loader (DataLoader): Data loader for visualization.
        - num_images (int): Number of images to visualize. Default is 5.
        """
        self.model.eval()

        images, labels = next(iter(loader))

        images, labels = images.to(self.device), labels.to(self.device)

        outputs = self.model(images)
        _, predicted = torch.max(outputs, 1)

        for i in range(num_images):
            image, label, prediction = images[i], labels[i], predicted[i]
            image_np = image.cpu().numpy().transpose((1, 2, 0))  # Assuming the tensor is in CHW format
            image_np = (image_np - image_np.min()) / (image_np.max() - image_np.min())

            plt.imshow(image_np)
            plt.title(f'Actual label: {label.item()}, Predicted label: {prediction.item()}')
            plt.show()

    def save_model(self, save_path):
        """
        Save the trained model to a file.

        Args:
        - save_path (str): File path to save the model.
        """
        torch.save(self.model.state_dict(), save_path)
        print(f"Model saved at: {save_path}")

    def plot_results(self, results):
        """
        Plot training and testing results.

        Args:
            results (tuple): Tuple of training and testing results.
        """
        train_losses, train_accuracies, test_losses, test_accuracies, time_per_epoch = results
        plt.figure(figsize=(15, 5))

        plt.subplot(131)
        plt.title('Training and Testing Loss value over epochs')
        plt.plot(np.arange(10) + 1, train_losses, label='Training Loss')
        plt.plot(np.arange(10) + 1, test_losses, label='Test Loss')
        plt.legend()

        plt.subplot(132)
        plt.title('Train Accuracy value over epochs')
        plt.plot(np.arange(10) + 1, train_accuracies, label='Training Accuracy')
        plt.plot(np.arange(10) + 1, test_accuracies, label='Test Accuracy')
        plt.legend()

        plt.subplot(133)
        plt.title('Time in Seconds per Epoch')
        plt.plot(np.arange(10) + 1, time_per_epoch)

        plt.show()
    

def train_models():
    """
    Train and save models for station and train spot classification.

    Creates instances of StationsCNN and TrainsCNN models, trains them using the Classifier,
    visualizes predictions, and saves the trained models.

    """
    station_cnn_model = StationsCNN()
    station_dir = 'test_train_data/station_data'
    station_cnn_classifier = Classifier(station_cnn_model.model, station_dir, 'station')
    station_cnn_classifier.train()
    station_cnn_classifier.visualize_predictions(station_cnn_classifier.test_loader)
    
    station_path = 'models/station_spot_classifiers/trained_station_model_07.pth'
    station_cnn_classifier.save_model(station_path)

    train_cnn_model = TrainsCNN()
    train_dir = 'test_train_data/train_data'
    train_cnn_classifier = Classifier(train_cnn_model.model, train_dir, 'train')
    train_cnn_classifier.train()
    train_cnn_classifier.visualize_predictions(train_cnn_classifier.test_loader)
    
    train_path = 'models/train_spot_classifiers/trained_train_model_08.pth'
    train_cnn_classifier.save_model(train_path)

    
if __name__ == "__main__":
    train_models()