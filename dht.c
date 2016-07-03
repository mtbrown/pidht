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


uint32_t *dht_read(int pin) {
   int i, expected, count;
   uint32_t *pulse_times = calloc(NUM_PULSES, sizeof(uint32_t));
   uint32_t prev_time, cur_time;

   // Initialize GPIO pin
   wiringPiSetupGpio();
   pinMode(pin, OUTPUT);
   pullUpDnControl(pin, PUD_UP);

   // The following is timing critical
   set_high_priority();

   // Activate sensor
   digitalWrite(pin, 0);
   delay(1);  // hold bus low for 1ms
   pinMode(pin, INPUT);  // release bus

   // Monitor pin and record pulse lengths
   prev_time = micros();
   expected = 0;
   
   for (i = 0; i < INIT_PULSES + NUM_PULSES; i++) {
      count = 0;
      while (digitalRead(pin) == expected) {
         count += 1;
         if (count > TIMEOUT_COUNT) {
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

   return pulse_times;
}

int main(int argc, char **argv) {
   int i;
   uint32_t *pulse_times;

   pulse_times = dht_read(25);
   
   for (i = 0; i < NUM_PULSES; i++) {
      printf("%u\n", pulse_times[i]);
   }
   free(pulse_times);

   return 0;
}
