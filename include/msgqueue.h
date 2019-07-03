#ifndef _MSGQUEUE_H_
#define _MSGQUEUE_H_

#include <stdint.h>

struct park_msgbuf {
    long mtype;
    char mtext[128];
};

#define SERVER_TYPE     0xa55a
#define CLIENT_TYPE     0x9a4f

#define MSG_KEYFILE    "/home/duan/park/msgkey.file"

int createMsgQueue(char *key);
int getMsgQueue(char *key);
int destoryMsgQueue(int msg_id);
int sendMsgQueue(int msg_id, int who, char *msg, int len);
int recvMsgQueue(int msg_id, int recvType,char *out);

#endif
