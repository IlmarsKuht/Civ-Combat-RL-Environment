from env import Civ6CombatEnv

from unitTest import unitTest


def main():
    # load_model=False
    # env = Civ6CombatEnv(max_steps=100, render_mode=None)
    # if load_model:
    #     model = PPO.load("./models/civ6_model")
    #     model.set_env(env)
    # else:
    #     policy_kwargs = dict(
    #         features_extractor_class=CustomCNN,
    #         activation_fn=torch.nn.ReLU,
    #         net_arch=dict(pi=[128, 128], vf=[128, 128])
    #     )
    #     model = PPO("CnnPolicy", env, n_steps=1024, ent_coef=0.001, verbose=True, tensorboard_log='./logs', policy_kwargs=policy_kwargs)
    # model.learn(total_timesteps=4000, progress_bar=True)
    # model.save("./models/civ6_model")
    env = Civ6CombatEnv(rows=8, columns=8, max_steps=100, render_mode="interactable", start_troops=1, fps=4)
    # check_env(env)
    # policy_kwargs = dict(
    #         features_extractor_class=CustomCNN,
    #         # activation_fn=torch.nn.ReLU,
    #         # net_arch=dict(pi=[128, 128, 128], vf=[128, 128, 128])
    #     )
    # model = PPO("CnnPolicy", env, verbose=True, policy_kwargs=policy_kwargs)
    # observation, info = env.reset()
    # while True:
    #     observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
    #     if terminated or truncated:
    #         env.reset()



    env.start_interactable()

if __name__ == "__main__":
    unitTest()
    main()
