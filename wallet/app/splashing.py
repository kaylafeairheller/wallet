import flet as ft

from wallet.app.assets import Assets


class Splash(ft.Column):
    def __init__(self, app):
        self.app = app

        super(Splash, self).__init__(
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                Assets().logo_splash,
                                expand=True,
                            )
                        ],
                    ),
                    padding=ft.Padding.only(left=0, top=-100, right=0, bottom=0),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            ],
            spacing=25,
            expand=True,
        )

    def did_mount(self):
        self.page.run_task(self.app.toggle_drawer, None)
