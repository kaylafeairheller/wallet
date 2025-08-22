import asyncio
import json
import logging
import pprint
from pathlib import Path

import flet as ft
from hio.help import decking
from keri.app import connecting
from keri.app.keeping import Algos
from keri.core import coring
from keri.core.coring import Tiers

from wallet.app import drawing
from wallet.app.assets import Assets
from wallet.app.layout import Layout
from wallet.core.agenting import close_agent_task
from wallet.core.configing import WalletConfig
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class WalletApp(ft.Stack):
    def __init__(self, page: ft.Page, config: WalletConfig):
        super().__init__()
        # Flet config props
        self.environment = config.environment
        self.layout = None
        self.page = page
        self.name = config.app_name
        self.page.title = (
            self.name if config.environment.value == 'production' else f'{self.name} [{config.environment.value}]'
        )
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.on_route_change = self.route_change
        self.page.window.width = 1024
        self.page.window.height = 768
        self.page.window.prevent_close = True
        self.page.window.on_event = self.on_window_event

        # ft.Stack attributes
        self.width = 1024
        self.height = 768
        self.current_top = 0
        self.current_left = 0

        # KERI props
        self.agent = None  # Will be set by the AgentDrawer
        self.agent_task = None  # Will be set by the AgentDrawer
        self.agent_shutdown_event = asyncio.Event()  # Will be set by the AgentDrawer

        # AgentEvents
        self.agent_events = decking.Deck()

        self.base = ''
        self.temp = False
        self.tier = Tiers.low
        self.algo = Algos.salty
        self.salt = coring.randomNonce()[2:23]

        # Flet Page state or components
        self.notes = []
        self.witnesses = []
        self.members = []

        self.agentDrawer = drawing.AgentDrawer(app=self, page=page, open=True, config=config)
        self.agentDrawerButton = ft.IconButton(
            ft.icons.WALLET_ROUNDED,
            tooltip='Wallets',
            on_click=self.toggle_drawer,
        )
        self.notificationsButton = ft.IconButton(
            ft.icons.NOTIFICATIONS_NONE_ROUNDED,
            on_click=self.show_notifications,
        )
        self.lockButton = ft.IconButton(ft.icons.LOCK, on_click=self.lock)

        self.actions = [self.agentDrawerButton]
        self.page.appbar = ft.AppBar(
            leading=ft.Container(
                Assets().logo_icon,
                border_radius=ft.border_radius.all(5),
                padding=ft.padding.all(2),
                margin=ft.margin.all(10),
            ),
            title=ft.Text(self.name, weight=ft.FontWeight.BOLD),
            center_title=False,
            actions=self.actions,
        )
        self.wit_pools = self.load_witness_pools(config)

    @staticmethod
    def load_witness_pools(config: WalletConfig):
        with open(config.witness_pool_path, 'r') as f:
            wit_pools = json.load(f)
            pp = pprint.PrettyPrinter(indent=2, sort_dicts=False)
            logger.info('Loaded witness pools from %s\n%s', config.witness_pool_path, pp.pformat(wit_pools))
        return wit_pools

    async def close(self):
        logger.info('Wallet App closing')
        closed = await close_agent_task(self.agent_task, self.agent_shutdown_event)
        self.agent_task = None  # Clear existing HioTask reference
        if closed:
            logger.info(f'Disconnected agent {self.agent.hby.name}')
        self.page.window.destroy()
        logger.info('Wallet App closed')

    async def on_window_event(self, e):
        if e.data == 'close':
            await self.close()

    def did_mount(self):
        logger.info('Wallet App mounted')

    @log_errors
    async def toggle_drawer(self, _):
        self.page.end_drawer = self.agentDrawer
        await self.page.show_end_drawer_async(self.page.end_drawer)
        await self.page.end_drawer.update_async()

    @log_errors
    async def route_change(self, _):
        tr = ft.TemplateRoute(self.page.route)
        if tr.match('/'):
            await self.page.go_async('/splash')
        elif tr.match('/home'):
            await self.layout.set_home()
        elif tr.match('/identifiers'):
            await self.layout.set_identifiers_list()
        elif tr.match('/identifiers/create'):
            await self.layout.set_identifier_create()
        elif tr.match('/identifiers/:prefix/view'):
            await self.layout.set_identifier_view(tr.prefix)
        elif tr.match('/identifiers/:prefix/rotate'):
            await self.layout.set_identifier_rotate(tr.prefix)
        elif tr.match('/contacts'):
            await self.layout.set_contacts_list()
        elif tr.match('/contacts/create'):
            await self.layout.set_contact_create()
        elif tr.match('/contacts/:prefix/view'):
            await self.layout.set_contact_view(tr.prefix)
        elif tr.match('/settings'):
            await self.layout.set_settings_view()
        elif tr.match('/notifications'):
            await self.layout.set_notifications_view()
        elif tr.match('/notifications/:note_id'):
            await self.layout.set_notifications_note_view(tr.note_id)
        elif tr.match('/witnesses'):
            await self.layout.set_witnesses_view()
        elif tr.match('/witnesses/create'):
            await self.layout.set_witness_add_view()
        elif tr.match('/witnesses/:prefix/view'):
            await self.layout.set_witness_view(tr.prefix)
        elif tr.match('/identifiers/:prefix/view'):
            await self.layout.set_witness_view()
        elif tr.match('/workflows/singlesig/identifiers/create'):
            await self.layout.set_singlesig_identifier_create()
        elif tr.match('/workflows/multisig/identifiers/create'):
            await self.layout.set_multisig_identifier_create()
        elif tr.match('/workflows/multisig/identifiers/:prefix/contacts/connect'):
            await self.layout.set_connect_contact(tr.prefix)
        elif tr.match('/workflows/multisig/identifiers/:prefix/contacts/:alias/:aid/challenge'):
            await self.layout.set_multisig_challenge(tr.prefix, tr.alias, tr.aid)
        elif tr.match('/workflows/multisig/identifiers/:prefix/contacts/:alias/:aid/multisig/create'):
            await self.layout.set_create_multisig(tr.prefix, tr.alias, tr.aid)
        elif tr.match('/workflows/delegation/accept'):
            await self.layout.set_accept_delegation()
        elif tr.match('/workflows/issue/ecr'):
            await self.layout.set_issue_ecr_auth()
        elif tr.match('/workflows/issue/oor'):
            await self.layout.set_issue_oor_auth()
        elif tr.match('/workflows/issue/qvi'):
            await self.layout.set_issue_qvi()
        elif tr.match('/splash'):
            logger.info('Route change to /splash')
            await self.layout.set_splash_view()

        await self.page.update_async()

    async def show_notifications(self, e=None):
        self.page.route = '/notifications'
        await self.page.update_async()

    async def lock(self, e=None):
        closed = await close_agent_task(self.agent_task, self.agent_shutdown_event)
        self.agent_task = None  # Clear existing HioTask reference
        if closed:
            logger.info(f'Disconnected agent {self.agent.hby.name}')
            self.agent = None
            self.page.floating_action_button = None
            self.layout.navbar.visible = False
            self.notificationsButton.visible = False
            self.lockButton.visible = False
            self.page.hby_name = None
            self.page.snack_bar = None
            self.page.route = '/splash'
            await self.page.update_async()

    async def refreshContacts(self):
        org = connecting.Organizer(hby=self.agent.hby)
        contacts = []
        for c in org.list():
            aid = c['id']
            accepted = [saider.qb64 for saider in self.agent.hby.db.chas.get(keys=(aid,))]
            received = [saider.qb64 for saider in self.agent.hby.db.reps.get(keys=(aid,))]
            valid = set(accepted) & set(received)

            challenges = []
            for said in valid:
                exn = self.agent.hby.db.exns.get(keys=(said,))
                challenges.append(dict(dt=exn.ked['dt'], words=exn.ked['a']['words']))

            c['challenges'] = challenges

            wellKnowns = []
            wkans = self.agent.hby.db.wkas.get(keys=(aid,))
            for wkan in wkans:
                wellKnowns.append(dict(url=wkan.url, dt=wkan.dt))

            c['wellKnowns'] = wellKnowns

            contacts.append(c)

        await self.layout.contacts.set_contacts(contacts)
        await self.layout.contacts.update_async()

    def reload(self):
        if self.agent is not None:
            self.layout.navbar.visible = True
            self.notificationsButton.visible = True
            self.lockButton.visible = True

    def reload_witnesses_and_members(self):
        org = connecting.Organizer(hby=self.agent.hby)

        self.witnesses.clear()
        self.members.clear()
        for contact in org.list():
            prefixer = coring.Prefixer(qb64=contact['id'])
            if not prefixer.transferable:
                self.witnesses.append(contact)
            else:
                self.members.append(contact)

        if all('alias' in c for c in self.witnesses):
            self.witnesses = sorted(self.witnesses, key=lambda c: c['alias'])
        else:
            self.witnesses = sorted(self.witnesses, key=lambda c: c['id'])
        if all('alias' in c for c in self.members):
            self.members = sorted(self.members, key=lambda c: c['alias'])
        else:
            self.members = sorted(self.members, key=lambda c: c['id'])

    def build(self):
        logger.info('Building Wallet App panel...')
        self.layout = Layout(
            self,
            self.page,
            expand=True,
            vertical_alignment='start',
        )
        return self.layout

    # on_change
    @property
    def agent(self):
        return self._agent

    @agent.setter
    def agent(self, agent):
        self._agent = agent
        if self._agent is not None:
            self.layout.navbar.visible = True
            self.layout.splash.visible = False
            self.actions.insert(0, self.notificationsButton)
            self.actions.insert(len(self.actions), self.lockButton)

    async def snack(self, message, duration=5000):
        self.page.snack_bar = ft.SnackBar(ft.Text(message), duration=duration)
        self.page.snack_bar.open = True
        await self.page.update_async()

    @property
    def hby(self):
        return self.agent.hby if self.agent is not None else None

    @staticmethod
    def environments():
        dbhome = Path('/usr/local/var/keri/db')
        if not dbhome.exists():
            dbhome = Path(f'{Path.home()}/.keri/db')

        if not dbhome.is_dir():
            return []

        envs = []
        for p in dbhome.iterdir():
            envs.append(p.stem)

        return envs
