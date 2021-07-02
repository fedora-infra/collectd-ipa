# Collectd plugin for IPA

A Collectd plugin to extract metrics from IPA

Currently supported metrics:

- `groups`: the number of groups
- `users`: the number of users, active or disabled
- `users_rate`: the rate at which the number of users is changing (registered
  users and deletions)
- `staged_users`: the number of staged users (users in the process of
  registering for an account), split by their spam detection status.


## Installation

On the IPA host:

- install the python module where Collectd's python plugin can see it
- run `make install`

On the host where the collectd server is running:

- run `make install-data`
- append the content of `collection.conf` to your `/etc/collection.conf`


## Configuration

The `collectd.d/ipa.conf` file has an example of the available configuration
values that you can adjust, in the `Module collectd_ipa` block.

Note that if you change the collection interval, you'll have to recreate your
RRD files.

To accomodate clusters, all the metrics will be attached to a virtual host
named after your domain in IPA. The `domain_prefix` value allows you to add a
prefix to this domain.


## License

Licensed under [lgpl-3.0](./LICENSE)
