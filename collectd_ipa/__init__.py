import os
import re
from configparser import ConfigParser

import collectd
import ldap
from ldap.controls.pagedresults import SimplePagedResultsControl


CONFIG = {
    "Interval": "3600",
    "DomainPrefix": "ipa.",
    "IpaConf": "/etc/ipa/default.conf",
    "LdapConf": "/etc/openldap/ldap.conf",
}


class LDAPClient:
    def __init__(self, config_path):
        self._config_path = config_path
        self.config = {}
        self.conn = None
        self._read_config()

    def _read_config(self):
        conf_re = re.compile(r"^([A-Z_]+)\s+(.+)$")
        with open(self._config_path) as cf:
            for line in cf:
                mo = conf_re.match(line.strip())
                if mo is None:
                    continue
                variable = mo.group(1)
                value = mo.group(2)
                self.config[variable] = value

    def connect(self):
        self.conn = ldap.initialize(self.config["URI"].split(" ")[0])
        self.conn.protocol_version = 3
        self.conn.sasl_gssapi_bind_s(authz_id="")

    def search(self, base, filters, attrs):
        page_size = 1000
        base_dn = f"{base},{self.config['BASE']}"
        page_cookie = ""
        results = []
        while True:
            page_control = SimplePagedResultsControl(
                criticality=False, size=page_size, cookie=page_cookie
            )
            msgid = self.conn.search_ext(
                base_dn,
                ldap.SCOPE_SUBTREE,
                filters,
                attrlist=attrs,
                serverctrls=[page_control],
            )
            rtype, rdata, rmsgid, serverctrls = self.conn.result3(msgid)
            results.extend(obj for dn, obj in rdata)
            for ctrl in serverctrls:
                if isinstance(ctrl, SimplePagedResultsControl):
                    page_cookie = ctrl.cookie
                    break
            if not page_cookie:
                break
        return results

    def count_groups(self):
        filters = "(objectclass=fasGroup)"
        return len(
            self.search(base="cn=groups,cn=accounts", filters=filters, attrs=["dn"])
        )

    def _get_users(self, base, attrs=None):
        filters = "(objectclass=fasUser)"
        response = self.search(base=base, filters=filters, attrs=attrs or [])
        return response

    def count_users(self):
        users = self._get_users("cn=users,cn=accounts", ["nsAccountLock"])
        results = {
            "active": 0,
            "locked": 0,
        }
        for u in users:
            status = (
                "locked"
                if u.get("nsAccountLock", [b"FALSE"])[0].decode("ascii") == "TRUE"
                else "active"
            )
            results[status] += 1
        return results

    def count_staged_users(self):
        users = self._get_users(
            "cn=staged users,cn=accounts,cn=provisioning", ["fasStatusNote"]
        )
        results = {
            "active": 0,
            "spamcheck_awaiting": 0,
            "spamcheck_denied": 0,
            "spamcheck_manual": 0,
        }
        for u in users:
            if "fasStatusNote" not in u:
                continue
            status = u["fasStatusNote"][0].decode("ascii")
            if status not in results:
                collectd.warning(f"Unknown FAS status: {status!r}")
                continue
            results[status] += 1
        return results


class Collector:
    def __init__(self, config):
        self.config = config
        self.client = LDAPClient(config_path=self.config["LdapConf"])
        self.ipa_config = self._read_ipa_conf()

    def _read_ipa_conf(self):
        conf = ConfigParser(interpolation=None)
        conf.read(self.config["IpaConf"])
        return dict(conf.items("global"))

    @property
    def vhost(self):
        prefix = self.config["DomainPrefix"]
        try:
            domain = self.ipa_config["domain"]
        except KeyError:
            return None
        return f"{prefix}{domain}"

    def setup(self):
        self.client.connect()

    def collect(self):
        # Groups
        self._dispatch(self.client.count_groups(), "groups")
        # Users
        self._dispatch_by_status("staged_users", self.client.count_staged_users())
        users = self.client.count_users()
        self._dispatch_by_status("users", users)
        self._dispatch(users["active"], "users_rate", category="users")

    def _dispatch_by_status(self, name, results):
        collectd.debug("Dispatching {}: {!r}".format(name, dict(results)))
        for status, count in results.items():
            self._dispatch(count, name, status, category="users")

    def _dispatch(self, value, name, subname=None, category=None):
        vl = collectd.Values()
        vl.type = f"ipa_{name}"
        vl.plugin = category or name
        vl.host = self.vhost
        if subname is not None:
            vl.type_instance = subname
        if not hasattr(value, "__iter__"):
            value = [value]
        vl.dispatch(values=value)


def configure(plugin_config):
    config = CONFIG.copy()
    for conf_entry in plugin_config.children:
        collectd.debug(f"{conf_entry.key} = {conf_entry.values}")
        try:
            if conf_entry.key == "SetEnv":
                envvar, value = conf_entry.values
                os.environ[envvar] = value
            else:
                if len(conf_entry.values) != 1:
                    raise ValueError
                config[conf_entry.key] = conf_entry.values[0]
        except ValueError:
            collectd.warning(
                f"Invalid configuration value for {conf_entry.key}: {conf_entry.values!r}"
            )
            continue

    collector = Collector(config=config)
    collectd.register_init(collector.setup)
    collectd.register_read(collector.collect, int(config["Interval"]))


collectd.register_config(configure)
