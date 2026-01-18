"""
Agenting module for the Wallet application.
"""

import logging

import flet as ft
from keri import kering
from keri.app import configing, directing, habbing
from keri.core import coring, signing
from keri.vdr import credentialing

from wallet import walleting
from wallet.app.colouring import Colouring
from wallet.core.configing import DEFAULT_PASSCODE, DEFAULT_USERNAME, Environments, WalletConfig
from wallet.core.habs import check_passcode, format_bran, keystore_exists, open_hby
from wallet.logs import log_errors
from wallet.tasks import migrating, oobiing
from wallet.tasks.migrating import check_migration

logger = logging.getLogger('wallet')


class AgentInitialization(ft.AlertDialog):
    """
    Represents the agent initialization dialog.

    Args:
        app (App): The application instance.
        page (ft.Page): The page instance.
        config (WalletConfig, optional): The Wallet configuration. Defaults to None.
    """

    def __init__(self, app, page: ft.Page, config: WalletConfig = None):
        super(AgentInitialization, self).__init__()
        # Environment-specific setup
        match config.environment:
            case Environments.DEVELOPMENT:
                default_username = DEFAULT_USERNAME
                default_passcode = DEFAULT_PASSCODE
            case Environments.PRODUCTION | Environments.STAGING:
                default_username = ''
                default_passcode = ''
            case _:
                default_username = ''
                default_passcode = ''

        self.app = app
        self._page = page  # Store page reference (page property is read-only in Flet controls)
        self.config = config
        self.username = ft.TextField(label='Name', value=default_username)
        self.passcode = ft.TextField(
            label='Passcode',
            value=default_passcode,
            password=True,
            can_reveal_password=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.modal = True
        self.title = ft.Text('Wallet Initialization')
        self.content = ft.Column(
            [
                ft.Divider(),
                self.username,
                self.passcode,
            ],
            height=170,
            width=300,
        )
        self.actions = [
            ft.Button(
                'Create',
                on_click=self.generate_habery,
            ),
            ft.Button(
                'Cancel',
                on_click=self.close_init,
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.SPACE_EVENLY

    @property
    def page(self):
        return self._page

    async def close_init(self, _):
        """
        Closes the agent initialization dialog.
        """
        self.page.pop_dialog()

    async def generate_habery(self, e):
        """
        Generates a new Habery instance and updates the agent drawer.
        """
        self.page.pop_dialog()
        cf = configing.Configer(
            name=self.config.config_file,
            base='',
            headDirPath=self.config.config_dir,
            temp=False,
            reopen=True,
            clear=False,
        )
        kwa = dict()

        kwa['salt'] = signing.Salter(raw=self.app.salt.encode('utf-8')).qb64
        kwa['bran'] = self.passcode.value
        kwa['algo'] = self.app.algo
        kwa['tier'] = self.app.tier

        hby = habbing.Habery(
            name=self.username.value,
            base=self.app.base,
            temp=self.app.temp,
            cf=cf,
            **kwa,
        )

        # self.rgy = credentialing.Regery(hby=hby)
        # self.rgy = credentialing.Regery(hby=self.hby, name=self.name, base=self.base)
        # self.vry = verifying.Verifier(hby=self.hby, reger=self.rgy.reger)

        directing.runController([oobiing.OOBILoader(hby=hby)])
        directing.runController([oobiing.OOBIAuther(hby=hby)])

        hby.close()

        self.app.agentDrawer.update_agents()

        self.page.update()


class AgentConnection(ft.AlertDialog):
    """Dialog for connecting to an existing agent identity."""

    def __init__(self, app, page, config: WalletConfig, username):
        """
        Args:
            app (WalletApp): The application instance.
            page (ft.Page): The page instance.
            config (WalletConfig): The Wallet configuration.
            username (str): The username of the agent to connect to.
        """
        super(AgentConnection, self).__init__()
        # Environment-specific setup
        match config.environment:
            case Environments.PRODUCTION | Environments.STAGING:
                default_passcode = ''
            case Environments.DEVELOPMENT:
                default_passcode = DEFAULT_PASSCODE
            case _:
                default_passcode = ''

        self.app = app
        self._page = page  # Store page reference (page property is read-only in Flet controls)
        self.config = config
        self.username = username
        self.passcode = ft.TextField(
            label='Passcode',
            value=default_passcode,
            password=True,
            can_reveal_password=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        self.title = ft.Text(f'Open {self.username}')
        column = ft.Column(
            [
                ft.Container(
                    content=ft.Divider(color=Colouring.get(color=Colouring.SECONDARY)),
                ),
                self.passcode,
            ],
            height=100,
            width=300,
        )

        self.modal = True
        self.content = ft.Container(
            content=column,
        )

        self.actions = [
            ft.Button(
                'Open',
                on_click=self.on_open,
            ),
            ft.Button(
                'Cancel',
                on_click=self.close_connect,
            ),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    @property
    def page(self):
        return self._page

    async def confirm_migrate(self, e):
        """
        Performs the actual migration
        """
        name = self.username
        base = self.app.base
        bran = format_bran(self.passcode.value)
        try:
            await migrating.migrate_keystore(name=name, base=base, bran=bran)
        except Exception as ex:
            logger.exception(ex)
            await self.app.snack(f'Database migration failed for {name}. Error: {str(ex)}')
            self.page.update()
            await self.close_connect(e)
            return
        await self.app.snack(f'Database migration succeeded for: {name}')
        await self.agent_connect(name, base, bran)
        await self.close_connect(e)
        await self.page.push_route('/home')
        self.page.update()
        await self.app.snack(f'Connected to {name}')

    async def close_connect(self, _):
        """
        Closes the connection dialog.

        Parameters:
        - _: Placeholder parameter (ignored)

        Returns:
        - None
        """
        self.page.pop_dialog()

    @log_errors
    async def agent_connect(self, name, base, passcode):
        try:
            agent, agent_task, event = open_hby(
                name=name,
                base=base,
                bran=passcode,
                config_file=self.config.config_file,
                config_dir=self.config.config_dir,
                app=self.app,
            )
        except kering.AuthError:
            await self.app.snack('Invalid Username or Passcode, please try again...')
            return
        except Exception as ex:
            logger.error(f'Error opening Habery: {str(ex)}')
            raise
        self.app.agent = agent
        self.app.agent_task = agent_task
        self.app.agent_shutdown_event = event

        await self.app.snack('Fetching notifications...')

        self.app.reload_witnesses_and_members()
        self.app.reload()
        self.page.title = f'{self.app.name} - {name} [{self.app.environment.value}]'
        self.page.hby_name = name

    @log_errors
    async def on_open(self, e):
        """Connects to the selected identity (Agent) stored locally on the filesystem."""
        name = self.username
        base = self.app.base
        bran = format_bran(self.passcode.value)
        if not keystore_exists(name, base):
            logger.error('Keystore must already exist, exiting')
            await self.app.snack('Keystore not already initialized...')
            return
        logger.info(f'Connecting to {name}')
        # check password first
        try:
            check_passcode(name=name, base=base, bran=bran)
        except kering.AuthError:
            logger.error(f'Passcode incorrect for user {name}')
            await self.app.snack('Invalid Username or Passcode, please try again...')
            return
        except Exception as ex:
            logger.exception(ex)
            await self.app.snack(f'Error checking passcode: {str(ex)}')
            return

        try:
            await check_migration(name, base, bran)
            await self.agent_connect(name, base, bran)
            await self.close_connect(e)
            await self.page.push_route('/home')
            self.page.update()
            await self.app.snack(f'Connected to {name}')
        except walleting.OldKeystoreError:
            logger.error('Old keystore detected, migration needed')
            await self.app.snack(f'Keystore migration needed for {name}. Migrating...')
            # Then connect if a migration is not needed
            self.title = ft.Text(f'Migrate {name}')
            self.content = ft.Text('Datastore migration needed.')
            self.actions = [
                ft.Button(
                    'Confirm',
                    on_click=self.confirm_migrate,
                ),
                ft.Button(
                    'Cancel',
                    on_click=self.close_connect,
                ),
            ]
            self.update()
        logger.info(f'Connected to {name}')
