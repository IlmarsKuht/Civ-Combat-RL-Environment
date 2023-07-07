from stable_baselines3.common.env_checker import check_env

from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3 import PPO

import gymnasium as gym

import numpy as np

from env import Civ6CombatEnv

from CNN import CustomActorCriticPolicy, CustomCNN

import torch

def mask_fn(env: gym.Env) -> np.ndarray:
    return env.valid_action_mask()

def main():
    env = Civ6CombatEnv(render_mode="human")
    policy_kwargs = dict(
        features_extractor_class=CustomCNN,
       
    )
    model = PPO(CustomActorCriticPolicy, env, verbose=True, policy_kwargs=policy_kwargs)
    
    # model.learn()
    #check_env(env)
    observation, info = env.reset()
    while True:
        env.step(model.predict(observation))
         


if __name__ == "__main__":
    main()
