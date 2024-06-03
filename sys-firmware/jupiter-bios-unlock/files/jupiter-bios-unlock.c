/*
 * https://gist.github.com/SmokelessCPUv2/8c1e6559031e199d9a678c9fe2ebf7d4
 * compile: gcc -O1 jupiter-bios-unlock.c -o jupiter-bios-unlock
 *   usage: [sudo] ./jupiter-bios-unlock [-l] [--lock]
*/

#include <sys/io.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (geteuid() != 0) {
        printf("error: root required to 🔓 unlock/lock 🔒 Steam Deck (jupiter) BIOS (AMD CBS/PBS).\n");
        printf(" info: run (as root) on Steam Deck (jupiter) hardware to 🔓 unlock/lock 🔒 BIOS (AMD CBS/PBS).\n");
        printf("usage: [sudo] %s [-l] [--lock]\n", argv[0]);
        return 1;
    }

    ioperm(0x72, 2, 1);
    outb(0xF7, 0x72);
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-l") == 0 || strcmp(argv[i], "--lock") == 0) {
            outb(0x00, 0x73);
            printf("Steam Deck (jupiter) BIOS successfully 🔒 locked 🔒 (AMD CBS/PBS).\n");
            return 0;
        }
    }
    outb(0x77, 0x73);
    printf("Steam Deck (jupiter) BIOS successfully 🔓 unlocked 🔓 (AMD CBS/PBS).\n");
    return 0;
}
