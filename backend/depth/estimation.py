import matplotlib
import torch
import numpy as np

from depth.depth_anything_v2.dpt import DepthAnythingV2


class DepthEstimation:
    def __init__(self, encoder='vits', input_size=800, device='cuda'):
        self.device = device
        self.input_size = input_size
        self.cmap = matplotlib.colormaps.get_cmap('Spectral_r')

        model_configs = {
            'vits': {'encoder': 'vits', 'features': 64, 'out_channels': [48, 96, 192, 384]},
            'vitb': {'encoder': 'vitb', 'features': 128, 'out_channels': [96, 192, 384, 768]},
            'vitl': {'encoder': 'vitl', 'features': 256, 'out_channels': [256, 512, 1024, 1024]},
        }

        self.model = DepthAnythingV2(**model_configs[encoder])
        self.model.load_state_dict(torch.load(f'depth/checkpoints/depth_anything_v2_{encoder}.pth', map_location='cpu'))
        self.model = self.model.to(self.device).eval()

    def estimate_depth(self, frame):
        with torch.no_grad():
            depth = self.model.infer_image(frame, self.input_size)

        depth = (depth - depth.min()) / (depth.max() - depth.min()) * 255.0
        return depth.astype(np.uint8)

    def visualize_depth(self, depth, grayscale):
        if grayscale:
            return np.repeat(depth[..., np.newaxis], 3, axis=-1)
        return (self.cmap(depth)[:, :, :3] * 255)[:, :, ::-1].astype(np.uint8)
