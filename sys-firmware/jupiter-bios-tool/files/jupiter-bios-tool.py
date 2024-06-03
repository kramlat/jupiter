#!/usr/bin/env python
# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL
# was not distributed with this file, You can obtain one
# at https://mozilla.org/MPL/2.0/.

"""
Steam Deck (Jupiter) BIOS Tool

Automatically analyze, verify, backup/generate/inject UID, and dynamically trim
any/all Steam Deck (jupiter) BACKUP and RELEASE BIOS (*_sign.fd) (>0x1000000)
images to 0x1000000 for hardware flashing/programming to a Winbond W25Q128JW
128Mb (16MB) Serial NOR Flash.
"""

# minimum      :  Python 2.6+/3.1+ (requires backported module: argparse)
# recommended  :  Python 2.7+/3.2+

# pylint: disable=C

import argparse
import base64
import os
import random
import string
import sys

ver = '0.4'
cyr = '2022-2023'

# BIOS version
rel_bios_ver_f7g = 'F7G0105'
rel_bios_ver_f7a = 'F7A0119'
# compare/match offset(s) from bios_offset_list
detect_rel_bios_ver = None
# detected BIOS image version/offset
bios_ver = None
bios_ver_offset = None
# detected BIOS image version offset - overrides bios_ver/bios_ver_offset
bios_ver_offset_str = None
bios_ver_offset_str_f7g = b'$Chachani-SPH'
bios_ver_offset_str_f7a = b'$CHACHANI-VANGOGH'
bios_ver_offset_str_offset = -0x18
bios_ver_size = 0x7
tbios_ver_size = 0x3
# bios_ver_size + tbios_ver_size (T[??])
#bios_ver_size = 0xa
# detected BIOS image revision/date/offset
ec_rev = None
ec_rev_offset = None
ec_date = None
ec_date_offset = None
bios_date = None
bios_date_offset = None
# detected BIOS image revision/date offset - overrides ec_rev/ec_rev_offset/ec_date/ec_date_offset/bios_date/bios_date_offset
ec_rev_offset_str = None
ec_rev_offset_str_offset = None
ec_rev_size = None
ec_date_offset_str_offset = None
ec_date_size = None
# EC string/offset tuple list [(ec_rev_offset_str, ec_rev_offset_str_offset, ec_rev_size, ec_date_offset_str_offset, ec_date_size)]
ec_offset_list = [
    # F7G0020+ (date and time)
    (b'F7G\x00ITE-81302', -0x18, 0x6, -0x10, 0xf),
    # F7G0020+ (date)
    #(b'F7G\x00ITE-81302', -0x18, 0x6, -0x10, 0xa),
    # F7G0014T20
    (b'F7G\x00ITE-81302', -0x14, 0x6, -0xc, 0xa),
    # F7G0005-F7G0013
    #(b'ITE-81302', -0x16, 0x6, -0xf, 0xa),
    (b'F7G ITE-81302', -0x12, 0x6, -0xb, 0xa),
    # F7A*
    #(b'Jupiter', -0x1d, 0x6, -0xf, 0xa)]
    #(b'F7A Jupiter', -0x19, 0x6, -0xb, 0xa)]
    (b'F7A Jupiter\x00ITE 5570', -0x19, 0x6, -0xb, 0xa)]
# bios_ver_offset_str instead of bios_date_offset_str
#bios_date_offset_str_offset = 0x13b
bios_date_offset_str = b'$RDATE'
#bios_date_offset_str_offset = 0x6
bios_date_offset_str_offset = len(bios_date_offset_str)
bios_date_size = 0x3

# header
#rel_header = b'\x4d\x5a'
rel_header = b'MZ'
bios_header = None
bios_header_f7a = b'\x02\x02\x00\x02\x28'
bios_header_f7g = b'\x02'

# offset
# RELEASE BIOS byte size tuple list - [(byte_size_int, str)]
rel_bios_size_list = [
    (0x10f48f8, 'F7G0020-%s(-???????) (F7G0020+)' % rel_bios_ver_f7g),
    (0x10f48c8, 'F7A0102-%s(-???????) (F7A0102+) or F7G0005-F7G0014' % rel_bios_ver_f7a),
    (0x1188908, 'Test2 (Test2_sign.fd)/F7A0006-F7A0101'),
    (0x11888d8, 'Test1 (Test1_sign.fd)')]
# BIOS offset tuple list - [(offset_int, str)]
bios_offset_list = [
    (0xe8c70, 'F7A0102-%s(-???????) (F7A0102+) or F7G0005-%s(-???????) (F7G0005+)' % (rel_bios_ver_f7a, rel_bios_ver_f7g)),
    (0x17d050, 'F7A0101 and lower (F7A0101-)')]
# detected BIOS offset
#bios_offset = None
# list
#bios_offset = bios_offset_list[0]
# tuple list (list of tuples)
bios_offset = bios_offset_list[0][0]
# detected BIOS offset - overrides bios_offset
#bios_offset_str = b'UUITE Tech. Inc.  '
#bios_offset_str = b'UUITE Tech. Inc.'
#bios_offset_str_offset = -0x4e
bios_offset_str = b'$_IFLASH_BIOSIMG'
bios_offset_str_offset = 0x18
bios_size = 0x1000000
# detected UID/offset/size
bios_uid = None
#bios_uid_offset = 0x6a4000
bios_uid_offset = None
# detected UID offset - overrides bios_uid/bios_uid_offset/bios_uid_size
#bios_uid_offset_str = b'\x24\x44\x4d\x49'
bios_uid_offset_str = b'$DMI'
#bios_uid_size_f7g = 0x10c
#bios_uid_size_f7a = 0x174
bios_uid_size = None

# download/network
url = 'https://gitlab.com/evlaV'
repo = 'jupiter-PKGBUILD'
rel_bios_dl_pkg = ['zip', 'tar.gz', 'tar.bz2', 'tar']
#rel_bios_dl_pkg_nozip = rel_bios_dl_pkg[1:]
#rel_bios_dl_pkg_nozip = [s for s in rel_bios_dl_pkg if s != 'zip']
rel_bios_dl_pkg_nozip = ['tar.gz', 'tar.bz2', 'tar']
src_form = ['blob', 'raw']

# generate UID
gen_uid_list = ['F7G0105', 'F7A0119']
# set to override pseudorandom generation (one/single CAPITAL/UPPERCASE alpha/letter) - MEY[X]ZZZZZZZZ
meYX_alpha = None
# set to override pseudorandom generation (8 digit integer/number) - MEYX[ZZZZZZZZ]
meYX_int = None
# set to override pseudorandom generation (8 byte alphanumeric) - MEYX[ZZZZZZZZ]
meYX_alnum = None
# serial number - set to override pseudorandom generation (one/single CAPITAL/UPPERCASE alpha/letter) - F[X]YYZZZZZZZZ
fXYY_alpha = None
# serial number - set to override pseudorandom generation (8 digit integer/number) - FXYY[ZZZZZZZZ]
fXYY_int = None
# serial alphanumeric - set to override pseudorandom generation (8 byte alphanumeric) - FXYY[ZZZZZZZZ]
fXYY_alnum = None
uid_1_f7g = '0x00000000-0x00000000'
#uid_1_null_f7g = b'\xff' * 21
uid_1_null_f7g = b'\xff' * len(uid_1_f7g)
uid_1_f7a = '0x00,0x00,0x00,0x00-0x00,0x00,0x00,0x00-0x00,0x00,0x00,0x00'
#uid_1_null_f7a = b'\xff' * 59
uid_1_null_f7a = b'\xff' * len(uid_1_f7a)
uid_2_f7a = '0x00,0x00,0x00,0x00-0x00,0x00,0x00,0x00-0x00,0x00,0x00,0x00'
#uid_2_null_f7a = b'\xff' * 59
uid_2_null_f7a = b'\xff' * len(uid_2_f7a)
backup_uid_default_file = 'jupiter-UID-backup.bin'
generate_uid_default_file = 'jupiter-UID-generated.bin'

# info/misc (fallback/preliminary/unused)
# RELEASE BIOS UID offset tuple list - [byte_size_int, str]
rel_bios_uid_offset_list = [
    (0x78cc70, 'F7A0102-%s(-???????) (F7A0102+) or F7G0005-%s(-???????) (F7G0005+)' % (rel_bios_ver_f7a, rel_bios_ver_f7g)),
    (0x821050, 'F7A0101 and lower (F7A0101-)')]
# block/string is duplicated/repeated at +0x800000 - [offset_int, offset_int + 0x800000]
rel_bios_ver_offset_list = [0x790c7e, 0xf90c7e]
bios_ver_offset_list = [0x6a800e, 0xea800e]
# block/string is duplicated/repeated at +0x40000 - [offset_int, offset_int + 0x40000]
rel_ec_rev_offset_list = [0xf0c76, 0x130c76]
ec_rev_offset_list = [0x8006, 0x48006]
rel_ec_date_offset_list = [0xf0c84, 0x130c84]
ec_date_offset_list = [0x8014, 0x48014]
# block/string is duplicated/repeated at +0x800000 - [offset_int, offset_int + 0x800000]
rel_bios_date_offset_list = [0x790dd1, 0xf90dd1]
bios_date_offset_list = [0x6a8161, 0xea8161]
invalid = None
name_list = ['aerith', 'chachani', 'galileo', 'jupiter', 'sephiroth', 'steamdeck', 'vangogh']
rcl = ['━', '┅', '┉', '╍', '═', '╳', '`', '~', '@', '#', '$', '%', '^', '&', '*', '-', '=', '+', '\\', '|', ';', ':', "'", '"', ',', '<', '.', '>', '/', '?', 'w', 'W', '0', 'o', 'O', 's', 'S', 'z', 'Z', 'x', 'X', 'v', 'V', 'n', 'N', 'm', 'M']
rc = random.choice(rcl)

# title
print("""
 ┏%s┓
 ┃ Steam Deck (jupiter) BIOS Tool v%s ┃
 ┣%s (jupiter-bios-tool) %s┫
 ┃Copyright (C) %s %s┃
 ┗%s┛
""" % (rc * 37, ver, '━' * 8, '━' * 8, cyr, base64.b64decode('RHJha2UgU3RlZmFuaQ==').decode('utf-8'), rc * 37))
if '-h' in sys.argv or '--help' in sys.argv:
    print("═" * 22)
    print("""\
Automatically analyze, verify, backup/generate/inject UID, and dynamically trim
any/all Steam Deck (jupiter) BACKUP and RELEASE BIOS (*_sign.fd) (>0x1000000)
images to 0x1000000 for hardware flashing/programming to a Winbond W25Q128JW
128Mb (16MB) Serial NOR Flash.""")
    print("═" * 22)
    print()
    print("━" * 22)
    print("Source Code:")
    for s in src_form:
        print("  %s/%s/-/%s/master/jupiter-bios-tool.py" % (url, repo, s))
    print("━" * 22)
    print("""\
Documentation:
  %s/%s#-steam-deck-jupiter-bios-backup-
  %s/%s#-steam-deck-jupiter-bios-tool-jupiter-bios-tool-""" % (url, repo, url, repo))
    print("━" * 22)
    print("""\
RELEASE BIOS Database:
  %s/%s#valve-official-steam-deck-jupiter-release-bios-database
  %s/%s#steam-deck-oled-galileo-f7g-release-bios
  %s/%s#steam-deck-lcd-f7a-release-bios
  %s/%s#steam-deck-lcd-f7a-deckhd-bios""" % (url, repo, url, repo, url, repo, url, repo))
    print("━" * 22)
    print("""\
RELEASE BIOS Download:
  %s/jupiter-hw-support/-/tree/master/usr/share/jupiter_bios
  %s/jupiter-hw-support/-/archive/master/jupiter-hw-support-master.%s?path=usr/share/jupiter_bios""" % (url, url, random.choice(rel_bios_dl_pkg)))
    print("─" * 22)
    print("""\
Download current/latest RELEASE BIOS to %s/jupiter_bios/ - requires curl and bsdtar (libarchive):
$ curl %s/jupiter-hw-support/-/archive/master/jupiter-hw-support-master.%s?path=usr/share/jupiter_bios | bsdtar --strip-components=3 -xvf-""" % (os.getcwd(), url, random.choice(rel_bios_dl_pkg)))
    print("━" * 22)
    print("""\
BIOS Backup:
If running official (jupiter) SteamOS - requires jupiter-hw-support:
$ sudo /usr/share/jupiter_bios_updater/h2offt jupiter-%s-bios-backup.bin -O""" % rel_bios_ver_f7g)
    print("─" * 22)
    print("""\
Universal - requires curl and bsdtar (libarchive):
$ curl %s/jupiter-hw-support/-/archive/master/jupiter-hw-support-master.%s?path=usr/share/jupiter_bios_updater | bsdtar --strip-components=3 -xvf-
$ sudo jupiter_bios_updater/h2offt jupiter-%s-bios-backup.bin -O""" % (url, random.choice(rel_bios_dl_pkg_nozip), rel_bios_ver_f7g))
    print("━" * 22)
    #print("\n%s\n" % ('═' * 22))
    print()
else:
    print("""\
-h, --help to show description, source code, documentation, BIOS database,
BIOS download, BIOS backup, and help (usage, examples, positional arguments,
and options).
""")

parser = argparse.ArgumentParser(usage='''\
%(prog)s [SOURCE_BIOS_IMAGE[.bin|.fd|.rom]]
       [DESTINATION_BIOS_IMAGE[.bin|.rom]] [-h] [-b] [-g] [-i] [-r] [-v]

 e.g.: %(prog)s jupiter-''' + rel_bios_ver_f7g + '''-bios-backup.bin -b
       %(prog)s ''' + rel_bios_ver_f7g + '_sign.fd jupiter-' + rel_bios_ver_f7g + '-bios-injected.bin -i')
parser.add_argument('src', metavar='SOURCE_BIOS_IMAGE[.bin|.fd|.rom]', nargs='?',
                    help='analyze/verify SOURCE BIOS image (e.g., %s)' % (rel_bios_ver_f7g + '_sign.fd'))
parser.add_argument('dest', metavar='DESTINATION_BIOS_IMAGE[.bin|.rom]', nargs='?',
                    help='dynamically trim SOURCE BIOS image and/or inject UID to DESTINATION (SOURCE -> DESTINATION)')
parser.add_argument('-b', '--backup-uid', dest='backup_uid', const=backup_uid_default_file, metavar='BACKUP_UID_TO_FILE', nargs='?',
                    help='backup SOURCE UID to SPECIFIED file (default: %s)' % backup_uid_default_file)
parser.add_argument('-g', '--generate-uid', dest='generate_uid', const=generate_uid_default_file, metavar='GENERATE_UID_TO_FILE', nargs='?',
                    help='generate (pseudorandom) F7G/F7A UID to SPECIFIED file (default: %s) and inject to DESTINATION (if SPECIFIED)' % generate_uid_default_file)
parser.add_argument('--ev2', '--EV2', dest='generate_serial_ev2', action='store_true',
                    help='generate (pseudorandom) EV2 serial integer/number/alphanumeric (e.g., FXYY[132]ZZZZZ)')
parser.add_argument('--ev3', '--EV3', dest='generate_serial_ev3', action='store_true',
                    help='generate (pseudorandom) EV3 serial integer/number/alphanumeric (e.g., FXYY[133]ZZZZZ)')
parser.add_argument('--f7a', '--F7A', dest='generate_uid_f7a', action='store_true',
                    help='generate (pseudorandom) F7A UID instead of %s UID (default: %s)' % (gen_uid_list[0][:3], gen_uid_list[0][:3]))
parser.add_argument('--int', '--num', dest='generate_uid_int', action='store_true',
                    help='generate (pseudorandom) integer/number UID instead of alphanumeric UID (e.g., FXYYA1B2C3D4 -> FXYY12345678) (default: alphanumeric)')
parser.add_argument('-i', '--inject-uid', dest='inject_uid', const=backup_uid_default_file, metavar='INJECT_UID_FROM_FILE', nargs='?',
                    help='inject UID from SPECIFIED file (default: %s) to DESTINATION' % backup_uid_default_file)
parser.add_argument('-r', '--remove-uid', dest='remove_uid', action='store_true',
                    help='remove ("scrub") UID from SOURCE to DESTINATION (commonize/sanitize)')
parser.add_argument('-v', '--version', dest='version', action='store_true',
                    help='show version information and exit')
args = parser.parse_args()

if args.version:
    sys.exit(0)

# enable UID generation if argument --f7a and/or --int and/or --ev2 and/or --ev3 specified (and not -g)
if args.generate_uid_f7a or args.generate_uid_int or args.generate_serial_ev2 or args.generate_serial_ev3:
    if not args.generate_uid:
        args.generate_uid = generate_uid_default_file

# generate UID file - F7G(0105) / F7A(0115/0116/0118/0119)
if args.generate_uid:
    if args.generate_uid_f7a:
        gen_uid_rev = 'F7A'
    else:
        gen_uid_rev = 'F7G'
    # nondestructive/conforming (refuse to overwrite)
    #if os.path.isfile(args.generate_uid):
    # destructive/nonconforming (overwrite generate_uid_default_file)
    if os.path.isfile(args.generate_uid) and args.generate_uid != generate_uid_default_file:
        print("error: generated UID file (%s) preexists! refuse to overwrite (nondestructive).\n" % args.generate_uid)
        sys.exit(1)
    with open(args.generate_uid, 'wb') as gen_uid_of:
        gen_uid_of.write(b'$DMI')
        gen_uid_of.write(b'\x02\x07\x00\x11\x00')
        #if not meYX_alpha or not isinstance(meYX_alpha, str) or not meYX_alpha.isalpha() or not len(meYX_alpha) == 1 or not meYX_alpha[0].isupper():
        if not meYX_alpha or not isinstance(meYX_alpha, str) or not meYX_alpha.isalpha():
            #meYX_alpha = str(chr(random.randint(ord('A'), ord('Z'))))
            meYX_alpha = str(chr(random.randint(65, 90)))
        if args.generate_uid_f7a:
            gen_uid_of.write(b'MEB' + bytes(meYX_alpha[0].upper(), 'utf-8'))
        else:
            gen_uid_of.write(b'MEC' + bytes(meYX_alpha[0].upper(), 'utf-8'))
        if not meYX_int or not isinstance(meYX_int, int):
            meYX_int = random.randint(0, 99999999)
        #meYX_int = '{:08d}'.format(meYX_int)
        meYX_int = str(meYX_int).zfill(8)
        if not meYX_alnum or not meYX_alnum.isalnum():
            meYX_alnum = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
        meYX_alnum = str(meYX_alnum).zfill(8)
        if args.generate_uid_int:
            gen_uid_of.write(bytes(meYX_int, 'utf-8'))
        else:
            gen_uid_of.write(bytes(meYX_alnum.upper(), 'utf-8'))
        gen_uid_of.write(b'\x02\x07\xff\x11\x00')
        if args.generate_uid_f7a:
            gen_uid_of.write(b'MEB' + bytes(meYX_alpha[0].upper(), 'utf-8'))
        else:
            gen_uid_of.write(b'MEC' + bytes(meYX_alpha[0].upper(), 'utf-8'))
        if args.generate_uid_int:
            gen_uid_of.write(bytes(meYX_int, 'utf-8'))
        else:
            gen_uid_of.write(bytes(meYX_alnum.upper(), 'utf-8'))
        gen_uid_of.write(b'\x01\x07\x00\x11\x00')
        #if not fXYY_alpha or not isinstance(fXYY_alpha, str) or not fXYY_alpha.isalpha() or not len(fXYY_alpha) == 1 or not fXYY_alpha[0].isupper():
        if not fXYY_alpha or not isinstance(fXYY_alpha, str) or not fXYY_alpha.isalpha():
            #fXYY_alpha = str(chr(random.randint(ord('A'), ord('Z'))))
            fXYY_alpha = str(chr(random.randint(65, 90)))
        if args.generate_uid_f7a:
            gen_uid_of.write(b'F' + bytes(fXYY_alpha[0].upper(), 'utf-8') + b'AA')
        else:
            gen_uid_of.write(b'F' + bytes(fXYY_alpha[0].upper(), 'utf-8') + b'ZZ')
        if not fXYY_int or not isinstance(fXYY_int, int):
            if args.generate_serial_ev3:
                fXYY_int = int(str(133) + str(random.randint(0, 99999)))
            elif args.generate_serial_ev2:
                fXYY_int = int(str(132) + str(random.randint(0, 99999)))
            else:
                fXYY_int = random.randint(0, 99999999)
        #fXYY_int = '{:08d}'.format(fXYY_int)
        fXYY_int = str(fXYY_int).zfill(8)
        if not fXYY_alnum or not fXYY_alnum.isalnum():
            if args.generate_serial_ev3:
                fXYY_alnum = '133' + ''.join(random.choice(string.ascii_letters + string.digits) for i in range(5))
            elif args.generate_serial_ev2:
                fXYY_alnum = '132' + ''.join(random.choice(string.ascii_letters + string.digits) for i in range(5))
            else:
                fXYY_alnum = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
        fXYY_alnum = str(fXYY_alnum).zfill(8)
        if args.generate_uid_int:
            gen_uid_of.write(bytes(fXYY_int, 'utf-8'))
        else:
            gen_uid_of.write(bytes(fXYY_alnum.upper(), 'utf-8'))
        gen_uid_of.write(b'\x01\x07\xff\x11\x00')
        if args.generate_uid_f7a:
            gen_uid_of.write(b'F' + bytes(fXYY_alpha[0].upper(), 'utf-8') + b'AA')
        else:
            gen_uid_of.write(b'F' + bytes(fXYY_alpha[0].upper(), 'utf-8') + b'ZZ')
        if args.generate_uid_int:
            gen_uid_of.write(bytes(fXYY_int, 'utf-8'))
        else:
            gen_uid_of.write(bytes(fXYY_alnum.upper(), 'utf-8'))
        if args.generate_uid_f7a:
            gen_uid_of.write(b'\x0b\x06\x00\x16\x00')
            #gen_uid_of.write(b'5.0')
            #gen_uid_of.write(b'5.555555555555555')
            gen_uid_of.write(b'5.' + b'5' * 15)
            gen_uid_of.write(b'\x0b\x06\xff\x16\x00')
            #gen_uid_of.write(b'5.0')
            #gen_uid_of.write(b'5.555555555555555')
            gen_uid_of.write(b'5.' + b'5' * 15)
            gen_uid_of.write(b'\x0b\x05\x00\x40\x00')
            gen_uid_of.write(bytes(uid_1_f7a, 'utf-8'))
            gen_uid_of.write(b'\x0b\x05\xff\x40\x00')
            gen_uid_of.write(bytes(uid_1_f7a, 'utf-8'))
            gen_uid_of.write(b'\x0b\x07\x00\x40\x00')
            gen_uid_of.write(bytes(uid_2_f7a, 'utf-8'))
            gen_uid_of.write(b'\x0b\x07\xff\x40\x00')
            gen_uid_of.write(bytes(uid_2_f7a, 'utf-8'))
        else:
            gen_uid_of.write(b'\x0b\x08\x00\x17\x00')
            #gen_uid_of.write(b'14.555555555555555')
            gen_uid_of.write(b'14.' + b'5' * 15)
            gen_uid_of.write(b'\x0b\x08\xff\x17\x00')
            #gen_uid_of.write(b'14.555555555555555')
            gen_uid_of.write(b'14.' + b'5' * 15)
            gen_uid_of.write(b'\x0b\x06\x00\x17\x00')
            #gen_uid_of.write(b'12.555555555555555')
            gen_uid_of.write(b'12.' + b'5' * 15)
            gen_uid_of.write(b'\x0b\x06\xff\x17\x00')
            #gen_uid_of.write(b'12.555555555555555')
            gen_uid_of.write(b'12.' + b'5' * 15)
            gen_uid_of.write(b'\x0b\x05\x00\x1a\x00')
            gen_uid_of.write(bytes(uid_1_f7g, 'utf-8'))
            gen_uid_of.write(b'\x0b\x05\xff\x1a\x00')
            gen_uid_of.write(bytes(uid_1_f7g, 'utf-8'))
            gen_uid_of.write(b'\x0b\x07\x00\x1a\x00')
            gen_uid_of.write(bytes(uid_1_f7g, 'utf-8'))
            gen_uid_of.write(b'\x0b\x07\xff\x1a\x00')
            gen_uid_of.write(bytes(uid_1_f7g, 'utf-8'))
        print("successfully generated %s UID file (%s). byte size (%s).\n" % (gen_uid_rev, args.generate_uid, gen_uid_of.tell()))
        # inject with -i, --inject-uid
        #if args.inject_uid == backup_uid_default_file:
        # inject with/without -i, --inject-uid
        if args.inject_uid == backup_uid_default_file or not args.inject_uid:
            args.inject_uid = args.generate_uid
        if not args.src:
            sys.exit(0)

# read UID file
if args.inject_uid:
    if os.path.isfile(args.inject_uid):
        with open(args.inject_uid, 'rb') as uid_if:
            bios_uid_inject = uid_if.read()
    else:
        print("error: UID file (%s) does not exist!\n" % args.inject_uid)
        sys.exit(2)

# SOURCE BIOS image check
if not args.src:
    print("error: SOURCE BIOS image not SPECIFIED!\n")
    sys.exit(3)
if not os.path.isfile(args.src):
    print("error: SOURCE BIOS image (%s) does not exist!\n" % args.src)
    sys.exit(4)
if os.path.getsize(args.src) < bios_size:
    print("""\
%s: error: less than BIOS byte size! | %s < %s | %s fewer bytes!
%s: error: CORRUPT or INVALID BIOS detected!""" % (args.src, os.path.getsize(args.src), bios_size, os.path.getsize(args.src) - bios_size, args.src))
    #if args.dest:
    if args.dest and not args.backup_uid and not args.generate_uid and not args.inject_uid:
        print("\nabort!\n")
        sys.exit(5)
# moved / more effective below
#if os.path.getsize(args.src) == bios_size:
    ##if args.dest:
    #if args.dest and not args.backup_uid and not args.generate_uid and not args.inject_uid and not args.remove_uid:
        #print("%s: error: TRIMMED or BACKUP BIOS image! nothing to trim.\n" % args.src)
        #print("abort!\n")
        #sys.exit(6)
    #print("%s: TRIMMED or BACKUP BIOS image.\n" % args.src)
    ##sys.exit(6)
# detect RELEASE BIOS byte size
for drb_size, drb_str in rel_bios_size_list:
    if os.path.getsize(args.src) == drb_size:
        #print("%s: valid UNTRIMMED RELEASE BIOS byte size (%s) detected." % (args.src, drb_size))
        print("%s: valid UNTRIMMED RELEASE BIOS image %s byte size (%s) detected." % (args.src, drb_str, drb_size))
        break

# read SOURCE BIOS image binary
with open(args.src, 'rb') as sf:
    sf_data = sf.read()
    # redundant?
    sf.seek(0)
    # detect BIOS image version
    for bios_ver_offset_str in bios_ver_offset_str_f7g, bios_ver_offset_str_f7a:
        if sf_data.find(bios_ver_offset_str) >= 0:
        #if sf_data.rfind(bios_ver_offset_str) >= 0:
            bios_ver_offset = sf_data.find(bios_ver_offset_str) + bios_ver_offset_str_offset
            #bios_ver_offset = sf_data.rfind(bios_ver_offset_str) + bios_ver_offset_str_offset
            sf.seek(bios_ver_offset)
            bios_ver = str(sf.read(bios_ver_size), 'utf-8')
            tbios_ver = str(sf.read(tbios_ver_size), 'utf-8')
            if tbios_ver.isalnum():
                bios_ver += tbios_ver
            sf.seek(0)
            print("%s: BIOS version (%s) detected at offset (%s)." % (args.src, bios_ver, hex(bios_ver_offset)))
            break
    # detect BIOS image revision/date
    for ec_rev_offset_str, ec_rev_offset_str_offset, ec_rev_size, ec_date_offset_str_offset, ec_date_size in ec_offset_list:
        if sf_data.find(ec_rev_offset_str) >= 0:
        #if sf_data.rfind(ec_rev_offset_str) >= 0:
            ec_rev_offset = sf_data.find(ec_rev_offset_str) + ec_rev_offset_str_offset
            sf.seek(ec_rev_offset)
            ec_rev = str(sf.read(ec_rev_size), 'utf-8')
            sf.seek(0)
            #if not ec_rev[1:].isdigit():
            if not ec_rev.isalnum():
                ec_rev = None
                continue
            print("%s: EC revision (%s) detected at offset (%s)." % (args.src, ec_rev, hex(ec_rev_offset)))
            ec_date_offset = sf_data.find(ec_rev_offset_str) + ec_date_offset_str_offset
            sf.seek(ec_date_offset)
            ec_date = str(sf.read(ec_date_size), 'utf-8')
            sf.seek(0)
            if not ec_date[:4].isdigit() or not ec_date[5:7].isdigit() or not ec_date[8:10].isdigit():
                ec_date = None
                continue
            print("%s: EC date (%s) detected at offset (%s)." % (args.src, ec_date, hex(ec_date_offset)))
            break
    if sf_data.find(bios_date_offset_str) >= 0:
    #if sf_data.rfind(bios_date_offset_str) >= 0:
        bios_date_offset = sf_data.find(bios_date_offset_str) + bios_date_offset_str_offset
        sf.seek(bios_date_offset)
        bios_date_bin = sf.read(bios_date_size)
        # 20YY/MM/DD
        bios_date = '20' + format(int(hex(bios_date_bin[0])[2:]), '02') + '/' + format(int(hex(bios_date_bin[1])[2:]), '02') + '/' + format(int(hex(bios_date_bin[2])[2:]), '02')
        sf.seek(0)
        print("%s: BIOS date (%s) detected at offset (%s)." % (args.src, bios_date, hex(bios_date_offset)))
    sf_header = sf.read(len(rel_header))
    sf.seek(0)
    # sort by size (large -> small) - F7A must be before F7G
    # 1) F7A (5) 2) F7G (1)
    for bios_header in bios_header_f7a, bios_header_f7g:
        sf_bios_header = sf.read(len(bios_header))
        sf.seek(0)
        # header checks
        if sf_header == rel_header:
            print("%s: valid UNTRIMMED RELEASE BIOS detected." % args.src)
            break
        if sf_bios_header == bios_header:
            bios_offset = 0x0
            #if args.dest:
            if args.dest and not args.backup_uid and not args.generate_uid and not args.inject_uid:
                print("\n%s: warning: valid TRIMMED or BACKUP BIOS detected." % args.src)
            else:
                print("%s: valid TRIMMED or BACKUP BIOS detected." % args.src)
            if os.path.getsize(args.src) == bios_size:
                #if args.dest:
                if args.dest and not args.backup_uid and not args.generate_uid and not args.inject_uid and not args.remove_uid:
                    print("%s: error: TRIMMED or BACKUP BIOS image! nothing to trim.\n" % args.src)
                    print("abort!\n")
                    sys.exit(6)
                if bios_ver:
                    print("%s: TRIMMED or BACKUP BIOS image version %s." % (args.src, bios_ver))
                else:
                    print("%s: TRIMMED or BACKUP BIOS image." % args.src)
                #sys.exit(6)
            break
        #else:
            #continue
    if sf_header != rel_header and sf_bios_header != bios_header:
        #print("%s: warning: INVALID or UNKNOWN BIOS detected! | %s != %s" % (args.src, sf_header, rel_header))
        #print("%s: warning: INVALID or UNKNOWN BIOS detected! | %s != %s" % (args.src, sf_bios_header, bios_header))
        print("%s: warning: INVALID or UNKNOWN BIOS detected!" % args.src)
    # detect BIOS offset
    if sf_bios_header != bios_header:
        if sf_data.find(bios_offset_str) >= 0:
            #bios_offset = sf_data.find(bios_offset_str)
            bios_offset = sf_data.find(bios_offset_str) + bios_offset_str_offset
            if bios_offset < 0:
                print("%s: error: CORRUPT or INVALID BIOS detected! | %s fewer bytes!\n" % (args.src, abs(bios_offset)))
                print("abort!\n")
                sys.exit(7)
            print("%s: BIOS offset (%s) detected." % (args.src, hex(bios_offset)))
            # detect BIOS image version
            for drb_offset, drb_str in bios_offset_list:
                if bios_offset == drb_offset:
                    detect_rel_bios_ver = drb_str
                    break
                detect_rel_bios_ver = None
        else:
            print("%s: error: BIOS offset not detected!" % args.src)
            invalid = True
            # fallback to (preset) bios_offset_list
            for drb_offset, drb_str in bios_offset_list:
                if isinstance(drb_offset, int) and isinstance(drb_str, str):
                    print("using (fallback/preset) %s BIOS offset (%s)" % (drb_str, hex(drb_offset)))
                    for bios_header in bios_header_f7a, bios_header_f7g:
                        sf.seek(drb_offset)
                        if sf.read(len(bios_header)) == bios_header:
                            bios_offset = drb_offset
                            invalid = None
                            break
                    if invalid:
                        print("error: %s BIOS offset (%s) INVALID!" % (drb_str, hex(drb_offset)))
                    else:
                        break
        if invalid:
            print("""\
%s: error: INVALID or UNKNOWN BIOS offset detected!

continuing (despite header mismatch!) ...
""" % args.src)
        else:
            print("%s: valid BIOS offset detected." % args.src)
    # detect UID offset
    if sf_data.find(bios_uid_offset_str) >= 0:
    #if sf_data.rfind(bios_uid_offset_str) >= 0:
        bios_uid_offset = sf_data.find(bios_uid_offset_str)
        #bios_uid_offset = sf_data.rfind(bios_uid_offset_str)
        sf.seek(bios_uid_offset)
        sf_uid_data = sf.read()
        bios_uid_size = sf_uid_data.find(b'\xff' * 4)
        sf.seek(bios_uid_offset)
        bios_uid = sf.read(bios_uid_size)
        sf.seek(0)
        if not bios_uid or bios_uid == bios_uid_offset_str:
            if os.path.getsize(args.src) == bios_size:
                #print("%s: warning: NO/NULL UID offset (%s) detected! DO NOT FLASH!" % (args.src, hex(bios_uid_offset)))
                print("%s: warning: NO/NULL UID offset (%s) detected! DO NOT FLASH! INJECT UID (-i)" % (args.src, hex(bios_uid_offset)))
            # maybe use rel_bios_size_list
            elif os.path.getsize(args.src) > bios_size:
                print("%s: NO/NULL UID offset (%s) detected. TRIM AND INJECT UID (-i) OR FLASH WITH H2OFFT!" % (args.src, hex(bios_uid_offset)))
        else:
            print("%s: UID offset (%s) detected. byte size (%s)." % (args.src, hex(bios_uid_offset), bios_uid_size))
            if args.backup_uid:
                if os.path.isfile(args.backup_uid):
                    print("error: UID file (%s) preexists! refuse to overwrite (nondestructive).\n" % args.backup_uid)
                    print("abort!\n")
                    sys.exit(8)
                with open(args.backup_uid, 'wb') as uid_df:
                    uid_df.write(bios_uid)
                #print("%s: successfully backed up UID file (%s).\n%s: successfully made UID file." % (args.src, args.backup_uid, args.backup_uid))
                print("%s: successfully backed up UID file (%s)." % (args.src, args.backup_uid))
    #sf.seek(bios_offset)
    # inject UID file
    if args.inject_uid and os.path.isfile(args.src) and bios_uid_offset >= 0 and bios_uid_offset >= bios_offset:
        sf.seek(bios_offset)
        # potentially inflate/pad bios_uid_inject
        if bios_uid_size > len(bios_uid_inject):
            print("%s: inflating/padding UID byte size: %s -> %s | padding byte size (%s)." % (args.src, len(bios_uid_inject), bios_uid_size, bios_uid_size - len(bios_uid_inject)))
            # must be AFTER print()
            bios_uid_inject += b'\xff' * (bios_uid_size - len(bios_uid_inject))
        #bios = sf.read(bios_uid_offset - bios_offset)
        #bios += bios_uid_inject
        bios = sf.read(bios_uid_offset - bios_offset) + bios_uid_inject
        # relative seek(,1)
        sf.seek(len(bios_uid_inject), 1)
        if bios_size >= len(bios):
            #bios += sf.read(bios_size - (bios_uid_offset - bios_offset) - len(bios_uid_inject))
            bios += sf.read(bios_size - len(bios))
        else:
            print("""\
error: injected BIOS greater than BIOS byte size! | %s > %s | %s extra bytes!
error: CORRUPT or INVALID injected BIOS detected!
""" % (len(bios), bios_size, len(bios) - bios_size))
            sys.exit(9)
        print("%s: injected UID file (%s) at offset (%s) | byte size (%s)." % (args.src, args.inject_uid, hex(bios_uid_offset), len(bios_uid_inject)))
    # remove UID (inject blank UID)
    elif args.remove_uid:
        sf.seek(bios_offset)
        bios = sf.read(bios_uid_offset - bios_offset) + b'\xff' * bios_uid_size
        # relative seek(,1)
        sf.seek(bios_uid_size, 1)
        #bios += sf.read(bios_size - (bios_uid_offset - bios_offset) - len(bios_uid_inject))
        bios += sf.read(bios_size - len(bios))
    # RAW BIOS
    else:
        sf.seek(bios_offset)
        bios = sf.read(bios_size)

# BIOS byte size check
if len(bios) == bios_size:
    print("%s: valid BIOS byte size (%s) detected." % (args.src, len(bios)))
else:
    print("""\
%s: error: BIOS byte size mismatch! | %s != %s | %s byte size difference!
%s: error: CORRUPT or INVALID BIOS detected!
""" % (args.src, len(bios), bios_size, len(bios) - bios_size, args.src))
    print("abort!\n")
    sys.exit(10)

if not invalid:
    if detect_rel_bios_ver:
        if bios_ver:
            print("%s: UNTRIMMED RELEASE BIOS image version %s | %s.\n" % (args.src, bios_ver, detect_rel_bios_ver))
        else:
            print("%s: UNTRIMMED RELEASE BIOS image version %s.\n" % (args.src, detect_rel_bios_ver))
    elif bios_ver:
        print("%s: BIOS image version %s.\n" % (args.src, bios_ver))
    else:
        if os.path.getsize(args.src) > bios_size:
            print("%s: warning: INVALID or UNKNOWN (UNTRIMMED RELEASE?) BIOS image!\n" % args.src)
        elif os.path.getsize(args.src) == bios_size:
            print("%s: warning: INVALID or UNKNOWN (TRIMMED or BACKUP?) BIOS image!\n" % args.src)
        else:
            print("%s: warning: INVALID or UNKNOWN BIOS image!\n" % args.src)

# exit if no DESTINATION BIOS image SPECIFIED
if not args.dest:
    sys.exit(0)

# DESTINATION BIOS image check
if os.path.isfile(args.dest):
    print("error: DESTINATION BIOS image (%s) preexists! refuse to overwrite (nondestructive).\n" % args.dest)
    print("abort!\n")
    sys.exit(11)

# write DESTINATION BIOS image binary
with open(args.dest, 'wb') as df:
    df.write(bios)

if invalid:
    print("""\
⚠️ MANUALLY CHECK/VERIFY TRIMMED BIOS INTEGRITY! ⚠️

%s: warning: potentially CORRUPT or INVALID or UNKNOWN BIOS detected!

%s: warning: potentially TRIMMED BIOS: %s -> %s
""" % (args.dest, args.dest, args.src, args.dest))
    sys.exit(12)

if os.path.getsize(args.src) > bios_size:
    print("%s: successfully TRIMMED BIOS: %s -> %s\n" % (args.dest, args.src, args.dest))
elif os.path.getsize(args.src) == bios_size:
    print("%s: successfully made BIOS: %s -> %s\n" % (args.dest, args.src, args.dest))
sys.exit(0)
