from ... import exceptions
from ...constants import KILLSWITCH_STATUS_TEXT, SUPPORTED_PROTOCOLS
from ...enums import (DisplayUserSettingsEnum, NetshieldTranslationEnum,
                      ProtocolEnum, ProtocolImplementationEnum,
                      UserSettingStatusEnum, ServerTierEnum)
from ...logger import logger
from .settings_configurator import SettingsConfigurator


class Settings:
    """Settings class.
    Use it to get and set user settings.

    Exposes methods:
        get_user_settings()
        reset_to_default_configs()

    Description:
        get_user_settings()
            Gets user settings, which include NetShield, Kill Switch,
            protocol and dns. Returns a dict with DisplayUserSettingsEnum keys.

        reset_to_default_configs()
            Reset users settings to default values.

    Properties:
        netshield
            Gets/Sets user Netshield setting.

        killswitch
            Gets/Sets user Kill Switch setting.

        protocol
            Gets/Sets user protocol setting.

        dns
            Gets/Sets user DNS setting.

        dns_custom_ips
            Gets/Sets users custom DNS list.
    """
    def __init__(self, settings_configurator=SettingsConfigurator()):
        self.settings_configurator = settings_configurator
        self.killswitch_obj = None
        self.protonvpn_user = None

    @property
    def netshield(self):
        """Get user netshield setting.

        Returns:
            NetshieldTranslationEnum
        """
        return self.settings_configurator.get_netshield()

    @netshield.setter
    def netshield(self, netshield_enum):
        """Set netshield to specified option.

        Args:
            netshield_enum (NetshieldTranslationEnum)
        """
        if (
            not netshield_enum
            and self.protonvpn_user.tier == ServerTierEnum.FREE
        ):
            raise Exception(
                "\nBrowse the Internet free of malware, ads, "
                "and trackers with NetShield.\n"
                "To use NetShield, upgrade your subscription at: "
                "https://account.protonvpn.com/dashboard"
            )

        self.settings_configurator.set_netshield(netshield_enum)

    @property
    def killswitch(self):
        """Get user Kill Switch setting.

        Returns:
            KillswitchStatusEnum
        """
        return self.settings_configurator.get_killswitch()

    @killswitch.setter
    def killswitch(self, killswitch_enum):
        """Set Kill Switch to specified option.

        Args:
            killswitch_enum (KillswitchStatusEnum)
        """
        try:
            self.killswitch_obj.update_from_user_configuration_menu(
                killswitch_enum
            )
        except exceptions.DisableConnectivityCheckError as e:
            logger.exception(e)
            raise Exception(
                "\nUnable to set kill switch setting: "
                "Connectivity check could not be disabled.\n"
                "Please disable connectivity check manually to be able to use "
                "the killswitch feature."
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception(e)
        except AttributeError:
            pass
        else:
            self.settings_configurator.set_killswitch(killswitch_enum)

    @property
    def protocol(self):
        """Get default protocol.

        Returns:
            ProtocolEnum
        """
        return self.settings_configurator.get_protocol()

    @protocol.setter
    def protocol(self, protocol_enum):
        """Set default protocol setting.

        Args:
            protocol_enum (ProtocolEnum)
        """
        logger.info("Setting protocol to: {}".format(protocol_enum))

        if not isinstance(protocol_enum, ProtocolEnum):
            logger.error("Select protocol is incorrect.")
            raise Exception(
                "\nSelected option \"{}\" is either incorrect ".format(
                    protocol_enum
                ) + "or protocol is (yet) not supported"
            )

        self.settings_configurator.set_protocol(
            protocol_enum
        )

        logger.info("Default protocol has been updated to \"{}\"".format(
            protocol_enum
        ))

    @property
    def dns(self):
        """Get user DNS setting.

        Args:
            custom_dns (bool):
            (optional) should be set to True
            if it is desired to get custom DNS values
            in a list.

        Returns:
            UserSettingStatusEnum
        """
        return self.settings_configurator.get_dns()

    @dns.setter
    def dns(self, setting_status):
        """Set DNS setting.

        Args:
            setting_status (UserSettingStatusEnum)
            custom_dns_ips (list): optional
        """
        if not isinstance(setting_status, UserSettingStatusEnum):
            raise Exception("Invalid setting status \"{}\"".format(
                setting_status
            ))

        try:
            self.settings_configurator.set_dns_status(setting_status)
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    @property
    def dns_custom_ips(self):
        """Get user DNS setting.

        Returns:
           list with custom DNS servers.
        """
        return self.settings_configurator.get_dns_custom_ip()

    @dns_custom_ips.setter
    def dns_custom_ips(self, custom_dns_ips):
        for dns_server_ip in custom_dns_ips:
            if not self.settings_configurator.is_valid_ip(dns_server_ip):
                logger.error("{} is an invalid IP".format(dns_server_ip))
                raise Exception(
                    "\n{0} is invalid. "
                    "Please provide a valid IP DNS server.".format(
                        dns_server_ip
                    )
                )
        self.settings_configurator.set_dns_custom_ip(custom_dns_ips)

    def reset_to_default_configs(self):
        """Reset user configuration to default values."""
        # should it disconnect prior to resetting user configurations ?
        try:
            self.__user_conf_manager.reset_default_configs()
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def get_user_settings(self, readeable_format):
        """Get user settings.

        Args:
            readeable_format (bool):
                If true then all content will be returnes in
                human readeable format, else all content is returned in
                enum objects.

        Returns:
            dict:
                Keys: DisplayUserSettingsEnum
        """
        settings_dict = {
            DisplayUserSettingsEnum.PROTOCOL: self.protocol,
            DisplayUserSettingsEnum.KILLSWITCH: self.killswitch,
            DisplayUserSettingsEnum.DNS: self.dns,
            DisplayUserSettingsEnum.CUSTOM_DNS: self.dns_custom_ips,
            DisplayUserSettingsEnum.NETSHIELD: self.netshield,
        }

        if not readeable_format:
            return settings_dict

        return self.__transform_user_setting_to_readable_format(settings_dict)

    def __transform_user_setting_to_readable_format(self, raw_format):
        """Transform the dict in raw_format to human readeable format.

        Args:
            raw_format (dict)

        Returns:
            dict
        """
        raw_protocol = raw_format[DisplayUserSettingsEnum.PROTOCOL]
        raw_ks = raw_format[DisplayUserSettingsEnum.KILLSWITCH]
        raw_dns = raw_format[DisplayUserSettingsEnum.DNS]
        raw_custom_dns = raw_format[DisplayUserSettingsEnum.CUSTOM_DNS]
        raw_ns = raw_format[DisplayUserSettingsEnum.NETSHIELD]

        # protocol
        if raw_protocol in SUPPORTED_PROTOCOLS[ProtocolImplementationEnum.OPENVPN]: # noqa
            transformed_protocol = "OpenVPN ({})".format(
                raw_protocol.value.upper()
            )
        else:
            transformed_protocol = raw_protocol.value.upper()

        # killswitch
        transformed_ks = KILLSWITCH_STATUS_TEXT[raw_ks]

        # dns
        dns_status = {
            UserSettingStatusEnum.ENABLED: "Automatic",
            UserSettingStatusEnum.CUSTOM: "Custom: {}".format(
                ", ".join(raw_custom_dns)
            ),
        }
        transformed_dns = dns_status[raw_dns]

        # netshield
        netshield_status = {
            NetshieldTranslationEnum.MALWARE: "Malware", # noqa
            NetshieldTranslationEnum.ADS_MALWARE: "Ads and malware", # noqa
            NetshieldTranslationEnum.DISABLED: "Disabled" # noqa
        }
        transformed_ns = netshield_status[raw_ns]

        return {
            DisplayUserSettingsEnum.PROTOCOL: transformed_protocol,
            DisplayUserSettingsEnum.KILLSWITCH: transformed_ks,
            DisplayUserSettingsEnum.DNS: transformed_dns,
            DisplayUserSettingsEnum.NETSHIELD: transformed_ns,
        }
