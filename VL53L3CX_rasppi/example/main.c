/**
******************************************************************************
* File Name          : main.c
* Description        : Main program body
******************************************************************************
*
* COPYRIGHT(c) 2020 STMicroelectronics
*
* Redistribution and use in source and binary forms, with or without modification,
* are permitted provided that the following conditions are met:
*   1. Redistributions of source code must retain the above copyright notice,
*      this list of conditions and the following disclaimer.
*   2. Redistributions in binary form must reproduce the above copyright notice,
*      this list of conditions and the following disclaimer in the documentation
*      and/or other materials provided with the distribution.
*   3. Neither the name of STMicroelectronics nor the names of its contributors
*      may be used to endorse or promote products derived from this software
*      without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
* IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*
******************************************************************************
*/

/* Includes ------------------------------------------------------------------*/
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <signal.h>   /* SIGINT handler */

#define XSHUTPIN 4  // GPIO 4

/* USER CODE BEGIN Includes */
#include "vl53lx_api.h"
#include "vl53lx_platform.h"
/* USER CODE END Includes */

/* Private variables ---------------------------------------------------------*/
VL53LX_Dev_t                   dev;
VL53LX_DEV                     Dev = &dev;
int status;

/* Flag set by SIGINT (Ctrl+C) to break the ranging loop cleanly */
static volatile int keep_running = 1;

/* SIGINT handler — just sets the flag, does no I/O */
static void handle_sigint(int sig)
{
    (void)sig;
    keep_running = 0;
}

/* Private function prototypes -----------------------------------------------*/
void RangingLoop(void);

int main(void)
{
  /* Install signal handler before doing anything else */
  signal(SIGINT, handle_sigint);

#if 0  // not necessary if you don't connect XSHUT
  printf("Raising XSHUT pin %d to enable sensor...\n", XSHUTPIN);
  char buffer[64];
  sprintf(buffer, "/sys/class/gpio/gpio%d/direction", XSHUTPIN);
  int fd = open(buffer, O_RDWR);
  if (fd < 0) {
    int fd = open("/sys/class/gpio/export", O_RDWR);
    if (fd < 0) {
      printf ("Failed to init 1\n");
      return 1;
    }
    sprintf(buffer, "%d", XSHUTPIN);
    write(fd, buffer, strlen(buffer));
    close(fd);
    usleep(1000);
  }
  sprintf(buffer, "/sys/class/gpio/gpio%d/direction", XSHUTPIN);
  fd = open(buffer, O_RDWR);
  if (fd < 0) {
      printf ("Failed to init 2 due to %s\n", strerror(errno));
      return 1;
  }
  write(fd, "out", 3);
  close(fd);
  sprintf(buffer, "/sys/class/gpio/gpio%d/value", XSHUTPIN);
  fd = open(buffer, O_RDWR);
  if (fd < 0) {
      printf ("Failed to init 3\n");
      return 1;
  }
  write(fd, "1", 1);
  close(fd);
  usleep(250000);
#endif

  printf("VL53L1X Examples...\n");

  Dev->I2cDevAddr = 0x29;
  Dev->fd = VL53LX_i2c_init("/dev/i2c-1", Dev->I2cDevAddr);
  if (Dev->fd < 0) {
      printf("Failed to init I2C\n");
      return 1;
  }

  uint8_t byteData;
  uint16_t wordData;
  VL53LX_RdByte(Dev, 0x010F, &byteData);
  printf("VL53LX Model_ID: %02X\n\r", byteData);
  if (byteData != 0xea) {
    printf("WARNING: Model Id is not 0xea, which it ought to be!\n");
  }
  VL53LX_RdByte(Dev, 0x0110, &byteData);
  printf("VL53LX Module_Type: %02X\n\r", byteData);
  if (byteData != 0xaa) {
    printf("WARNING: Module type is not 0xaa, which it ought to be!\n");
  }
  VL53LX_RdWord(Dev, 0x010F, &wordData);
  printf("VL53LX: %02X\n\r", wordData);

  RangingLoop();

  return 0;
}

/* Ranging and display loop */
void RangingLoop(void)
{
  VL53LX_MultiRangingData_t MultiRangingData;
  VL53LX_MultiRangingData_t *pMultiRangingData = &MultiRangingData;
  uint8_t NewDataReady = 0;
  int no_of_object_found = 0, j;

  printf("Ranging loop starts\n");

  status = VL53LX_WaitDeviceBooted(Dev);
  status = VL53LX_DataInit(Dev);
  status = VL53LX_StartMeasurement(Dev);

  if (status) {
    printf("VL53LX_StartMeasurement failed: error = %d\n", status);
    return;
  }

  /* Main ranging loop — exits cleanly on Ctrl+C */
  while (keep_running) {
    status = VL53LX_GetMeasurementDataReady(Dev, &NewDataReady);
    usleep(250000); /* 250 ms polling period */

    if ((!status) && (NewDataReady != 0)) {
      status = VL53LX_GetMultiRangingData(Dev, pMultiRangingData);
      no_of_object_found = pMultiRangingData->NumberOfObjectsFound;

      printf("Count=%5d, ", pMultiRangingData->StreamCount);
      printf("#Objs=%1d ", no_of_object_found);

      for (j = 0; j < no_of_object_found; j++) {
        if (j != 0) printf("\n                     ");
        printf("status=%d, D=%5dmm, S=%7dmm, Signal=%2.2f Mcps, Ambient=%2.2f Mcps",
               pMultiRangingData->RangeData[j].RangeStatus,
               pMultiRangingData->RangeData[j].RangeMilliMeter,
               pMultiRangingData->RangeData[j].SigmaMilliMeter,
               pMultiRangingData->RangeData[j].SignalRateRtnMegaCps / 65536.0,
               pMultiRangingData->RangeData[j].AmbientRateRtnMegaCps / 65536.0);
      }
      printf("\n");

      if (status == 0) {
        status = VL53LX_ClearInterruptAndStartMeasurement(Dev);
      }
    }
  }

  /* Clean shutdown — stop the sensor before exit so the next run starts fresh */
  printf("\nStopping measurement...\n");
  status = VL53LX_StopMeasurement(Dev);
  if (status == 0) {
    printf("Sensor stopped cleanly. Safe to rerun.\n");
  } else {
    printf("StopMeasurement returned error %d\n", status);
  }
}

/**
* @brief  This function is executed in case of error occurrence.
*/
void Error_Handler(void)
{
  while (1) {}
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t* file, uint32_t line)
{
  /* unused */
}
#endif

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/