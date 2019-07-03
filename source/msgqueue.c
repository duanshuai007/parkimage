#include "msgqueue.h"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/msg.h>

static int commMsgQueue(char *keyfile, int flags)
{
    //char strkey[64] = {0};
    key_t key;

    //sprintf( strkey, "%s%s", MSGKEYDIR, MSGKEYFILE);
    //key = ftok( strkey, 0x6666);
    key = ftok( keyfile, 0x6666);
    if (key < 0) {
        perror("ftok");
        return -1; 
    }

    int msg_id = msgget( key, flags);
    if ( msg_id < 0) {
        perror("msgget");
        return -1;
    }   

    return msg_id;
}

int createMsgQueue(char *keyfile)
{
    return commMsgQueue(keyfile, IPC_CREAT /*| IPC_EXCL*/ | 0666);
}

int getMsgQueue(char *keyfile)
{
    return commMsgQueue(keyfile, IPC_CREAT);
}

int destoryMsgQueue(int msg_id)
{
    if (msgctl(msg_id, IPC_RMID, NULL) < 0) {
        perror("msgctl");
        return -1;
    }

    return 0;
}

int sendMsgQueue(int msg_id, int who, char *msg, int len)
{
    struct park_msgbuf buf;
    buf.mtype = who;
    //strcpy(buf.mtext, msg);
    memcpy(buf.mtext, msg, len);

    if (msgsnd(msg_id, (void *)&buf, sizeof(buf.mtext), 0) < 0) {
        perror("msgsnd");
        return -1;
    }

    return 0;
}

int recvMsgQueue(int msg_id, int recvType,char *out)
{
    struct park_msgbuf buf;
    int size = sizeof(buf.mtext);

    if (msgrcv(msg_id, (void *)&buf, size, recvType, 0) < 0) {
        perror("msgrcv");
        return -1;
    }

    //strncpy(out, buf.mtext, size);
    //out[size] = 0;
    memcpy(out, buf.mtext, size);

    return 0;
}

