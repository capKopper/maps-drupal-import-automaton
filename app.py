#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Application."""
import errno
import sys

import lib.config as Config
import lib.drupal as Drupal
import lib.logger as Logger
import lib.profile as Profile
import lib.identifier as Identifier

# variables
cfg_file = "./config.yml"


def main():
    """Main process."""
    try:
        # init logger
        logger = Logger.configure()
        # parse arguments
        cfg = Config.Config(cfg_file)
        cfg.parse_args()
        # load configuration
        logger.info("loading configuration file (%s)" % cfg_file)
        cfg.load()

        # drupal checks
        drupal = Drupal.Drupal(cfg.get_value("drupal.root"), cfg.get_value("drupal.uri"))
        logger.info("checking if drush binary is installed")
        drupal.check_drush_bin()
        logger.info("checking that '%s' is a valid drupal instance" %
                    drupal.root)
        ## drupal.check_instance()

        # init profile
        pf = Profile.Profile(drupal, cfg.get_value("log.directory"), logger)
        # load given profile
        logger.info("loading profile")
        pf.load(cfg.config, cfg.profile)
        # profile checkings
        logger.info("checking source and target directories")
        pf.check_config_dir("source.directory")
        pf.check_config_dir("target.directory")
        logger.info("checking target config files")
        pf.check_config_file("target.objects")
        pf.check_config_file("target.config")
        #
        pf.get_state()
        logger.info("queuing...")
        todo_jobs = pf.queuing()
        logger.info("[todo] %s files has been added in the queue" %
                    todo_jobs)
        logger.info("[todo] processing...")
        pf.process_todo_q()


        # # debug
        # print "--------------------------"
        # print drupal.drush_bin
        # print drupal.root
        # print drupal.valid_instance
        # print pf.config
        # print pf.debug()
        # print "--------------------------"


    # fatal errors
    except (Config.ConfigError,
            Config.ConfigParserError,
            Drupal.DrushBinError,
            Drupal.DrupalInstanceError,
            Profile.ProfileError,
            Profile.ProfileKeyError,
            Profile.ProfileLoadError,
            Profile.ProfileCheckError,
            Profile.ProfileProcessingError) as e:
        logger.error(e)
        sys.exit(1)

main()
