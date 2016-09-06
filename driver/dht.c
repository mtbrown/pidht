#include <stdio.h>
#include <sys/mman.h>
#include <sched.h>
#include <stdlib.h>
#include <stdint.h>
#include <wiringPi.h>

#include "dht.h"

#define INIT_PULSES 4
#define TIMEOUT_COUNT 10000


void set_high_priority(void) {
   struct sched_param param;
   param.sched_priority = sched_get_priority_max(SCHED_FIFO);

   if (sched_setscheduler(0, SCHED_FIFO, &param) < 0) {
      perror("sched_setscheduler");
   }
   if (mlockall(MCL_CURRENT | MCL_FUTURE) < 0) {
      perror("mlockall");
   }
}


void set_low_priority(void) {
   struct sched_param param;
   param.sched_priority = sched_get_priority_min(SCHED_FIFO);

   if (sched_setscheduler(0, SCHED_FIFO, &param) < 0) {
      perror("sched_setscheduler");
   }
   if (munlockall() < 0) {
      perror("munlockall");
   }
}


void dht_init(void) {
   wiringPiSetup();  // initialize wiringPi library
}


uint32_t *dht_read(int pin) {
   int i, expected, count;
   uint32_t *pulse_times = calloc(NUM_PULSES, sizeof(uint32_t));
   uint32_t prev_time, cur_time;

   prev_time = micros();
   expected = 0;

   // The following is timing critical
   set_high_priority();

   // Activate sensor
   pinMode(pin, OUTPUT);
   pullUpDnControl(pin, PUD_UP);
   digitalWrite(pin, 0);
   delay(1);  // hold bus low for 1ms
   pinMode(pin, INPUT);  // release bus

   // Monitor pin and record pulse lengths sent by sensor
   for (i = 0; i < INIT_PULSES + NUM_PULSES; i++) {
      count = 0;
      while (digitalRead(pin) == expected) {
         count += 1;
         if (count >= TIMEOUT_COUNT) {
            break;
         }
      }
      cur_time = micros();
      if (i >= INIT_PULSES) {
         pulse_times[i - INIT_PULSES] = cur_time - prev_time;
      }

      prev_time = cur_time;
      expected = !expected;
   }

   // End of timing critical section
   set_low_priority();

   return pulse_times;
}
