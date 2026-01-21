"""
Issuer module for the application.
"""

import asyncio
import logging

import flet as ft
from keri import kering
from keri.app import grouping, habbing
from keri.core import coring, eventing, serdering, signing
from keri.help import helping

logger = logging.getLogger('wallet')

# vLEI Schema SAIDs
SCHEMA_QVI = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
SCHEMA_LE = 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY'
SCHEMA_ECR = 'EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw'
SCHEMA_OOR = 'EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy'
SCHEMA_ECR_AUTH = 'EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g'
SCHEMA_OOR_AUTH = 'EKA57bKBKxr_kN7iN5i7lMUxpMG-s19dRcmov1iDxz-E'


class IssuerBase(ft.Column):
    """
    Base class for issuing workflows in the application.

    Args:
        app: The application object.
        panel: The panel object.
        title (ft.Row): The title panel.

    Attributes:
        app: The application object.
        panel: The panel object.
        card: The container for the panel.
    """

    def __init__(self, app, panel, title=None):
        self.app = app
        title = title if title else ft.Row()
        self.panel = panel
        self.card = ft.Container(
            content=self.panel,
            expand=True,
            alignment=ft.Alignment.TOP_LEFT,
        )

        super().__init__(
            [
                title,
                self.card,
            ],
            expand=True,
            scroll=ft.ScrollMode.ALWAYS,
        )

    @staticmethod
    def loadIssuers(agent):
        habs = agent.hby.habs.values()
        return [
            ft.DropdownOption(
                key=hab.pre,
                text=f'{hab.name} | {hab.pre}',
                data=hab,
            )
            for hab in habs
        ]

    @staticmethod
    def loadContacts(org):
        contacts = org.list()
        contacts = sorted(contacts, key=lambda c: c['alias'])
        contacts = list(filter(lambda c: 'tag=witness' not in c['oobi'], contacts))
        return [
            ft.DropdownOption(
                key=contact['id'],
                text=f'{contact["alias"]} | {contact["id"]}',
                data=contact,
            )
            for contact in contacts
        ]

    @staticmethod
    def loadRegistries(agent):
        if not agent.rgy.regs:
            return []
        return [
            ft.DropdownOption(
                key=rgy.regk,
                text=f'{rgy.name} | {rgy.regk}',
                data=rgy,
            )
            for rgy in agent.rgy.regs.values()
        ]

    @staticmethod
    def loadCredentialsBySchema(agent, schema_said):
        """Load credentials filtered by schema SAID that this agent holds.

        Args:
            agent: The agent instance
            schema_said: The schema SAID to filter by

        Returns:
            List of DropdownOption for matching credentials
        """
        try:
            saiders = agent.rgy.reger.schms.get(keys=(schema_said,))
            if not saiders:
                return []

            credentials = []
            for saider in saiders:
                creder = agent.rgy.reger.creds.get(keys=(saider.qb64,))
                if creder is not None:
                    credentials.append(creder)

            return [
                ft.DropdownOption(
                    key=cred.said,
                    text=f'{cred.attrib.get("LEI", "Unknown")} | {cred.said[:16]}...',
                    data=cred,
                )
                for cred in credentials
            ]
        except Exception:
            logger.exception(f'Error loading credentials by schema {schema_said}')
            return []

    @staticmethod
    async def issue_credential(
        app,
        registry_key: str,
        recipient: str,
        schema: str,
        data: dict,
        source: dict | None = None,
        rules: dict | None = None,
        private: bool = False,
    ) -> tuple:
        """
        Issue a credential using the agent's credentialer.

        Args:
            app: Application instance with agent
            registry_key: Registry key (regk) to use
            recipient: Recipient identifier prefix
            schema: Schema SAID for the credential
            data: Credential data/attributes
            source: Edge sources (optional)
            rules: Rules section (optional)
            private: Privacy flag (optional)

        Returns:
            tuple: (creder, success: bool, error_message: str or None)
        """
        try:
            # Find registry by key
            registry = None
            for reg in app.agent.rgy.regs.values():
                if reg.regk == registry_key:
                    registry = reg
                    break

            if registry is None:
                return (None, False, f'Registry not found: {registry_key}')

            # Create the credential
            creder = app.agent.credentialer.create(
                regname=registry.name,
                recp=recipient,
                schema=schema,
                source=source,
                rules=rules,
                data=data,
                private=private,
            )

            hab = registry.hab

            # Create TEL iss event with timestamp
            dt = helping.nowIso8601()
            iserder = registry.issue(said=creder.said, dt=dt)

            # Create seal linking registry event to issuer's KEL
            vcid = iserder.ked['i']
            rseq = coring.Seqner(snh=iserder.ked['s'])
            rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
            rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

            # Anchor to KEL via interaction or rotation event
            if registry.estOnly:
                anc = hab.rotate(data=[rseal])
            else:
                anc = hab.interact(data=[rseal])

            aserder = serdering.SerderKERI(raw=anc)

            # Process issuance through credentialer and registrar
            app.agent.credentialer.issue(creder, iserder)
            app.agent.registrar.issue(creder, iserder, aserder)

            # Handle multisig coordination if GroupHab
            if isinstance(hab, habbing.GroupHab):
                smids = hab.db.signingMembers(pre=hab.pre)
                smids.remove(hab.mhab.pre)

                # Serialize ACDC with signing artifacts
                acdc = signing.serialize(
                    creder, coring.Prefixer(qb64=iserder.pre), coring.Seqner(sn=iserder.sn), coring.Saider(qb64=iserder.said)
                )

                for recp in smids:
                    exn, atc = grouping.multisigIssueExn(ghab=hab, acdc=acdc, iss=iserder.raw, anc=anc)
                    app.agent.postman.send(src=hab.mhab.pre, dest=recp, topic='multisig', serder=exn, attachment=atc)

            return (creder, True, None)

        except kering.ConfigurationError as e:
            logger.error(f'Configuration error issuing credential: {e}')
            return (None, False, str(e))
        except Exception as e:
            logger.exception('Error issuing credential')
            return (None, False, str(e))

    @staticmethod
    async def wait_for_completion(app, said: str, timeout: float = 120.0) -> bool:
        """
        Poll credentialer.complete() until credential issuance completes.

        Args:
            app: Application instance
            said: Credential SAID to check
            timeout: Maximum seconds to wait

        Returns:
            bool: True if completed, False if timed out
        """
        start = asyncio.get_event_loop().time()
        while not app.agent.credentialer.complete(said):
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > timeout:
                logger.warning(f'Credential issuance timed out after {timeout}s for {said}')
                return False
            # Process escrows
            app.agent.rgy.processEscrows()
            await asyncio.sleep(0.5)
        return True
