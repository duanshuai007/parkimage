CC=gcc
RM=rm

ROOT_DIR :=  $(shell pwd)

C_FLAGS	:= -g -Wall
INCDIRS	:= include
LIB		:= lib/libwty.a
LD_FLAG	:= -lpthread
OBJS	:= source/utf8.o source/msgqueue.o

NO_MAKE_DIR := include Picture lib handler __pycache__ packet image_rsync
NO_MAKE     := $(patsubst %, grep -v % |, $(NO_MAKE_DIR))
SUBDIRS     = $(shell ls -l | grep ^d | awk '{print $$9}' | $(NO_MAKE) tr "\n" " ")
X_INCDIR    := $(patsubst %, -I $(ROOT_DIR)/%, $(INCDIRS))

export CC ROOT_DIR X_INCDIR

.PHONY: subdirs $(SUBDIRS)
.PHONY: clean

all:$(SUBDIRS)
	$(CC) $(C_FLAGS) $(X_INCDIR) main.c -o park_imagerecogn_c $(OBJS) $(LIB) $(LD_FLAG)

subdirs:$(SUBDIRS)
$(SUBDIRS):
	@make -s -C $@
