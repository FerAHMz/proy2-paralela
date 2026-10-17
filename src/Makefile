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

all: bruteforce bruteforce_texto cifrar

# programa original del catedrático, sin modificar (-w porque tiene warnings)
bruteforce: bruteforce.c $(COMPAT_SRC)
	$(CC) $(CFLAGS) -w $(COMPAT_CFLAGS) $^ -o $@ $(COMPAT_LIBS)

bruteforce_texto: bruteforce_texto.c des_util.h $(COMPAT_SRC)
	$(CC) $(CFLAGS) $(COMPAT_CFLAGS) bruteforce_texto.c $(COMPAT_SRC) -o $@ $(COMPAT_LIBS)

cifrar: cifrar.c des_util.h $(COMPAT_SRC)
	$(CC) $(CFLAGS) $(COMPAT_CFLAGS) cifrar.c $(COMPAT_SRC) -o $@ $(COMPAT_LIBS)

clean:
	rm -f bruteforce bruteforce_texto cifrar

.PHONY: all clean
