import asyncio
import datetime
import logging

from keri.db import basing
from keri.help import helping

from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class OOBIResolverService:
    def __init__(self, app):
        """
        Creates the service for resolving an oobi.

        Attributes:
            app(WalletApp): The app that will be used to resolve the oobi
            org(Organizer): The KERIpy Organizer containing contacts for resolved OOBIs
        """
        self.app = app
        self.org = app.agent.org
        super().__init__()

    @log_errors
    async def resolve_oobi(self, pre: str = None, oobi: str = None, force=False, alias=None):
        """
        Resolves an OOBI with the connected Agent's Habery and recreates the full contact data in Organizer.
        This includes a workaround because resolving an OOBI resets all attributes for a contact including the alias.

        Parameters:
            pre (str): The AID prefix of the target AID to resolve the OOBI against.
                Can also be an alias if the alias is unique.
            oobi (str): The OOBI url to resolve
            force (bool): If true, the existing OOBI resolution will be cleared and re-resolved
        """
        if not pre and not alias:
            logger.error('OOBI resolve failed: pre and alias are empty')
            return False
        contact = self.org.get(pre) if pre else None
        if not contact:
            contacts = self.org.find('alias', alias)
            if len(contacts) == 1:
                contact = contacts[0]
            if not contact:
                contact = {
                    'alias': alias,
                }
        obr = basing.OobiRecord(date=helping.nowIso8601())
        obr.oobialias = alias if alias else pre

        if pre is None and alias is None or oobi is None:
            logger.error(f'OOBI resolve failed: alias ({alias}) or oobi ({oobi}) is empty')
            return False

        if force:
            self.app.hby.db.roobi.rem(keys=(oobi,))

        start_time = helping.nowUTC()
        timeout_delta = datetime.timedelta(seconds=15)
        try:
            self.app.hby.db.oobis.put(keys=(oobi,), val=obr)
            while not self.app.hby.db.roobi.get(keys=(oobi,)):
                if helping.nowUTC() > start_time + timeout_delta:
                    logger.info('OOBI resolve timeout')
                    return False
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f'OOBI Resolution failed for alias {alias} and OOBI {oobi}: {e}')
            return False

        if not pre:  # prefix will not be provided if alias is used, so after resolution look up prefix from contacts
            cts = self.org.find('alias', alias)
            if len(cts) > 1:
                logger.error(f'OOBI resolve failed: multiple contacts found for alias {alias}')
                return False
            pre = cts[0]['id']
            print("PRINTING AID? ", pre)
            print("PRINTING CONTACT ? ", cts[0])
        contact['last-refresh'] = helping.nowIso8601()
        self.org.update(pre, contact)
        logger.info(f'OOBI resolved: {alias} {oobi}')
        return True
