from remi.gui import Widget, VBox, HBox


def show(widget: Widget):
    if isinstance(widget, HBox) or isinstance(widget, VBox):
        widget.set_style("display: flex")
    else:
        widget.set_style("display: block")


def hide(widget: Widget):
    widget.set_style("display: none")
