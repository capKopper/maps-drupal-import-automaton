"""Profile definition."""
import datetime
import errno
import json
import os
import tarfile
import shutil
import subprocess
import re

from lib.tools import add_symlink
from lib.identifier import SourceIdentifierInterface as SourceIdentifierInterface
from lib.identifier import SourceIdentifierTimestamp as SourceIdentifierTimestamp

class ProfileError(Exception):

    """Common exception."""

    pass


class ProfileLoadError(Exception):

    """Specific loading exception."""

    pass


class ProfileCheckError(Exception):

    """Configuration checking exception."""

    pass


class ProfileKeyError(Exception):

    """Retrieve key from config exception."""

    pass


class ProfileProcessingError(Exception):

    """Processing exception."""

    pass


class ProfileProcessingError(Exception):

    """Processing exception."""

    pass


class Profile(object):

    """Defined a importation profile."""

    def __init__(self, drupal, log_dir, logger):
        """Constructor."""
        self.id = 0
        self.alias = ""
        self.config = {}
        self.lock_file = ""
        self.state_file = ""
        self.state_timestamp = "0"
        self.source_object_files = 0
        self.log_dir = log_dir
        # queues
        self.todo_queue = []
        self.active_queue = []
        # external "components"
        self.logger = logger
        self.drupal = drupal

    def load(self, config, profile_key):
        """
        Check if the specified profile exists into config.

        The profile can be access by his 'id' or his 'alias'.
        - We need to detect the type of the profile access and
        than "cast" it to the right type (integer or string).
        """
        # a none numeric argument is supposed to be 'alias'
        if re.search(r"\b[0-9]+\b", profile_key) is None:
            key = profile_key
            self.alias = key
            access_by = "alias"
        else:
            key = (int)(profile_key)
            self.id = key
            access_by = "id"
        self.logger.debug("profile will be access by his '%s'" % access_by)

        # check if the profile exists into config...
        i = 0
        profile_found = False
        while (i < len(config["profiles"])
               and profile_found is False):

            if config["profiles"][i][access_by] == key:
                profile_found = True
                self.logger.debug("profile '%s' found (access by '%s')" %
                      (key, access_by))
                self.config = config["profiles"][i]

            i += 1

        # ... and if not raise an exception
        if profile_found is False:
            raise ProfileLoadError("profile '%s' not found" % profile_key)

        # set profile properties
        self.id = self.config["id"]
        self.alias = self.config["alias"]
        self.state_file = os.path.join(config["state_dir"],
                                       self.config["alias"] + ".json")
        self.lock_file = os.path.join(config["state_dir"],
                                      self.config["alias"] + ".lock")

    def check_config_dir(self, directory):
        """
        Check the presence the given directory.

        First test if the directory is defined into the profile configuration.
        If yes, test if this parameter is a directory
        """
        (var1, var2) = directory.split(".")
        try:
            d = self.config[var1][var2]
            if os.path.isdir(d) is False:
                raise ProfileCheckError("'%s' isn't a directory" % d)

        except KeyError:
            raise ProfileKeyError("no value for '%s'" % directory)

    def check_config_file(self, file):
        """Check the given file is absent or is a symlink."""
        (var1, var2) = file.split(".")
        try:
            f = os.path.join(self.config[var1]["directory"],
                             self.config[var1][var2])
            if os.path.exists(f) or os.path.lexists(f):
                if os.path.islink(f) is False:
                    raise ProfileCheckError("'%s' is in a bad config" % f)

        except KeyError:
            raise ProfileKeyError("no value for %s.%s" % (var1, var2))

    def get_state(self):
        """
        Get the profile's state.

        This information is store into a .json file.
        - current state is the last succeed file 'timestamp'.
        """
        try:
            json_data = open(self.state_file)
            data = json.load(json_data)
            self.state_timestamp = data["timestamp"]
            json_data.close()

        except IOError:
            self.logger.info("'%s' not found: an initial state file will be create" % \
                             self.state_file)
            data = {"timestamp": self.state_timestamp}
            with open(self.state_file, 'w') as out_file:
                json.dump(data, out_file, indent=4)
            out_file.close()

    def queuing(self):
        """
        Add source 'objects' files into the [todo] queue.

        Find all the new source 'objects' files that need to be process.
        For this we:
        - filter files into the 'src_dir' according to the param pattern
        - compare the current profile's state to the filename
        """
        try:
            src_dir = self.config["source"]["directory"]
            # get the filter pattern
            src_obj_filter = self._source_filter()
            self.logger.debug("filter => '%s'" % src_obj_filter)
            # put valid files into [todo] queue
            for f in os.listdir(src_dir):
                is_object_file = re.match(r'%s' % src_obj_filter, f)
                if is_object_file:
                    self.source_object_files += 1
                    if is_object_file.group(1) > self.state_timestamp:
                        item = {"id": is_object_file.group(1),
                                "objects_filename": os.path.join(src_dir, f)}
                        self.todo_queue.append(item)

            return len(self.todo_queue)

        except KeyError:
            raise ProfileError("no value found for source.directory")

    def _source_filter(self):
        """Return the filter pattern."""
        param_id = self._detect_source_params()
        cls_str = self._detect_source_param_class(param_id)
        if cls_str is None:
            raise ProfileError("parameter '%s' isn't defined in config" %
                               param_id)
        else:
            self.logger.debug("source objects class => '%s'" % cls_str)
            cls = globals()[cls_str]
            instance = cls(param_id, "$", self.config["source"]["objects"])
            return instance.get_pattern()

    def _detect_source_params(self):
        """
        Return the first parameter present into the source.objects definition.

        Identifier start with the '$' character and can containt
        - minus alphabeticalic character (a-z)
        - underscore character '_'
        - hyphen character '-'
        If others parameters are present they are ignored
        """
        src_obj_def = self.config["source"]["objects"]
        id_pattern = r"\w+\$([a-z_-]+)(\$.*)?\.xml"
        regex_id = re.match(r'%s' % id_pattern, src_obj_def)
        # strip the last character of the first parameter when
        # others arguments are present
        if regex_id.group(2) is None:
            first_param = regex_id.group(1)
        else:
            first_param = regex_id.group(1)[:-1]

        return first_param

    def _detect_source_param_class(self, param):
        """Return the class associated with the given param."""
        if self.config["source"]["parameter"]["name"] == param:
            return self.config["source"]["parameter"]["class"]
        else:
            return None

    def process_todo_q(self):
        """
        Processing the [todo] queue.

        For all the tasks into the [todo] queue:
          1. add the next [todo] task to the [active] queue
          2. check if a config file is present for the [active] job
          3. set target symlinks
        """
        self.logger.info("[todo] %s files to process" % len(self.todo_queue))

        while len(self.todo_queue) > 0:
            if len(self.active_queue) == 0:
                # add job to [active] queue...
                self.active_queue.append(self.todo_queue.pop(0))
                job_id = self.active_queue[0]["id"]
                # ...log his 'id'...
                self.logger.info("[active/%s] processing file '%s'"
                                  % (job_id,
                                     self.active_queue[0]["objects_filename"]))
                # ...and process it
                has_config, cfg_file = self._check_object_config()
                if has_config:
                    self.logger.debug("[active/%s] config file '%s' is present"
                                      % (job_id,
                                         cfg_file))
                    self._set_target_symlinks()
                    self._run_operations()
                else:
                    # # TODO: if no file is found send an email
                    # # TODO: blocking error ?
                    self.logger.error("[active/%s] config file '%s' is absent"
                                     % (job_id,
                                        cfg_file))
                    self.logger.error("=> **TODO: send an email**")

                # remove the job from the [active] queue
                self.active_queue = []
            else:
                raise ProfileProcessingError("only one job is permitted \
                                              in [active] queue")

        self.logger.debug("[todo] all files has been processed")

    def _check_object_config(self):
        """
        Check to that current active job 'object' file has a 'config'.

        Returns:
        - True if the file exists, else False
        - the absolute path of the 'config' file
        """
        src_cfg_format = self.config["source"]["config"]

        job = self.active_queue[0]
        src_cfg_file = os.path.join(os.path.dirname(job["objects_filename"]),
                                    src_cfg_format.replace("$id", job["id"]))
        job["config_filename"] = src_cfg_file

        return os.path.isfile(src_cfg_file), src_cfg_file

    def _set_target_symlinks(self):
        """Set target symlinks to current active files (objects and config)."""
        try:
            job_id = self.active_queue[0]["id"]
            tgt_dir = self.config["target"]["directory"]
            for t in ["objects", "config"]:
                src = self.active_queue[0][t + "_filename"]
                tgt = os.path.join(tgt_dir, self.config["target"][t])
                # force symlink creation
                add_symlink(src, tgt, True)
                self.logger.debug("[active/%s] set symlink: '%s' -> '%s'"
                                  % (job_id, tgt, src))

        except KeyError:
            raise ProfileKeyError("no value for target.directory")

    def _run_operations(self):
        """
        Run all the operations for the [active] job.

        For each operation
        - acquire a lock
        - run the operations
        - release the lock

        A the end of the process, we archive a given directory and some files.
        Generally this directory is the logdir of all operations.
        """
        # get job informations
        job = self.active_queue[0]
        job_id = job["id"]
        job_logdir = self._create_logdir(job_id)

        for operation in self.config["operations"]:
            self._acquire_lock(job_id + "," + operation)
            self._run_operation(operation, job_logdir)
            self._release_lock(job_id + "," + operation)

        files_to_archives = [job["objects_filename"], job["config_filename"]]
        self._archive_logs(job_logdir, files_to_archives)
        self._update_state(job_id)

    def _create_logdir(self, job_id):
        """Create and return the log directory for the given 'job_id'."""
        job_logdir = os.path.join(self.log_dir, self.alias, job_id)
        if not os.path.isdir(job_logdir):
            self.logger.debug("creating log directory '%s'" % job_logdir)
            os.makedirs(job_logdir)

        return job_logdir

    def _acquire_lock(self, job_info):
        """Acquire the lock file."""
        if os.path.exists(self.lock_file):
            raise ProfileProcessingError("lock file '%s' already exists" %
                                         self.lock_file)
        else:
            f = open(self.lock_file, 'w')
            f.write(job_info)
            f.close()
            self.logger.debug("lock acquire for '%s'" % job_info)

    def _release_lock(self, job_info):
        """Release the lock file."""
        os.remove(self.lock_file)
        self.logger.debug("lock release for '%s'" % job_info)

    def _run_operation(self, operation, logdir):
        """
        Run the given operation.

        Use drush binary.
        """
        op_start_time = datetime.datetime.now()
        drush_cmd = subprocess.Popen([self.drupal.drush_bin,
                                      "--root=" + self.drupal.root,
                                      "--uri=" + self.drupal.uri,
                                      "maps-import",
                                      str(self.id),
                                      "--op=" + operation],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        (drush_out, drush_err) = drush_cmd.communicate()
        op_end_time = datetime.datetime.now()

        self._log_operation(operation, logdir,
                             drush_out, drush_err)
        self._update_operation_state(operation, op_start_time, op_end_time)

    def _log_operation(self, operation, logdir, stdout, stderr):
        """Log the operations results."""
        self.logger.debug("log operation results")
        # log filenames
        log_file = os.path.join(logdir, operation + ".log")
        err_file = os.path.join(logdir, operation + "-err.log")
        # always log stdout
        self.logger.info("complete informations in '%s'" % log_file)
        log = open(log_file, "w")
        log.write(stdout)
        log.close()
        # only log if there is errors
        if stderr is not "":
            self.logger.warning("errors are logged in '%s'" % err_file)
            err = open(err_file, "w")
            err.write(stderr)
            err.close()

    def _update_operation_state(self, operation, start_time, end_time):
        """Update the operation state in global profile state."""
        self.logger.info("updating '%s' operation in profile state" %
                         operation)
        # get current profile state ...
        with open(self.state_file, "r") as json_current:
            state = json.load(json_current)
            json_current.close()
        # ..., create "succeded_operations" object if not exists...
        try:
            _ = state["succeded_operations"]
        except KeyError:
            state["succeded_operations"] = {}
        # ... and also create the operation if not exists
        try:
            _ = state["succeded_operations"][operation]
        except KeyError:
            state["succeded_operations"][operation] = {}

        # update state
        start_time_iso8601 = start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        end_time_iso8601 = end_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        op_status = {}
        op_status["start_time"] = start_time_iso8601
        op_status["end_time"] = end_time_iso8601
        op_status["duration"] = str(end_time-start_time)
        op_status["file"] = self.active_queue[0]["objects_filename"]
        state["succeded_operations"][operation] = op_status
        # write to file
        with open(self.state_file, 'w') as out_file:
            json.dump(state, out_file, indent=4)
        out_file.close()

    def _update_state(self, job_id):
        """
        Update the timestamp in the profile state file.

        This action only occurred when all the operations succeded.
        """
        self.logger.info("updating 'timestamp' in profile state")
        # get current state ...
        with open(self.state_file, "r") as json_current:
            state = json.load(json_current)
            json_current.close()
        # ... and write new timestamp
        with open(self.state_file, "w") as json_new:
            state["timestamp"] = job_id
            json.dump(state, json_new, indent=4, sort_keys=True)
            json_new.close()

    def _archive_logs(self, logdir, files):
        """Archive job logs and source files."""
        cwd = os.getcwd()
        archive_wd = os.path.dirname(logdir)
        archive_file = os.path.basename(logdir) + ".tgz"

        # move files into logdir for archive
        for f in files:
            self.logger.info("moving '%s' to archive folder" % f)
            shutil.move(f, logdir)

        # move to logdir parent folder
        self.logger.info("archiving profile logs into '%s'" % archive_file)
        os.chdir(archive_wd)
        archive = tarfile.open(archive_file, "w:gz")
        archive.add(os.path.basename(logdir))
        archive.close()

        # go back to current working dir and remove logdir
        os.chdir(cwd)
        shutil.rmtree(logdir)













    def debug(self):
        """Debug information."""
        print "id: %s" % self.id
        print "alias: %s" % self.alias
        print "state_file: %s" % self.state_file
        print "state_timestamp: %s" % self.state_timestamp
        print "source_object_files: %s" % self.source_object_files
