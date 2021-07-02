.PHONY: install install-data
PYTHON_SITELIB=$(shell python3 -Esc "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
DATADIR = $(INSTALL_ROOT)/usr/share/collectd
CONFDIR = $(INSTALL_ROOT)/etc/collectd.d

install: install-data $(CONFDIR)/ipa.conf
install-data: $(DATADIR)/ipa-types.db $(CONFDIR)/ipa-data.conf

$(DATADIR)/ipa-types.db: types.db
	install -D -m 644 $< $@

$(CONFDIR)/%.conf: collectd.d/%.conf
	install -D -m 644 $< $@
