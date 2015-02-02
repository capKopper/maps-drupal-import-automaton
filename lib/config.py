"""Configuration class."""
import argparse
import yaml


class ConfigError(Exception):

    """Configuration exception."""

    pass


class ConfigParserError(Exception):

    """Specific configuration exception on arguments parsing."""

    pass


class Config(object):

    """Defined a configuration."""

    def __init__(self, config_file):
        """Constructor."""
        self.file = config_file
        self.config = {}
        self.profile = ""
        if config_file is "":
            raise ConfigError("'config_file' is empty")

    def load(self):
        """Load application configuration file."""
        try:
            with open(self.file, 'r') as ymlfile:
                self.config = yaml.load(ymlfile)
        except IOError:
            raise ConfigError("configuration file '%s' not found" %
                              self.file)

    def parse_args(self):
        """Parser configuration."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--profile", "-p", help="profile")

        if parser.parse_args().profile is None:
            raise ConfigParserError("no profile specified")
        else:
            self.profile = parser.parse_args().profile

    def get_value(self, key):
        """Get the value of the specified key."""
        key_tab = key.split(".")
        try:
            if len(key_tab) == 1:
                value = self.config[key_tab[0]]
            elif len(key_tab) == 2:
                value = self.config[key_tab[0]][key_tab[1]]
        except KeyError:
                value = None

        return value
