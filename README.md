# CUCWD fork of edx-platform

This is CUCWD's fork of https://github.com/edx/edx-platform

> The **master** branch of this repository is meaningless - do not
> refer to it nor use it as a base branch for changes to edx-platform.
> Always use the edx/edx-platform master branch as a
> starting point, or whatever other branch is appropriate.

We push branches here that are used for pull requests against
the upstream edx-platform repository or other forks. [Latest Open edX Release](https://edx.readthedocs.io/projects/edx-developer-docs/en/latest/named_releases.html#latest-open-edx-release)
is helpful to see how edX releases the platform releases. When deploying
releases to production we are using the version number tag release 
(e.g. `open-release/juniper.3`) rather than staying with the open release 
name main branch (e.g. `open-release/juniper.master`)

This fork also holds the cucwd branches for the edx-platform. Here 
is a structure on how we perform Gitflow and Pull Request (PR). Wherever
it says `name` it should be replace with Open edX named release (e.g. `juniper`):

- `cu-release/name.master`: changes from `open-release/name.master` branch + additional commits from cucwd. Not released to production instances to avoid confusion between multiple VMs in load balancer setup.
- `cu-release/name.#`: changes from `open-release/name.#` tag + additional commits from cucwd. This is released to production instances to avoid issue with load balancer setup of having every instance look the same.
- `open-release/name.master`: latest main branch of open named release. Start of cucwd development for this release. The `develop.name` branch is started from this release.
- `open-release/name.#`: latest versioned release tag of open named release. Not used for cucwd.
- `develop.name`: branched from `open-release.name.master` at start of release development; additional commits from `feature.name/EW-###-name` get committed here while in development.
- `feature.name/EW-###-name`: feature work in-progress. Push to remote `origin-cucwd` then make a PR to `develop.release`.

## Development Process for Open edX Release
1. `develop.name` is branched from `open-release/name.master` to start development.
2. `feature.name/EW-###-name` is branched from `develop.name` to start feature development for named release. Branch is pushed to remote `origin-cucwd` and a PR is initiated going from this branch to `develop.name`. Changes are reviewed then merged.
3. Once all changes for release are completed for development a `cu-release/name.master` branch is created from `develop.name` and pushed up to remote `origin-cucwd`.
4. Any commits that come after latest `open-release/name.#` are removed from `cu-release/name.master` and a tag `cu-release/name.#` is created. This will be the release that gets put in production.

