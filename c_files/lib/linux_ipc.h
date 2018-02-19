#ifndef __LINUX_IPC__
#define __LINUX_IPC__

#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>


void* pvtmMmapAlloc (char * mmapFileName, size_t size, char create);
void sem_get(uint8_t* sem);
void sem_release(uint8_t* sem);

#endif
