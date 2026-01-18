import logging

import flet as ft

logger = logging.getLogger('wallet')


class NotificationsBase(ft.Column):
    """
    Base class for notifications panel.

    Args:
        app (object): The application object.
        panel (object): The panel object.

    Attributes:
        app (object): The application object.
        title (object): The title of the notifications panel.
        panel (object): The panel object.
        card (object): The container for the panel content.

    """

    def __init__(self, app, panel, title=None):
        self.app = app
        self.panel = panel
        self.card = ft.Container(content=self.panel, expand=True, alignment=ft.Alignment.TOP_LEFT)
        self.title = title if title else ft.Row()
        super().__init__(
            [
                self.title,
                ft.Row([self.card]),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
