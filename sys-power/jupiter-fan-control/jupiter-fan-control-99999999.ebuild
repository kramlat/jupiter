# Copyright 1999-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8
DESCRIPTION="Jupiter fan controller"
HOMEPAGE="https://gitlab.steamos.cloud/jupiter/jupiter-fan-control/"
LICENSE="MIT"
SLOT="0"

SRC_URI="https://gitlab.com/evlaV/jupiter-fan-control/-/archive/main/jupiter-fan-control-main.tar.gz"

KEYWORDS="~amd64"

BDEPEND="
	dev-vcs/git
	net-misc/rsync
	net-misc/openssh
"

S=/var/tmp/portage/sys-power/jupiter-fan-control-99999999/work

src_install() {
	rsync -a --exclude 'README.md' "${S}"/jupiter-fan-control-main/* "${D}"
}
