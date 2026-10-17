# En Linux: <rpc/des_crypt.h> viene en glibc (o en libtirpc en distros recientes).
# En macOS no existe, así que se usa compat/ implementado con OpenSSL.
UNAME := $(shell uname)
CC = mpicc
CFLAGS = -O2

ifeq ($(UNAME),Darwin)
OPENSSL ?= $(shell brew --prefix openssl@3)
COMPAT_CFLAGS = -Icompat -I$(OPENSSL)/include
COMPAT_SRC = compat/des_compat.c
COMPAT_LIBS = -L$(OPENSSL)/lib -lcrypto
endif

all: bruteforce

bruteforce: bruteforce.c $(COMPAT_SRC)
	$(CC) $(CFLAGS) -w $(COMPAT_CFLAGS) $^ -o $@ $(COMPAT_LIBS)


clean:
	rm -f bruteforce

.PHONY: all clean
