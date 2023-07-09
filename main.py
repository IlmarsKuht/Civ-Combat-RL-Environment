from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO

import torch

from env import Civ6CombatEnv

from CNN import CustomCNN


def main():
    load_model=False
    env = Civ6CombatEnv(max_steps=100, render_mode=None)
    if load_model:
        model = PPO.load("./models/civ6_model")
        model.set_env(env)
    else:
        policy_kwargs = dict(
            features_extractor_class=CustomCNN,
            activation_fn=torch.nn.ReLU,
            net_arch=dict(pi=[128, 128], vf=[128, 128])
        )
        model = PPO("CnnPolicy", env, ent_coef=0.01, verbose=True, use_sde=True, tensorboard_log='./logs', policy_kwargs=policy_kwargs)
    model.learn(total_timesteps=500000, progress_bar=True)
    model.save("./models/civ6_model")
    check_env(env)
    env = Civ6CombatEnv(max_steps=100, render_mode="human")
    policy_kwargs = dict(
            features_extractor_class=CustomCNN,
            # activation_fn=torch.nn.ReLU,
            # net_arch=dict(pi=[128, 128, 128], vf=[128, 128, 128])
        )
    model = PPO("CnnPolicy", env, verbose=True, policy_kwargs=policy_kwargs)
    observation, info = env.reset()
    while True:
        actions, _ = model.predict(observation)
        observation, reward, terminated, truncated, info = env.step(actions)
        if terminated or truncated:
            env.reset()

if __name__ == "__main__":
    main()
