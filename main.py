from env import Civ6CombatEnv

from unitTest import unitTest


def main():
    env = Civ6CombatEnv(rows=8, columns=8, max_steps=100, render_mode="interactable", bots=2, start_troops=1, fps=60)
    env.start_interactable()
    
    # env = Civ6CombatEnv(rows=8, columns=8, max_steps=100, render_mode="human", bots=2, start_troops=1, fps=60)
    # observation, info = env.reset()
    # while True:
    #     observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
    #     if terminated or truncated:
    #         env.reset()

    # env = Civ6CombatEnv(rows=8, columns=8, max_steps=100, render_mode=None, bots=2, start_troops=1, fps=60)
    # observation, info = env.reset()
    # while True:
    #     observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
    #     if terminated or truncated:
    #         env.reset()



    

if __name__ == "__main__":
    #unitTest()
    main()
