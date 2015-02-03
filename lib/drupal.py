"""Drupal tools."""
import os
import subprocess
import sys

import lib.tools as Tools


class Drupal(object):

    """Drupal installation status."""

    def __init__(self, drupal_root, drupal_uri):
        """Constructor."""
        self.root = drupal_root
        self.uri = drupal_uri
        self.drush_bin = ""
        self.valid_instance = False
        if drupal_root is None or drupal_root == "":
            raise DrupalInitError("'drupal_root' isn't defined")

    def check_drush_bin(self, drush_bin=None):
        """
        Check if the given 'drush_bin' is installed.

        If 'drush_bin' isn't defined, use the "which" shell commande
        to detect the right location of 'drush'
        """
        if drush_bin is not None:
            if os.path.isfile(drush_bin) and os.access(drush_bin, os.X_OK):
                self.drush_bin = drush_bin
            else:
                raise DrushBinError("given drush binary '%s' is not correct" %
                                    drush_bin)
        else:
            if Tools.which("drush") is not None:
                self.drush_bin = Tools.which("drush")
            else:
                raise DrushBinError("drush binary not detected")

    def check_instance(self):
        """Check if 'Drupal.root' if a valid drupal instance."""
        if os.path.isdir(self.root):
            drush_cmd = subprocess.Popen([self.drush_bin,
                                          "--root=" + self.root,
                                          "core-status", "version"],
                                         stdout=subprocess.PIPE)

            grep_cmd = subprocess.Popen(["grep", "-c", "Drupal version"],
                                        stdin=drush_cmd.stdout,
                                        stdout=subprocess.PIPE)

            drupal_found = grep_cmd.communicate()[0].strip('\n\r')

            if drupal_found == "1":
                self.valid_instance = True
            else:
                raise DrupalInstanceError("'%s' not a valid drupal instance" %
                                          self.root)
        else:
            raise DrupalInstanceError("directory '%s' doesn't exists" %
                                      self.root)


class DrupalInitError(Exception):

    """Specific exception raise when Drupal initialization isn't correctly."""

    pass


class DrushBinError(Exception):

    """Specific exception raise when the drush binary is not found."""

    pass


class DrupalInstanceError(Exception):
    pass




def check_drush_install(config, logger):
    """
    Check if drush binary is installed.

    First test the 'drush.path' value defined into configuration file.
    If this last isn't present set default to "which drush" command.
    """
    try:
        drush_bin = config["drush"]
        if os.path.isfile(drush_bin) and os.access(drush_bin, os.X_OK):
            logger.info("%s binary is installed." % "drush")
        else:
            logger.error("%s binary not installed. exiting..." % "drush")
            sys.exit(1)
    except KeyError:
        logger.info("no value for drush.path in config: set to default value")
        if Tools.which("drush") is not None:
            drush_bin = Tools.which("drush")
            logger.info("=> %s" % drush_bin)
        else:
            logger.error("%s binary not installed. exiting..." % "drush")
            sys.exit(1)

    return drush_bin


def check_drupal_instance(config, drush_bin, logger):
    """Test if 'drupal.root' is a drupal instance."""
    try:
        drupal_root = config["drupal"]["root"]
        if os.path.isdir(drupal_root):
            logger.info("checking '%s'" % drupal_root)
            drush_cmd = subprocess.Popen([drush_bin, "--root=" + drupal_root,
                                         "core-status", "version"],
                                         stdout=subprocess.PIPE
                                        )

            grep_cmd = subprocess.Popen(["grep", "-c", "Drupal version"],
                                        stdin=drush_cmd.stdout,
                                        stdout=subprocess.PIPE
                                       )

            drupal_found = grep_cmd.communicate()[0].strip('\n\r')
            return Tools.str_to_bool(drupal_found)
        else:
            logger.error("%s not a directory. exiting..." % drupal_root)
            sys.exit(1)
    except KeyError:
        logger.error("not value for drupal.root in config. exiting...")
        sys.exit(1)
