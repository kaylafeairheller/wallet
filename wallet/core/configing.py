import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('wallet')

DEFAULT_USERNAME = 'work'
DEFAULT_PASSCODE = 'DoB26Fj4x9LboAFWJra17O'
DEFAULT_WITNESS_POOL_PATH = './conf/witness-pools-production.json'
DEFAULT_AGENT_CONFIG_DIR = './conf/production'  # Demo witnesses used with `kli witness demo`.
DEFAULT_AGENT_CONFIG_FILE = 'production'  # Demo witness config file with demo witnesses and vLEI schema OOBIs


class Environments(Enum):
    PRODUCTION = 'production'
    STAGING = 'staging'
    DEVELOPMENT = 'development'


@dataclass
class WalletConfig:
    app_name = 'Sparán'
    # Flet assets directory for pictures, fonts, and the like.
    assets_dir: str = './assets'
    # The specific font to use from the fonts subdirectory within the assets_dir.
    font: str = 'fonts/SourceCodePro-Light.ttf'
    # The KERI configuration file directory for both witness definitions and inception file config
    config_dir: str = DEFAULT_AGENT_CONFIG_DIR
    # The specific configuration file to use for configuring the agent keystore when creating an agent
    config_file: str = DEFAULT_AGENT_CONFIG_FILE
    # The JSON file to retrieve the witness pool options from.
    witness_pool_path: str = DEFAULT_WITNESS_POOL_PATH
    # The environment the app is being run in.
    environment: Environments = Environments.PRODUCTION


def read_config():
    environment = os.environ.get('WALLET_ENVIRONMENT')
    match environment:
        case Environments.PRODUCTION.value:
            environment = Environments.PRODUCTION
        case Environments.STAGING.value:
            environment = Environments.STAGING
        case Environments.DEVELOPMENT.value:
            environment = Environments.DEVELOPMENT
        case _:
            environment = Environments.PRODUCTION
    logger.info(f'Running in the {environment} environment')

    wit_pool_path_var = os.environ.get('WITNESS_POOL_PATH')
    config_dir_var = os.environ.get('KERI_CONFIG_DIR')
    config_file_var = os.environ.get('KERI_AGENT_CONFIG_FILE')

    # Set defaults for each environment, and default env is production
    match environment:
        case Environments.PRODUCTION:
            wit_pool_path = './conf/witness-pools-production.json'
            config_dir = './conf/production'
            config_file = 'production'
        case Environments.STAGING:
            wit_pool_path = './conf/witness-pools-staging.json'
            config_dir = './conf/staging'
            config_file = 'staging'
        case Environments.DEVELOPMENT:
            wit_pool_path = './conf/local/keri/cf/local.json'
            config_dir = './conf/local'
            config_file = 'local'
        case _:
            wit_pool_path = './conf/witness-pools-production.json'
            config_dir = './conf/production'
            config_file = 'production'

    # Allow for overrides
    if wit_pool_path_var is not None:
        wit_pool_path = wit_pool_path_var
    if config_dir_var is not None:
        config_dir = config_dir_var
    if config_file_var is not None:
        config_file = config_file_var

    config = WalletConfig()
    config.config_dir = config_dir
    config.config_file = config_file
    config.witness_pool_path = wit_pool_path
    config.environment = environment
    return config
