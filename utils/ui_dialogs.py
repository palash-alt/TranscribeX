import tkinter.messagebox as mb


def show_error(title: str, message: str) -> None:
    """Display an error dialog.

    Args:
        title: Dialog title.
        message: Error message.
    """
    mb.showerror(title, message)


def show_warning(title: str, message: str) -> None:
    """Display a warning dialog.

    Args:
        title: Dialog title.
        message: Warning message.
    """
    mb.showwarning(title, message)


def show_info(title: str, message: str) -> None:
    """Display an information dialog.

    Args:
        title: Dialog title.
        message: Information message.
    """
    mb.showinfo(title, message)
