# Copyright 1999-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DESCRIPTION="Valve's digital software delivery system - Jupiter bootstrapped packaging"
HOMEPAGE="https://steampowered.com/"
LICENSE="custom"

inherit xdg-utils


SLOT="0"
S=/var/tmp/portage/games-util/steam-jupiter-1.0.0.76-r1/work/

KEYWORDS="amd64"

IUSE="networkmanager"

RDEPEND="
	networkmanager? ( net-misc/networkmanager[abi_x86_32] )
"

SRC_URI="https://gitlab.com/evlaV/jupiter_steam-jupiter-stable-PKGBUILD/-/archive/master/jupiter_steam-jupiter-stable-PKGBUILD-master.tar.gz"

DEPEND="
	${RDEPEND}
	app-shells/bash
	dev-util/desktop-file-utils
	x11-themes/hicolor-icon-theme
	sys-libs/libxcrypt[compat,abi_x86_32,abi_x86_64]
	net-misc/curl
	sys-apps/dbus
	x11-libs/gdk-pixbuf:2
	media-libs/freetype:2
	dev-libs/nss[abi_x86_32,abi_x86_64]
	sys-apps/diffutils
	dev-lang/python
	sys-apps/lsb-release
	sys-apps/usbutils
	x11-apps/xrandr
	media-libs/vulkan-loader[abi_x86_32,abi_x86_64]
	sys-process/lsof
	gnome-extra/zenity
	x11-libs/libX11[abi_x86_32,abi_x86_64]
	x11-libs/libXScrnSaver[abi_x86_32,abi_x86_64]
	media-libs/fontconfig[abi_x86_32,abi_x86_64]
	sys-devel/gcc
	media-libs/libva[abi_x86_32,abi_x86_64]
	media-libs/mesa[abi_x86_32,abi_x86_64]
	dev-libs/libgpg-error[abi_x86_32,abi_x86_64]
	sys-apps/systemd[abi_x86_32,abi_x86_64]
	x11-libs/libXinerama[abi_x86_32,abi_x86_64]
	media-video/pipewire[abi_x86_32,abi_x86_64]
	media-plugins/alsa-plugins[abi_x86_32,abi_x86_64]
	!!games-util/steam
	!!games-util/steam-launcher
"

src_install() {
	cd ${WORKDIR}/jupiter_steam-jupiter-stable-PKGBUILD-master
	tar -xpzvf steam_1.0.0.76.tar.gz
	cd steam-launcher

	sed -r 's|("0666")|"0660", TAG+="uaccess"|g' -i subprojects/steam-devices/60-steam-input.rules
        sed -r 's|("misc")|\1, OPTIONS+="static_node=uinput"|g' -i subprojects/steam-devices/60-steam-input.rules
        sed -r 's|(, TAG\+="uaccess")|, MODE="0660"\1|g' -i subprojects/steam-devices/60-steam-vr.rules

	make DESTDIR="${D}" install
	install -Dm 755 "${WORKDIR}/jupiter_steam-jupiter-stable-PKGBUILD-master/steam-runtime.sh" "${D}/usr/bin/steam-runtime"
	install -Dm 755 "${WORKDIR}/jupiter_steam-jupiter-stable-PKGBUILD-master/steam-jupiter.sh" "${D}/usr/bin/steam-jupiter"
	install -d "${D}/usr/lib/steam"
	mv "${D}/usr/bin/steam" "${D}/usr/lib/steam/steam"
	ln -sf /usr/bin/steam-runtime "${D}/usr/bin/steam"
	install -Dm 644 COPYING steam_subscriber_agreement.txt -t "${D}/usr/share/licenses/${P}"
	install -Dm 644 debian/changelog -t "${D}/usr/share/doc/${P}"

	# blank steamdeps because apt-get
	ln -sf /usr/bin/true "${D}/usr/bin/steamdeps"

	# Jupiter
	# Install permissive input rules
	install -Dm 644 "${WORKDIR}/jupiter_steam-jupiter-stable-PKGBUILD-master/70-steam-jupiter-input.rules" "${D}/usr/lib/udev/rules.d/70-steam-jupiter-input.rules"

	# Jupiter
	# Replace the runtime with our own wrapper
	rm "${D}/usr/bin/steam-runtime"
	ln -sf /usr/bin/steam-jupiter "${D}/usr/bin/steam"

	# Replace bootstrapper with fat one
	rm "$D"/usr/lib/steam/bootstraplinux_ubuntu12_32.tar.xz
	install -Dm 644 "${WORKDIR}/jupiter_steam-jupiter-stable-PKGBUILD-master/steam_jupiter_stable_bootstrapped_20230316.1.tar.xz" "$D"/usr/lib/steam/bootstraplinux_ubuntu12_32.tar.xz
}

pkg_postinst() {
	xdg_desktop_database_update
}

pkg_postrm() {
	xdg_desktop_database_update
}
