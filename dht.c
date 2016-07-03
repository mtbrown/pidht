#include <stdio.h>
#include <sys/mman.h>
#include <sched.h>
#include <stdlib.h>
#include <stdint.h>
#include <wiringPi.h>

#include "dht.h"

#define TIMEOUT_COUNT 10000


static void set_high_priority() {
   struct sched_param param;
   param.sched_priority = sched_get_priority_max(SCHED_FIFO);

   if (sched_setscheduler(0, SCHED_FIFO, &param) < 0) {
      perror("sched_setscheduler");
   }
   if (mlockall(MCL_CURRENT | MCL_FUTURE) < 0) {
      perror("mlockall");
   }
}


int *dht_read(int pin) {
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

   // Ignore initialization pulses
   while (!digitalRead(pin)) ;
   while (digitalRead(pin)) ;
   while (!digitalRead(pin)) ;
   while (digitalRead(pin)) ;

   // Monitor pin and record pulse lengths
   prev_time = micros();
   expected = 0;
   
   for (i = 0; i < NUM_PULSES; i++) {
      count = 0;
      while (digitalRead(pin) == expected) {
         count += 1;
         if (count > TIMEOUT_COUNT) {
            break;
         }
      }
      cur_time = micros();
      pulse_times[i] = cur_time - prev_time;
      prev_time = cur_time;
      expected = !expected;
   }

   for (i = 0; i < NUM_PULSES; i++) {
      printf("%u\n", pulse_times[i]);
   }

   return pulse_times;
}

int main() {
   dht_read(25);
}
