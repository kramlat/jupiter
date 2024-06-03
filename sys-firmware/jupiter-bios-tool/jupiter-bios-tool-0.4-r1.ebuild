EAPI=8
DESCRIPTION="analyze, verify, backup/generate/inject UID, and dynamically trim any/all Steam Deck (jupiter) BACKUP and RELEASE BIOS images"
HOMEPAGE="https://gitlab.com/evlaV/jupiter-PKGBUILD"
SRC_URI=""
S="${WORKDIR}"
LICENSE="MPL"
SLOT="0"

KEYWORDS="amd64"
IUSE="detect-serial-number"

DEPEND="
	detect-serial-number? ( sys-apps/coreutils )
	app-shells/bash
	dev-lang/python
"

BDEPEND="sys-apps/coreutils"

src_install() {
	install -Dm755 $FILESDIR/jupiter-bios-tool.py "$D/usr/bin/jupiter-bios-tool"
	install -Dm755 $FILESDIR/jupiter-detect-unsupported-hw.sh "$D/usr/bin/jupiter-detect-unsupported-hw"
	install -Dm644 $FILESDIR/LICENSE "$D/usr/share/licenses/$P/LICENSE"
}
