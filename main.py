from kivy.app import App
from vivy.uic.label import Label

class TestApp(App):
    def build(self):
        return Label(text="APK FUNCIONANDO 🚀", font_size=40)
        if __name__ == "__main__":
            TestApp().run()
