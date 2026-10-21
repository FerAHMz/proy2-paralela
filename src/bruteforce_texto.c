// Búsqueda de la llave por fuerza bruta con MPI sobre un archivo cifrado con cifrar.c.
// Uso: mpirun -np N ./bruteforce_texto <cifrado.bin> "<frase clave>"
// Misma estrategia que bruteforce.c: el rango [0, 2^56) se divide en N bloques
// contiguos y el que encuentra la llave avisa a los demás.
#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <unistd.h>
#include "des_util.h"

int main(int argc, char *argv[]){
  int N, id;
  long upper = (1L <<56); //upper bound DES keys 2^56
  long mylower, myupper;
  MPI_Status st;
  MPI_Request req;
  MPI_Comm comm = MPI_COMM_WORLD;

  MPI_Init(&argc, &argv);
  MPI_Comm_size(comm, &N);
  MPI_Comm_rank(comm, &id);

  if(argc != 3){
    if(id == 0) fprintf(stderr, "Uso: mpirun -np N %s <cifrado.bin> \"<frase clave>\"\n", argv[0]);
    MPI_Finalize();
    return 1;
  }
  char *search = argv[2];

  // todos los procesos leen el archivo cifrado
  FILE *f = fopen(argv[1], "rb");
  if(!f){ perror(argv[1]); MPI_Abort(comm, 1); }
  fseek(f, 0, SEEK_END);
  int ciphlen = ftell(f);
  rewind(f);
  char *cipher = malloc(ciphlen + 1);
  fread(cipher, 1, ciphlen, f);
  cipher[ciphlen] = 0;
  fclose(f);

  long found = 0;
  int ready = 0;

  long range_per_node = upper / N;
  mylower = range_per_node * id;
  myupper = range_per_node * (id+1); // límite exclusivo, sin omitir una llave
  if(id == N-1){
    myupper = upper;
  }

  MPI_Irecv(&found, 1, MPI_LONG, MPI_ANY_SOURCE, MPI_ANY_TAG, comm, &req);

  MPI_Barrier(comm);
  double t0 = MPI_Wtime();

  for(long i = mylower; i<myupper; ++i){
    MPI_Test(&req, &ready, MPI_STATUS_IGNORE);
    if(ready)
      break;

    if(tryKey(i, cipher, ciphlen, search)){
      long key = i;
      printf("Proceso %d encontró la llave (%ld llaves probadas)\n", id, i - mylower + 1);
      for(int node=0; node<N; node++){
        MPI_Send(&key, 1, MPI_LONG, node, 0, comm);
      }
      break;
    }
  }

  // Completar también las recepciones de los procesos distintos de cero.
  MPI_Wait(&req, &st);
  if(id==0){
    double t1 = MPI_Wtime();
    decrypt(found, cipher, ciphlen);
    printf("Llave = %ld\n", found);
    printf("Procesos = %d\n", N);
    printf("Tiempo = %.6f s\n\n", t1 - t0);
    printf("%s\n", cipher);
  }

  free(cipher);
  MPI_Finalize();
  return 0;
}
