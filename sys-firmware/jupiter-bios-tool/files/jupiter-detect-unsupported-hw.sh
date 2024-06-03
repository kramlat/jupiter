#!/bin/bash
echo
usage() {
  echo "usage: [sudo] $0 [serial_number] [-h] [--help]"
  echo " e.g.: [sudo] $0 FXYY133ZZZZZ"
}
for arg; do
case ${arg,,} in
-h|--help)
  usage
  exit 0
  ;;
*)
  if [[ ${#arg} -ge 7 && ${arg:4:3} =~ ^[0-9]+$ ]]; then
    product_serial=$arg
  else
    echo "error: provided argument ($arg) invalid!"
    echo
  fi
  ;;
esac
done
detect_serial=
serial_path=/sys/devices/virtual/dmi/id/product_serial
if [[ ! ${#product_serial} -ge 7 && ! ${product_serial:4:3} =~ ^[0-9]+$ && -r $serial_path ]]; then
  if hash cat 2>/dev/null; then
    product_serial=$(cat "$serial_path" 2>/dev/null)
    detect_serial=1
  else
    echo "error: cat (coreutils) not found!"
    echo "install cat (coreutils) to detect product_serial ($serial_path)"
    echo
    exit 1
  fi
fi
# uppercase
product_serial=${product_serial^^}
[[ -n $detect_serial ]] && dp=detected || dp=provided
if [[ -z $product_serial ]]; then
  echo "error: product_serial not provided or found/readable! ($serial_path)"
  echo
  usage
  exit 2
elif [[ ! ${#product_serial} -ge 7 && ! ${product_serial:4:3} =~ ^[0-9]+$ ]]; then
  echo "error: $dp product_serial ($product_serial) invalid!"
  echo
  usage
  exit 3
fi
product_year=${product_serial:4:1}
product_week=${product_serial:5:2}
#echo -e " Steam Deck (jupiter) $dp serial: \e[1m$product_serial\e[0m"
echo -e " Steam Deck (jupiter) $dp serial: \e[1m${product_serial:0:4}\e[91m${product_serial:4:1}\e[92m${product_serial:5:2}\e[39m${product_serial:7}\e[0m"
echo -e "Steam Deck (jupiter) manufacture date: \e[1;91myear: 202$product_year\e[0m | \e[1;92mweek: $product_week\e[0m"
echo
if [[ $product_year == 1 && $product_week -lt 33 ]]; then
  echo -e "\e[1;31munsupported hardware revision! (<=EV2 | EV2-)\e[0m 👎"
else
  echo -e "\e[1;32msupported hardware revision (>EV2 | EV3+)\e[0m 👍"
fi
