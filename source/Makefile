OBJS    := utf8.o msgqueue.o
CURDIR  := $(ROOT_DIR)/source

all: $(OBJS)
$(OBJS) : %.o : %.c
	$(CC) -c $^ $(X_INCDIR) -o $@
