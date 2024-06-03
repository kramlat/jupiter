# Copyright 1999-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8
DESCRIPTION="unlock/lock Steam Deck (jupiter) BIOS (AMD CBS/PBS)"
HOMEPAGE="https://gitlab.com/evlaV/jupiter-PKGBUILD"
SRC_URI=""
S="${WORKDIR}"
LICENSE="MPL"
SLOT="0"
KEYWORDS="amd64"

IUSE="c++ clang gcc"

DEPEND="
	clang? ( sys-devel/clang )
	gcc? ( sys-devel/gcc )
	virtual/libc
	sys-apps/grep
"

REQUIRED_USE="?? ( gcc clang )"

src_compile() {
	if use gcc; then
		if use c++; then
			g++ -O1 ${FILESDIR}/jupiter-bios-unlock.cc -o jupiter-bios-unlock
		else
			gcc -O1 ${FILESDIR}/jupiter-bios-unlock.c -o jupiter-bios-unlock
		fi
	elif use clang; then
		if use c++; then
			clang++ -O1 ${FILESDIR}/jupiter-bios-unlock.cc -o jupiter-bios-unlock
		else
			clang -O1 ${FILESDIR}/jupiter-bios-unlock.c -o jupiter-bios-unlock
		fi
	else
		die "this IUSE choice should be impossible. Please choose ony one of them: gcc or clang"
	fi
}

src_install() {
	install -Dm755 jupiter-bios-unlock "${D}/usr/bin/jupiter-bios-unlock"
	install -Dm644 ${FILESDIR}/LICENSE "${D}/usr/share/licenses/$pkgname/LICENSE"
}
