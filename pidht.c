#include <stdio.h>
#include <fcntl.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdint.h>
#include <inttypes.h>
#include <sys/mman.h>
#include <sched.h>

#include <wiringPi.h>

#define DATA_BITS 40
#define NUM_PULSES (2 * DATA_BITS)

#define TIMEOUT_COUNT 10000

static uint32_t get_time() {
   struct timeval tv;
   gettimeofday(&tv, NULL);
   return tv.tv_sec * (uint32_t) 1000000 + tv.tv_usec;
}


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


int dht_read(int pin) {
   int i, expected, count;
   int pulse_counts[NUM_PULSES] = {0};

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
   expected = 0;
   for (i = 0; i < NUM_PULSES; i++) {
      count = 0;
      while (digitalRead(pin) == expected) {
         count += 1;
         if (count > TIMEOUT_COUNT) {
            break;
         }
      }
      pulse_counts[i] = count;
      expected = !expected;
   }

   for (i = 0; i < NUM_PULSES; i++) {
      printf("%d\n", pulse_counts[i]);
   }

   return 0;
}


int main() {
   dht_read(25);
}
