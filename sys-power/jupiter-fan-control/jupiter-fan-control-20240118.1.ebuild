# Copyright 1999-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8
DESCRIPTION="Jupiter fan controller"
HOMEPAGE="https://gitlab.steamos.cloud/jupiter/jupiter-fan-control/-/tree/20240118.1"
LICENSE="MIT"
SLOT="0"

SRC_URI="https://gitlab.com/evlaV/jupiter-fan-control/-/archive/20240118.1/jupiter-fan-control-20240118.1.tar.gz"

KEYWORDS="amd64"

BDEPEND="
	dev-vcs/git
	net-misc/rsync
	net-misc/openssh
"

S=/var/tmp/portage/sys-power/jupiter-fan-control-20240118.1/work

src_install() {
	rsync -a --exclude 'README.md' "${S}"/jupiter-fan-control-20240118.1/* "${D}"
}
