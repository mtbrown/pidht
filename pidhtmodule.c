#include <stdlib.h>
#include <stdint.h>
#include <Python.h>
#include "dht.h"


static PyObject *dht_read_wrapper(PyObject *self, PyObject *args) {
   int i;
   int pin;  // argument specifying pin to read
   uint32_t *pulse_lengths;
   PyObject *ret;

   // parse arguments
   if (!PyArg_ParseTuple(args, "i", &pin)) {
      return NULL;
   }

   // perform actual sensor read
   pulse_lengths = dht_read(pin);

   // build the resulting list into a Python object
   ret = PyList_New(NUM_PULSES);
   for (i = 0; i < NUM_PULSES; i++) {
      PyList_Append(ret, Py_BuildValue("i", pulse_lengths[i]));
   }
   free(pulse_lengths);

   return ret;
}


static PyMethodDef PidhtMethods[] = {
   {"dht_read", dht_read_wrapper, METH_VARARGS, 
      "Read the pulse lengths of a DHT temperature sensor"},
   {NULL, NULL, 0, NULL}
};


static struct PyModuleDef pidhtmodule = {
   PyModuleDef_HEAD_INIT,
   "pidht",  // module name
   NULL,  // module documentation
   -1,  // no module state
   PidhtMethods
};


PyMODINIT_FUNC PyInit_pidht(void) {
   return PyModule_Create(&pidhtmodule);
}
