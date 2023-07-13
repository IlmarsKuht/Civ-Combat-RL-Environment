from stable_baselines3.common.env_checker import check_env

from env import Civ6CombatEnv


def stable_baselines_test(env):
    check_env(env)

def unitTest():
    #First test using stable baselines
    stable_baselines_test()

    #Now custom tests
    env = Civ6CombatEnv(max_steps=100, render_mode=None)
    observation, info = env.reset()
    while True:
        observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
        if terminated or truncated:
            env.reset()
