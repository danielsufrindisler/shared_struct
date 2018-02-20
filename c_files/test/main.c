#include <stdio.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "linux_ipc.h"
#include "shs_shared_file.h"



extern shs_struct * p_shs_struct;

static shs_threads_processes Se_thread;
shs_threads_processes get_thread(void)
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

  if (argv[1][0] == '1')
  {
    Se_thread = foreground;
    mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(shs_struct), true);
    printf("creating %s %d",argv[0],argv[1][0]);
    assert (mem1 != NULL);

    p_shs_struct = mem1;
    sem_release(&(p_shs_struct->sem));
    while(1)
    {
      sleep_rand();
      TsTest* ptr = shs_TsTest_write();
      ptr->a ++;
      ptr->b =ptr->a;
      shs_TsTest_post();
    }
  }
  if (argv[1][0] == '2')
  {
    Se_thread = background;
    mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(shs_struct), false);
    if (mem1 == NULL)
    {
      printf ("need to create\n");
      mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(shs_struct), true);
      assert (mem1 != NULL);
    }
    uint32_t count=0;
    uint16_t old = 0;
    p_shs_struct = mem1;
    printf("rte ptr %p",p_shs_struct);
    fflush(stdout);
    while (1)
    {
      sleep_rand();
      TsTest* ptr = shs_TsTest_read();
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
  if (argv[1][0] == '3')
  {
    Se_thread = fore2;
    mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(shs_struct), false);
    if (mem1 == NULL)
    {
      printf ("need to create\n");
      mem1 = pvtmMmapAlloc ("/dev/shm/rte_1", sizeof(shs_struct), true);
      assert (mem1 != NULL);
    }
    uint32_t count=0;
    uint16_t old = 0;
    p_shs_struct = mem1;
    printf("rte ptr %p",p_shs_struct);
    fflush(stdout);
    while (1)
    {
      sleep_rand();
      TsTest* ptr = shs_TsTest_read();
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
