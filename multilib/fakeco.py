class FakeConfigObject(object):
    """
    fake mash configuration object that contains enough data to run
    through the testing framework herein
    """
    def __init__(self, conf):
        setattr(self, 'multilib_devel_blacklist', conf.get('devel', 'black'))
        setattr(self, 'multilib_devel_whitelist', conf.get('devel', 'white'))
        setattr(self, 'multilib_runtime_blacklist', conf.get('runtime', 'black'))
        setattr(self, 'multilib_runtime_whitelist', conf.get('runtime', 'white'))
        self.multilib_file = 'cheat'
