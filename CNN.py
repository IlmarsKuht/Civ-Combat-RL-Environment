import torch
from torch import nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy
from gym import spaces

from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

class CustomCNN(BaseFeaturesExtractor):
    def __init__(self, observation_space: spaces.Dict):
        # Compute shape by doing one forward pass with a sample observation
        with torch.no_grad():
            cnn_test = nn.Sequential(
                nn.Conv2d(observation_space.spaces['observation'].shape[0], 32, kernel_size=3, stride=1, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2),
                nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=2),
                nn.Flatten(),
            )
            n_flatten = cnn_test(
                torch.as_tensor(observation_space.spaces['observation'].sample()[None]).float()
            ).shape[1]

        super(CustomCNN, self).__init__(observation_space, n_flatten)

        self.cnn = nn.Sequential(
            nn.Conv2d(observation_space.spaces['observation'].shape[0], 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
            nn.Flatten(),
        )

        #self.linear = nn.Sequential(nn.Linear(n_flatten, n_flatten), nn.ReLU())

    def forward(self, observations) -> torch.Tensor:
        x = self.cnn(observations['observation'])
        #x = self.linear(x)
        return {'observation': x, 'mask': observations['mask']}


class MaskedPolicyNet(nn.Module):
    def __init__(self, input_dim, output_dim, action_dim):
        super(MaskedPolicyNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, output_dim), 
            nn.ReLU()
        )
        self.masked_linear = MaskedLinear(output_dim, action_dim)

    def forward(self, input):
        x = self.net(input['observation'])
        return self.masked_linear(x, input['mask'])

class MaskedLinear(nn.Module):
    """
    Linear layer with input masking.
    """
    def __init__(self, input_dim, output_dim):
        super(MaskedLinear, self).__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, input: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        x =  self.linear(input)
        return x * mask


class CustomNetwork(nn.Module):
    def __init__(self, feature_dim: int, action_dim: int, last_layer_dim_pi: int = 100, last_layer_dim_vf: int = 64):
        super().__init__()

        self.latent_dim_pi = last_layer_dim_pi #needs to match the action dimensions
        self.latent_dim_vf = last_layer_dim_vf

        self.policy_net = MaskedPolicyNet(feature_dim, last_layer_dim_pi, action_dim)  # Masked output layer for policy

        self.value_net = nn.Sequential(
            nn.Linear(feature_dim, last_layer_dim_vf), 
            nn.ReLU(),
            nn.Linear(last_layer_dim_vf, 1)
        )

    def forward(self, obs: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        features = obs['observation']
        mask = obs.get('mask', None)  # Just in case there is no mask in obs
        return self.forward_actor(features, mask), self.forward_critic(features)

    def forward_actor(self, obs: Dict[str, torch.Tensor]) -> torch.Tensor:
        x = self.policy_net(obs)
        return x

    def forward_critic(self, obs: Dict[str, torch.Tensor]) -> torch.Tensor:
        x = self.value_net(obs['observation'])
        return x


class CustomActorCriticPolicy(ActorCriticPolicy):
    def __init__(self, observation_space, action_space, lr_schedule, *args, **kwargs):
        # Extract dimensions from action and observation spaces
        self.action_dim = action_space.n
        super().__init__(observation_space, action_space, lr_schedule, *args, **kwargs)

        # Replace transformer from default MultiInputProcessor to our custom one
        self.features_extractor = CustomCNN(observation_space)

        # Redefine mlp_extractor with the new input dimension
        self.features_dim = self.features_extractor.features_dim
        self._build_mlp_extractor()

   

    def extract_features(self, observation: torch.Tensor):
        return self.features_extractor(observation)
    
    def _build_mlp_extractor(self) -> None:
        self.mlp_extractor = CustomNetwork(self.features_dim, self.action_dim)
