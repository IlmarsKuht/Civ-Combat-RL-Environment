from stable_baselines3.common.env_checker import check_env

from env import Civ6CombatEnv


def stable_baselines_test():
    env = Civ6CombatEnv(rows=6, columns=6, max_steps=10, render_mode=None)
    check_env(env)
    env = Civ6CombatEnv(rows=6, columns=6, max_steps=10, render_mode="human", fps=100)
    check_env(env)
    env.close()


def random_test():
    env = Civ6CombatEnv(rows=7, columns=7, max_steps=100, render_mode=None)
    env.reset()
    for i in range(10000):
        _, _, terminated, truncated, _ = env.step(env.action_space.sample())
        if terminated or truncated:
            env.reset()
        if i%1000==0:
            print(f"iteration {i}")
    env = Civ6CombatEnv(rows=7, columns=7, max_steps=10, render_mode="human", fps=100)
    env.reset()
    for i in range(100):
        _, _, terminated, truncated, _ = env.step(env.action_space.sample())
        if terminated or truncated:
            env.reset()
    env.close()

#NEED A UNIT TEST FOR INTERACTABLE GAME MODE
#AND UNIT TEST SHOULD SAY WHAT'S THE PROBLEM, NOT JUST RANDOMLY PLAY, but we doin this for now, better than nothing

def unitTest():
    #First test using stable baselines
    # print(f"Starting stable baselines test")
    # stable_baselines_test()
    # print(f"Finished stable baselines test")

    #completely random test
    print(f"Starting random test")
    random_test()
    print(f"Finished random test")
   
    

    # #test using No render mode
    # env = Civ6CombatEnv(max_steps=100, render_mode=None)

    # #Test using human render mode
    # env = Civ6CombatEnv(max_steps=100, render_mode="human")
    # check_env(env)
    # policy_kwargs = dict(
    #         features_extractor_class=CustomCNN,
    #         # activation_fn=torch.nn.ReLU,
    #         # net_arch=dict(pi=[128, 128, 128], vf=[128, 128, 128])
    #     )
    # observation, info = env.reset()
    # while True:
    #     actions, _ = model.predict(observation)
    #     observation, reward, terminated, truncated, info = env.step(actions)
    #     if terminated or truncated:
    #         env.reset()

    print(f"############### UNIT TESTS PASSED!!! ###############")

    
