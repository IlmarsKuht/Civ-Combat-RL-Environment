from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO

from env import Civ6CombatEnv

from CNN import CustomCNN


def main():
    env = Civ6CombatEnv(render_mode="human")
    policy_kwargs = dict(
        features_extractor_class=CustomCNN,

    )
    model = PPO("CnnPolicy", env, verbose=True, policy_kwargs=policy_kwargs)
    
    # model.learn()
    #check_env(env)
    observation, info = env.reset()
    while True:
        actions, _ = model.predict(observation)
        observation, reward, terminated, truncated, info = env.step(actions)
        
        if terminated == True:
            env.reset()

if __name__ == "__main__":
    main()
