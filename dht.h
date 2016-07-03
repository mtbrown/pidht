#ifndef DHT_H
#define DHT_H

#define DATA_BITS 40
#define NUM_PULSES (2 * DATA_BITS)

uint32_t *dht_read(int pin);

#endif /* DHT_H */
