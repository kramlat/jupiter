/*
 * https://gist.github.com/SmokelessCPUv2/8c1e6559031e199d9a678c9fe2ebf7d4
 * compile: g++ -O1 jupiter-bios-unlock.cc -o jupiter-bios-unlock
 *   usage: [sudo] ./jupiter-bios-unlock [-l] [--lock]
*/

#include <cstring>
#include <sys/io.h>
#include <iostream>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (geteuid() != 0) {
        std::cout << "error: root required to 🔓 unlock/lock 🔒 Steam Deck (jupiter) BIOS (AMD CBS/PBS)." << std::endl;
        std::cout << " info: run (as root) on Steam Deck (jupiter) hardware to 🔓 unlock/lock 🔒 BIOS (AMD CBS/PBS)." << std::endl;
        std::cout << "usage: [sudo] " << argv[0] << " [-l] [--lock]" << std::endl;
        return 1;
    }

    ioperm(0x72, 2, 1);
    outb(0xF7, 0x72);
    for (int i = 1; i < argc; i++) {
        if (std::strcmp(argv[i], "-l") == 0 || std::strcmp(argv[i], "--lock") == 0) {
            outb(0x00, 0x73);
            std::cout << "Steam Deck (jupiter) BIOS successfully 🔒 locked 🔒 (AMD CBS/PBS)." << std::endl;
            return 0;
        }
    }
    outb(0x77, 0x73);
    std::cout << "Steam Deck (jupiter) BIOS successfully 🔓 unlocked 🔓 (AMD CBS/PBS)." << std::endl;
    return 0;
}
