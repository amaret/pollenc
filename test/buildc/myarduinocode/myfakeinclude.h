
/* 
 * OeScript http://www.oescript.net
 * Copyright 2012 Ed Sweeney, all rights reserved.
 */

#ifdef __cplusplus
extern "C" {
#endif 

#ifndef DATAOBJECTITERATOR_H
#define DATAOBJECTITERATOR_H

#include "arena.h"
#include <stdbool.h>
#define T ArrayIterator
struct array_iterator_T {
    int pos;
    void **darray;
};

typedef struct array_iterator_T *T;

extern T ArrayIterator_new(void **);

extern void *ArrayIterator_next(T);
extern bool ArrayIterator_hasMore(T);
extern void ArrayIterator_free(T*);

#undef T
#endif

#ifdef __cplusplus
}
#endif 

