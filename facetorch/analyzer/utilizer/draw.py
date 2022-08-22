import torch
import torchvision
import numpy as np
from codetiming import Timer
from facetorch.base import BaseUtilizer
from facetorch.datastruct import ImageData
from facetorch.logger import LoggerJsonFile
from torchvision import transforms
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

logger = LoggerJsonFile().logger


class BoxDrawer(BaseUtilizer):
    def __init__(
        self,
        transform: transforms.Compose,
        device: torch.device,
        optimize_transform: bool,
        colors: str,
        line_width: int,
    ):
        """Initializes the BoxDrawer class. This class is used to draw the face boxes to the image tensor.

        Args:
            transform (Compose): Composed Torch transform object.
            device (torch.device): Torch device cpu or cuda object.
            optimize_transform (bool): Whether to optimize the transform.
            colors (str): Color of the boxes.
            line_width (int): Line width of the boxes.

        """
        super().__init__(transform, device, optimize_transform)
        self.colors = colors
        self.line_width = line_width

    @Timer("BoxDrawer.run", "{name}: {milliseconds:.2f} ms", logger.debug)
    def run(self, data: ImageData) -> ImageData:
        """Draws face boxes to the image tensor.

        Args:
            data (ImageData): ImageData object containing the image tensor and face locations.
        Returns:
            ImageData: ImageData object
        """
        data = self.draw_boxes(data)

        return data

    def draw_boxes(self, data: ImageData) -> ImageData:
        """Draws face boxes to the image tensor.

        Args:
            data (ImageData): ImageData object containing the image tensor, detections, and faces.

        Returns:
            None
        """
        loc_tensor = data.aggregate_loc_tensor()
        labels = [str(face.indx) for face in data.faces]
        data.img = torchvision.utils.draw_bounding_boxes(
            image=data.img,
            boxes=loc_tensor,
            labels=labels,
            colors="green",
            width=3,
        )

        return data


class LandmarkDrawer(BaseUtilizer):
    def __init__(
        self,
        transform: transforms.Compose,
        device: torch.device,
        optimize_transform: bool,
        marker: str,
        markersize: float,
        alpha: float,
        line_width: float,
        color: str,
        markeredgecolor: str,
    ):
        """Initializes the LandmarkDrawer class. This class is used to draw the 3D face landmarks to the image tensor.

        Args:
            transform (Compose): Composed Torch transform object.
            device (torch.device): Torch device cpu or cuda object.
            optimize_transform (bool): Whether to optimize the transform.
            marker (str): Marker type.
            markersize (float): Marker size.
            alpha (float): Marker alpha.
            line_width (float): Line width.
            color (str): Marker color.
            markeredgecolor (str): Marker edge color.

        """
        super().__init__(transform, device, optimize_transform)
        self.marker = marker
        self.markersize = markersize
        self.alpha = alpha
        self.line_width = line_width
        self.color = color
        self.markeredgecolor = markeredgecolor

    @Timer("LandmarkDrawer.run", "{name}: {milliseconds:.2f} ms", logger.debug)
    def run(self, data: ImageData) -> ImageData:
        """Draws 3D face landmarks to the image tensor.

        Args:
            data (ImageData): ImageData object containing the image tensor and 3D face landmarks.
        Returns:
            ImageData: ImageData object
        """
        data = self.draw_landmarks(data)

        return data

    def draw_landmarks(self, data: ImageData) -> ImageData:
        """Draws 3D face landmarks to the image tensor.

        Args:
            data (ImageData): ImageData object containing the image tensor, 3D face landmarks, and faces.

        Returns:
            (ImageData): ImageData object
        """
        img = data.img.cpu().numpy().transpose(1, 2, 0)
        pts = [face.preds["align"].other["lmk3d"].cpu() for face in data.faces]

        if len(pts) > 0:

            height, width = img.shape[:2]
            fig = plt.figure(figsize=(height / 100, width / 100))
            plt.imshow(img)
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            plt.axis("off")

            if not type(pts) in [tuple, list]:
                pts = [pts]
            for i in range(len(pts)):

                nums = [0, 17, 22, 27, 31, 36, 42, 48, 60, 68]

                # close eyes and mouths
                plot_close = lambda i1, i2: plt.plot(
                    [pts[i][0, i1], pts[i][0, i2]],
                    [pts[i][1, i1], pts[i][1, i2]],
                    color=self.color,
                    lw=self.line_width,
                    alpha=self.alpha - 0.1,
                )
                plot_close(41, 36)
                plot_close(47, 42)
                plot_close(59, 48)
                plot_close(67, 60)

                for ind in range(len(nums) - 1):
                    l, r = nums[ind], nums[ind + 1]
                    plt.plot(
                        pts[i][0, l:r],
                        pts[i][1, l:r],
                        color=self.color,
                        lw=self.line_width,
                        alpha=self.alpha - 0.1,
                    )

                    plt.plot(
                        pts[i][0, l:r],
                        pts[i][1, l:r],
                        marker=self.marker,
                        linestyle="None",
                        markersize=self.markersize,
                        color=self.color,
                        markeredgecolor=self.markeredgecolor,
                        alpha=self.alpha,
                    )

            canvas = FigureCanvas(fig)
            canvas.draw()
            img_np = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
            img_np = img_np.reshape(canvas.get_width_height()[::-1] + (3,))
            img_np = img_np.transpose(2, 0, 1)
            data.img = torch.from_numpy(np.array(img_np))

            plt.close()

        return data
