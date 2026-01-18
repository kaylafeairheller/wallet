import flet as ft


class Colouring:
    PRIMARY = 'primary'
    ON_PRIMARY = 'on_primary'
    SECONDARY = 'secondary'
    ON_SECONDARY = 'on_secondary'
    SURFACE = 'surface'
    ON_SURFACE = 'on_surface'
    BACKGROUND = 'background'
    ON_BACKGROUND = 'on_background'
    RED = 'red'

    # Class-level variable to store the theme mode
    _theme_mode = None

    class Light(ft.Theme):
        RED = '#b00020'
        PRIMARY = '#61783e'
        ON_PRIMARY = '#FFFFFF'
        SECONDARY = '#819f49'
        ON_SECONDARY = '#FFFFFF'
        SURFACE = '#F5F5F5'
        BACKGROUND = '#FFFFFF'
        ON_BACKGROUND = '#000000'
        ON_SURFACE = '#1a1a1a'
        ON_SURFACE_VARIANT = '#424242'
        # Surface container hierarchy for Material 3
        SURFACE_CONTAINER_LOWEST = '#FFFFFF'
        SURFACE_CONTAINER_LOW = '#F7F7F7'
        SURFACE_CONTAINER = '#F0F0F0'
        SURFACE_CONTAINER_HIGH = '#E8E8E8'
        SURFACE_CONTAINER_HIGHEST = '#E0E0E0'
        # Outline colors for borders and dividers
        OUTLINE = '#757575'
        OUTLINE_VARIANT = '#C0C0C0'

        def __init__(self):
            super().__init__(
                color_scheme=ft.ColorScheme(
                    primary=self.PRIMARY,
                    on_primary=self.ON_PRIMARY,
                    secondary=self.SECONDARY,
                    on_secondary=self.ON_SECONDARY,
                    surface=self.SURFACE,
                    on_surface=self.ON_SURFACE,
                    on_surface_variant=self.ON_SURFACE_VARIANT,
                    surface_container_lowest=self.SURFACE_CONTAINER_LOWEST,
                    surface_container_low=self.SURFACE_CONTAINER_LOW,
                    surface_container=self.SURFACE_CONTAINER,
                    surface_container_high=self.SURFACE_CONTAINER_HIGH,
                    surface_container_highest=self.SURFACE_CONTAINER_HIGHEST,
                    outline=self.OUTLINE,
                    outline_variant=self.OUTLINE_VARIANT,
                ),
                text_theme=ft.TextTheme(
                    body_large=ft.TextStyle(color=self.ON_SURFACE),
                    body_medium=ft.TextStyle(color=self.ON_SURFACE),
                    body_small=ft.TextStyle(color=self.ON_SURFACE_VARIANT),
                    label_large=ft.TextStyle(color=self.ON_SURFACE),
                    label_medium=ft.TextStyle(color=self.ON_SURFACE),
                    label_small=ft.TextStyle(color=self.ON_SURFACE_VARIANT),
                ),
            )

        class FloatingActionButtonTheme(ft.FloatingActionButtonTheme):
            def __init__(self):
                super().__init__(
                    bgcolor='#61783e',
                    foreground_color='#ffffff',
                )

    class Dark(ft.Theme):
        RED = '#b00020'
        PRIMARY = '#b4d070'
        ON_PRIMARY = '#000000'
        SECONDARY = '#819f49'
        ON_SECONDARY = '#ffffff'
        SURFACE = '#1e1e1e'
        BACKGROUND = '#121212'
        ON_BACKGROUND = '#ffffff'
        ON_SURFACE = '#e0e0e0'
        ON_SURFACE_VARIANT = '#c0c0c0'
        # Surface container hierarchy for Material 3
        SURFACE_CONTAINER_LOWEST = '#0d0d0d'
        SURFACE_CONTAINER_LOW = '#1a1a1a'
        SURFACE_CONTAINER = '#242424'
        SURFACE_CONTAINER_HIGH = '#2e2e2e'
        SURFACE_CONTAINER_HIGHEST = '#383838'
        # Outline colors for borders and dividers - brighter for visibility
        OUTLINE = '#9e9e9e'
        OUTLINE_VARIANT = '#6e6e6e'

        def __init__(self):
            super().__init__(
                color_scheme=ft.ColorScheme(
                    primary=self.PRIMARY,
                    on_primary=self.ON_PRIMARY,
                    secondary=self.SECONDARY,
                    on_secondary=self.ON_SECONDARY,
                    surface=self.SURFACE,
                    on_surface=self.ON_SURFACE,
                    on_surface_variant=self.ON_SURFACE_VARIANT,
                    surface_container_lowest=self.SURFACE_CONTAINER_LOWEST,
                    surface_container_low=self.SURFACE_CONTAINER_LOW,
                    surface_container=self.SURFACE_CONTAINER,
                    surface_container_high=self.SURFACE_CONTAINER_HIGH,
                    surface_container_highest=self.SURFACE_CONTAINER_HIGHEST,
                    outline=self.OUTLINE,
                    outline_variant=self.OUTLINE_VARIANT,
                ),
                text_theme=ft.TextTheme(
                    body_large=ft.TextStyle(color=self.ON_SURFACE),
                    body_medium=ft.TextStyle(color=self.ON_SURFACE),
                    body_small=ft.TextStyle(color=self.ON_SURFACE_VARIANT),
                    label_large=ft.TextStyle(color=self.ON_SURFACE),
                    label_medium=ft.TextStyle(color=self.ON_SURFACE),
                    label_small=ft.TextStyle(color=self.ON_SURFACE_VARIANT),
                ),
            )

        class FloatingActionButtonTheme(ft.FloatingActionButtonTheme):
            def __init__(self):
                super().__init__(
                    bgcolor='#b4d070',
                    foreground_color='#000000',
                )

    @classmethod
    def set_theme(cls, theme_mode):
        if theme_mode in [ft.Brightness.LIGHT.name, ft.Brightness.DARK.name]:
            cls._theme_mode = theme_mode
        else:
            raise ValueError("Theme mode must be ft.Brightness.LIGHT.name or 'dark'")

    @classmethod
    def get(cls, color):
        """Get the color based on the set theme mode."""
        if cls._theme_mode is None:
            raise Exception("Theme mode is not set. Use 'set_theme' to set it first.")

        match color:
            case cls.PRIMARY:
                return cls.Light.PRIMARY if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.PRIMARY
            case cls.ON_PRIMARY:
                return cls.Light.ON_PRIMARY if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.ON_PRIMARY
            case cls.SECONDARY:
                return cls.Light.SECONDARY if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.SECONDARY
            case cls.ON_SECONDARY:
                return cls.Light.ON_SECONDARY if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.ON_SECONDARY
            case cls.SURFACE:
                return cls.Light.SURFACE if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.SURFACE
            case cls.ON_SURFACE:
                return cls.Light.ON_SURFACE if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.ON_SURFACE
            case cls.BACKGROUND:
                return cls.Light.BACKGROUND if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.BACKGROUND
            case cls.ON_BACKGROUND:
                return cls.Light.ON_BACKGROUND if cls._theme_mode == ft.Brightness.LIGHT.name else cls.Dark.ON_BACKGROUND
            case cls.RED:
                return '#b00020'
            case _:
                return '#000000'
