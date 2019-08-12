#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <pthread.h>

#include "LPRCClientSDK.h"
#include "common.h"
#include "utf8.h"

static int siMsgID = 0;
static bool isWaitRecogn = false;
static int iRetryRecogn = 0;
static char sCameraIp[20];
static int sCameraPort;
static char gImageUnicode[10];

void LPRC_DataEx2CallBackHandler(CLIENT_LPRC_PLATE_RESULTEX *recResult, LDWORD dwUser)
{
    char sendbuff[128] = {0};
    //与结构体CLIENT_LPRC_PLATE_RESULTEX中的对应元素大小一致
    char colorbuff[8] = {0};
    char platebuff[16] = {0};
    
    if (strcmp(recResult->chCLIENTIP, sCameraIp) == 0) {
        //printf("callback\n");
        //有车进入停车场
        if (recResult->pPlateImage.nLen > 0) {
            gb_to_utf8(recResult->chColor, colorbuff, 8);
            gb_to_utf8(recResult->chLicense, platebuff, 16);
            //sprintf(sendbuffer, "Color:%s,Plate:%s", recResult->chColor, recResult->chLicense);
            sprintf(sendbuff, "Color:%s,Plate:%s", colorbuff, platebuff);
            sendMsgQueue(siMsgID, CLIENT_TYPE, (char *)&sendbuff, sizeof(sendbuff));
            isWaitRecogn = false;
            iRetryRecogn = 0;
        } else {
            //printf("callback null\n");
        }
    } 
}

// 输出连接状态的回调函数
void ConnectStatus(char *chCLIENTIP, UINT Status, LDWORD dwUser)
{
    if(strcmp(chCLIENTIP, sCameraIp) == 0)
    {
        if(Status == 0)
        {
            printf("%s connect fail!\n", chCLIENTIP);
        } else {
            //printf("%s connect Normal!\n", chCLIENTIP);
        }
    }
}

//专门用于处理抬杆动作
static void pthread_doorlockctl_handler(void *arg)
{
    char recvbuff[128];
    char sendbuff[64];
    int ret;
    fd_set read_fds;
    //fd_set write_fds;
    struct timeval tv;
    int fd = *((int *)arg);

    while(1)
    {
        tv.tv_sec = 1;
        tv.tv_usec = 0;
        FD_ZERO(&read_fds);
        FD_SET(fd, &read_fds);
        //FD_SET(fd, &write_fds);
        memset(recvbuff, 0, sizeof(recvbuff));

        //ret = select(fd+1, &read_fds, &write_fds, NULL, NULL);
        ret = select(fd + 1, &read_fds, NULL, NULL, &tv);
        if (ret == 0) {
            //timeout
            if (isWaitRecogn == true) {
                printf("retry trigger\n");
                iRetryRecogn++;
                CLIENT_LPRC_SetTrigger(sCameraIp, sCameraPort);
                if (iRetryRecogn >= 3) {
                    iRetryRecogn = 0;
                    isWaitRecogn = false;
                    memset(sendbuff, 0, sizeof(sendbuff));
                    sprintf(sendbuff, "{\"id\":\"%s\",\"status\":\"%s\"}", gImageUnicode, "fail");
                    //strncpy(sendbuff, "Recogn Failed", strlen("Recogn Failed"));
                    send(fd, sendbuff, strlen(sendbuff), 0);
                }
            }
        } else if (ret == -1) {
            //failed
        } else {
            //success
            if (FD_ISSET(fd, &read_fds)) {
                FD_CLR(fd, &read_fds);
                //printf("socket readable\r\n");
                ret = recv(fd, recvbuff, sizeof(recvbuff), 0);
                if(ret < 0) {
                    continue;
                } else if (ret == 0) {
                    continue;
                }
                printf("C Thread Socket Recv Image Unicode:%s\r\n", recvbuff);
                memset(gImageUnicode, 0, sizeof(gImageUnicode));
                strncpy(gImageUnicode, recvbuff, strlen(recvbuff));
                //sleep(1);
                //CLIENT_LPRC_SetTrigger(sCameraIp, sCameraPort);
                isWaitRecogn = true;
                iRetryRecogn = 0;
            } 
        }
    }
}

/*
 *  传入参数列表
 *  参数1: 图片保存地址
 *  参数2: 本地socket端口号
 *  参数3: 相机IP
 *  参数4: 相机Port
 *  参数5: C程序内部的生成消息队列的文件
 */
int main(int argc, char **argv)
{
    int     ret;
    //char    chPath[128];
    pthread_t pthread_doorctl_id;

    int server_fd;
    struct sockaddr_in server_addr;
    char recvbuff[128];
    char sendbuff[128];
    int len;
    int port;
    char msg_keyfile_name[100];

    if (argc < 6) {
        printf("paramters num = %d\n", argc);
        printf("main.c parameters must be 5\n");
        printf("expamle: ./main saveimagedir   local_socket_port   camera_ip   camera_port   keyfile_path_name\n");
        return 1;
    }
#if 0
    if (strlen(argv[1]) > sizeof(chPath)) {
        printf("save img path buffer is too short\n");
        printf("you should modify main.c file chPath[] more bigger\n");
        return 1;
    }
#endif
    if (strlen(argv[5]) > sizeof(msg_keyfile_name)) {
        printf("save key file path buffer is too short\n");
        printf("you should modify main.c file msg_keyfile_name[] more bigger\n");
        return 1;
    }
#if 0
    memset(chPath, 0, sizeof(chPath));
    strncpy(chPath, argv[1], strlen(argv[1]));
    printf("save Image Path:%s\n", chPath);
#endif
    port = atoi(argv[2]);
    printf("locale socket port = %d\n", port);

    sCameraPort = atoi(argv[4]);
    memset(sCameraIp, 0, sizeof(sCameraIp));
    strncpy(sCameraIp, argv[3], strlen(argv[3]));
    printf("camera ip = %s, port = %d\n", sCameraIp, sCameraPort);

    memset(msg_keyfile_name, 0, sizeof(msg_keyfile_name));
    strncpy(msg_keyfile_name, argv[5], strlen(argv[5]));
    printf("msgqueue keyfile : %s\n", msg_keyfile_name);


    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    //server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    server_addr.sin_port = htons(port);

    server_fd = socket(PF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return -1;
    }

    siMsgID = createMsgQueue(msg_keyfile_name);
    if (siMsgID == -1) {
        printf("createMsgQueue failed\r\n");
        return -1;
    }

   // 注册获取识别结果数据的回调函数
    CLIENT_LPRC_RegDataEx2Event((CLIENT_LPRC_DataEx2Callback) LPRC_DataEx2CallBackHandler);
    // 注册链接状态的回调函数
    CLIENT_LPRC_RegCLIENTConnEvent ((CLIENT_LPRC_ConnectCallback) ConnectStatus);
    // 设置图片保存的路径（设置路径后，接口库会自动将识别结果保存到指定目录下）
    //CLIENT_LPRC_SetSavePath(chPath);
    //设置gpio回掉函数
    //CLIENT_LPRC_RegWTYGetGpioState((CLIENT_LPRC_GetGpioStateCallback) GPIOCallBackHandler);

    // 初始化。（多个相机的话，需要调用多次这个接口,输入不同的IP地址）
    ret = CLIENT_LPRC_InitSDK(sCameraPort, NULL, 0, sCameraIp, 1);
    if (ret == 1)
    {
#if 0
        printf("%s InitSDK fail\n\tthen quit\r\n", sCameraIp);
        CLIENT_LPRC_QuitSDK();
        return -1;
#endif
    } else {
        printf("%s InitSDK success\n", sCameraIp);
    }

    if (connect(server_fd, (struct sockaddr *)&server_addr, sizeof(struct sockaddr)) < 0) {
        //if (errno != EISCONN)
        //    continue;
        perror("connect");
        return -1;
    }

    if (pthread_create(&pthread_doorctl_id, NULL, (void *)(pthread_doorlockctl_handler), (void *)&server_fd) == -1) {
        perror("pthread_create");
        return -1;
    }

    while(1)
    {
        memset(recvbuff, 0, sizeof(recvbuff));
        memset(sendbuff, 0, sizeof(sendbuff));
        recvMsgQueue(siMsgID, CLIENT_TYPE, recvbuff);
        printf("C Socket Send:%s\r\n", recvbuff);
        sprintf(sendbuff, "{\"id\":\"%s\", \"status\":\"success\",\"result\":\"%s\"}", 
                gImageUnicode, recvbuff);

        len = send(server_fd, sendbuff, strlen(sendbuff), 0);
        if (len == strlen(recvbuff)) {
            printf("Send OK\r\n");
        }
        memset(gImageUnicode, 0, sizeof(gImageUnicode));
    }

    close(server_fd);
    // 释放资源
    CLIENT_LPRC_QuitSDK();
    destoryMsgQueue(siMsgID);

    return 0;
}
