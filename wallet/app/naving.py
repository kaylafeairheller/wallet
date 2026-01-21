import flet as ft


class Navbar(ft.Stack):
    HOME = 0
    IDENTIFIERS = 1
    REGISTRIES = 2
    CREDENTIALS = 3
    CONTACTS = 4
    WITNESSES = 5
    SETTINGS = 6

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page  # Store page reference (page property is read-only in Flet controls)

        destinations = [
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.HOME),
                selected_icon=ft.Icon(ft.Icons.HOME_OUTLINED),
                label='Home',
                padding=ft.Padding.all(10),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DATASET_LINKED,
                selected_icon=ft.Icons.DATASET_LINKED_OUTLINED,
                label='Identifiers',
                padding=ft.Padding.all(10),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ACCOUNT_TREE_OUTLINED,
                selected_icon=ft.Icons.ACCOUNT_TREE,
                label='Registries',
                padding=ft.Padding.all(10),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.LOCK_OUTLINED,
                selected_icon=ft.Icons.LOCK_ROUNDED,
                label='Credentials',
                padding=ft.Padding.all(10),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.PEOPLE),
                selected_icon=ft.Icon(ft.Icons.PEOPLE_OUTLINE),
                label='Contacts',
                padding=ft.Padding.all(10),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icon(ft.Icons.VIEW_COMFY_ALT),
                selected_icon=ft.Icon(ft.Icons.VIEW_COMFY_ALT_OUTLINED),
                label='Witnesses',
                padding=ft.Padding.all(10),
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icon(ft.Icons.SETTINGS),
                label=ft.Text('Settings'),
                padding=ft.Padding.all(10),
            ),
        ]

        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=400,
            destinations=destinations,
            on_change=self.nav_change,
            expand=True,
        )
        # Flet 1.0 declarative: set controls directly
        self.controls = [self.rail]

    @property
    def page(self):
        return self._page

    async def nav_change(self, e):
        index = e if (type(e) is int) else e.control.selected_index
        self.rail.selected_index = index
        if index == self.HOME:
            await self.page.push_route('/home')
        elif index == self.IDENTIFIERS:
            await self.page.push_route('/identifiers')
        elif index == self.REGISTRIES:
            await self.page.push_route('/registries')
        elif index == self.CREDENTIALS:
            await self.page.push_route('/credentials')
        elif index == self.CONTACTS:
            await self.page.push_route('/contacts')
        elif index == self.WITNESSES:
            await self.page.push_route('/witnesses')
        elif index == self.SETTINGS:
            await self.page.push_route('/settings')

        self.page.update()
