#ifndef __SHARED_STRUCTS_H__
#define __SHARED_STRUCTS_H__

#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>

#include "tstest.h"
#include "shared_structs_threads.h"
#include "linux_ipc.h"


typedef struct
{
  uint8_t sem;
  uint8_t u8_TsTest_newest;
  uint8_t u8_TsTest_back2;
  uint8_t u8_TsTest_write;

  TsTest TsTest_Arr[3];
} TsRte;

TsTest* rte_TsTest_write(void);
void rte_TsTest_post(void);
TsTest* rte_TsTest_read(void);
void rte_init(void);

#endif
