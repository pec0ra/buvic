import os

import remi.gui as gui
from remi import start, App
from irradiance_evaluation import IrradianceEvaluation

TMP_FILE_DIR = "tmp/"
if not os.path.exists(TMP_FILE_DIR):
    os.makedirs(TMP_FILE_DIR)


class MyApp(App):
    def __init__(self, *args):
        super(MyApp, self).__init__(*args)

    def main(self):
        self.main_container = gui.VBox(width="80%")
        self.main_container.set_style("margin: 30px auto; padding: 20px")

        self.title = gui.Label("Irradiance calculation")
        self.title.set_style("font-size: 20pt; margin-bottom: 30px")

        self.file_form = gui.HBox()
        self.file_form.set_style("margin-bottom: 20px")
        self.uv_file_selector = FileSelector("UV File:", handler=self.handle_uv_file)
        self.calibration_file_selector = FileSelector("Calibration File:", handler=self.handle_calibration_file)
        self.arf_file_selector = FileSelector("ARF File:", handler=self.handle_arf_file)

        self.calculate_button = gui.Button("Calculate", width=120)
        self.calculate_button.set_enabled(False)
        self.calculate_button.set_style("align-self: end")
        self.calculate_button.onclick.do(self.calculate)

        self.file_form.append(self.uv_file_selector)
        self.file_form.append(self.calibration_file_selector)
        self.file_form.append(self.arf_file_selector)

        # appending a widget to another, the first argument is a string key
        self.main_container.append(self.title)
        self.main_container.append(self.file_form)
        self.main_container.append(self.calculate_button)

        # returning the root widget
        return self.main_container

    def handle_uv_file(self, file_uploader, file_data, file_name):
        self.uv_file = TMP_FILE_DIR + file_name
        self.check_files()

    def handle_calibration_file(self, file_uploader, file_data, file_name):
        self.calibration_file = TMP_FILE_DIR + file_name
        self.check_files()

    def handle_arf_file(self, file_uploader, file_data, file_name):
        self.arf_file = TMP_FILE_DIR + file_name
        self.check_files()

    def check_files(self):
        print(self.uv_file)
        print(self.calibration_file)
        print(self.arf_file)
        if self.uv_file is not None and self.calibration_file is not None and self.arf_file is not None:
            self.calculate_button.set_enabled(True)
        else:
            self.calculate_button.set_enabled(False)

    def calculate(self, widget):
        self.calculate_button.set_enabled(False)
        ie = IrradianceEvaluation(self.uv_file, self.calibration_file, self.arf_file)
        results = ie.calculate()
        print(results)


class FileSelector(gui.VBox):

    def __init__(self, title: str, handler=None):
        super().__init__(width=300)
        self.set_style("align-items: left")
        self.handler = handler
        self.title = title
        self.label = gui.Label(title)
        self.file_selector = gui.FileUploader("tmp/")
        self.file_selector.ondata.do(self.handle_data)
        self.change_file_button = gui.Button("Change", width=80)
        self.change_file_button.set_style("display: none")
        self.change_file_button.onclick.do(self.change_file)
        self.append(self.label)
        self.append(self.file_selector)
        self.append(self.change_file_button)

    def handle_data(self, file_uploader, file_data, file_name):
        self.label.set_text(self.title + " " + file_name)
        self.change_file_button.set_style("display: block")
        self.file_selector.set_style("display: none")

        if self.handler is not None:
            self.handler(file_uploader, file_data, file_name)

    def change_file(self, widget):
        self.label.set_text(self.title)
        self.change_file_button.set_style("display: none")
        self.file_selector.set_style("display: block")

        if self.handler is not None:
            self.handler(self.file_selector, None, None)



# starts the web server
start(MyApp)
