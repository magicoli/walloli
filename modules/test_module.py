import modules.config as config

class MyClass:
    def __init__(self):
        print("Volume from myclass ", config.volume)
        self.my_function()

    def my_function(self):
        print("Volume from my_function ", config.volume)

