from stable_baselines3.common.env_checker import check_env

from sb3_contrib.common.maskable.policies import MaskableActorCriticCnnPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from stable_baselines3 import PPO

import gymnasium as gym

import numpy as np

from env import Civ6CombatEnv

def mask_fn(env: gym.Env) -> np.ndarray:
    return env.valid_action_mask()

def main():
    
    env = Civ6CombatEnv(render_mode="human")
    env = ActionMasker(env, mask_fn)
    model = PPO("CnnPolicy", env, verbose=True, policy_kwargs={'normalize_images': False})
    # model.learn()
    #check_env(env)
    observation, info = env.reset()
    while True:
        valid_action_mask = env.valid_action_mask()
        env.step(model.predict(observation, action_masks=valid_action_mask))
         


if __name__ == "__main__":
    main()
