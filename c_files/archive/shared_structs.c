#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "shared_structs.h"

#include "linux_ipc.h"
#include "main.h"



TsRte * rte_ptr;



TsTest* rte_TsTest_write(void)
{
  sem_get(&(rte_ptr->sem));
  //printf("indices new: %d  back2:  %d write:%d \n",rte_ptr->u8_TsTest_newest,rte_ptr->u8_TsTest_back2,rte_ptr->u8_TsTest_write);
  if ((0 != rte_ptr->u8_TsTest_newest) &&
      (0 != rte_ptr->u8_TsTest_back2))
  {
      rte_ptr->u8_TsTest_write = 0;
  }
  else if ((1 != rte_ptr->u8_TsTest_newest) &&
      (1 != rte_ptr->u8_TsTest_back2))
  {
      rte_ptr->u8_TsTest_write = 1;
  }
  else
  {
    rte_ptr->u8_TsTest_write = 2;
  }
  sem_release(&(rte_ptr->sem));
  memcpy(&(rte_ptr->TsTest_Arr[rte_ptr->u8_TsTest_write]), &(rte_ptr->TsTest_Arr[rte_ptr->u8_TsTest_newest]),sizeof(TsTest));
  return &(rte_ptr->TsTest_Arr[rte_ptr->u8_TsTest_write]);

}

void rte_TsTest_post(void)
{
  //todo atomic store
  sem_get(&(rte_ptr->sem));
  rte_ptr->u8_TsTest_newest = rte_ptr->u8_TsTest_write;
  sem_release(&(rte_ptr->sem));

}

TsTest* rte_TsTest_read(void)
{
  sem_get(&(rte_ptr->sem));
  //printf("indices new: %d  back2:  %d write:%d \n",rte_ptr->u8_TsTest_newest,rte_ptr->u8_TsTest_back2,rte_ptr->u8_TsTest_write);
  rte_ptr->u8_TsTest_back2 = rte_ptr->u8_TsTest_newest;
  sem_release(&(rte_ptr->sem));
  return &(rte_ptr->TsTest_Arr[rte_ptr->u8_TsTest_back2]);
}

void rte_init(void)
{
  TsTest * ptr = rte_TsTest_write();
  *ptr = (TsTest){0};
  rte_TsTest_post();
}
