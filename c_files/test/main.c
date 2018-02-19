#include <stdio.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "linux_ipc.h"
#include "shared_structs.h"


extern TsRte * rte_ptr;

static rte_threads_processes Se_thread;
rte_threads_processes get_thread(void)
{
  return Se_thread;
}


void sleep_rand (void)
{
   struct timespec tim;
   tim.tv_sec = 0;
   tim.tv_nsec = rand() % 1000;
   nanosleep(&tim , NULL);
}

int main (int argc, char *argv[])
{
  void * mem1;
  srand(time(NULL));   // should only be called once

  if (argc >= 2)
  {
    Se_thread = back1;
    mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(TsRte), true);
    printf("creating %s %d",argv[0],argv[1][0]);
    assert (mem1 != NULL);

    rte_ptr = mem1;
    sem_release(&(rte_ptr->sem));
    while(1)
    {
      sleep_rand();
      TsTest* ptr = rte_TsTest_write();
      ptr->a ++;
      ptr->b =ptr->a;
      rte_TsTest_post();
    }
  }
  else
  {
    Se_thread = back2;
    mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(TsRte), false);
    if (mem1 == NULL)
    {
      printf ("need to create\n");
      mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(TsRte), true);
      assert (mem1 != NULL);
    }
    uint32_t count=0;
    uint16_t old = 0;
    rte_ptr = mem1;
    printf("rte ptr %p",rte_ptr);
    fflush(stdout);
    while (1)
    {
      sleep_rand();
      TsTest* ptr = rte_TsTest_read();
      if (count % 100 == 0)
      {
        printf("reading %p  %d \n",ptr,ptr->a);
        fflush(stdout);
      }
      if (ptr->a != old)
      {
        old = ptr->a;
        count++;
      }
      assert(ptr->a == ptr->b);

    }
  }
}
