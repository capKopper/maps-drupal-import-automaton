"""AlertTransport class."""
import abc
import smtplib


class AlertTransportInterface(object):

    """Abstract class definition."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def send(self):
        """Send an alert."""
        pass


class AlertTransportMail(AlertTransportInterface):

    """Implementation for a email alert."""

    def __init__(self, smtp_host, smtp_port,
                 smtp_user, smtp_password, smtp_starttls,
                 sender, recipients, subject, message, headers):
        """
        Constructor.

        Additionnal RFC 822 headers can be added:
        - each headers must be separated with the new line character
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_starttls = smtp_starttls
        self.sender = sender
        self.recipients = recipients
        self.subject = subject
        self.message = message
        self.additionnal_headers = headers

    def _connect(self):
        """Establish the connexion to the SMTP host."""
        smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
        smtp.ehlo()
        if self.smtp_starttls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(self.smtp_user, self.smtp_password)

        return smtp

    def send(self, override_message=None):
        """
        Send the message from 'sender' to 'recipients'.

        The 'default' email message can be override be 'override_message'.
        """
        # create the message in RFC 822 format.
        # - this include message headers like subject
        msg_rfc822 = ""
        msg_rfc822 += "MIME-Version: 1.0" + "\n"
        msg_rfc822 += "Subject: " + self.subject + "\n"
        msg_rfc822 += "Content-Type: text/plain" + "\n"
        msg_rfc822 += self.additionnal_headers + "\n"
        if override_message is None:
            msg_rfc822 += self.message
        else:
            msg_rfc822 += override_message
        # send the message
        smtp = self._connect()
        smtp.sendmail(self.sender, self.recipients, msg_rfc822)
        smtp.close()
